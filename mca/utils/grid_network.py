from mca.utils.ogr2ogr import *
from mca.utils.grid import *
from mca.model.meta import Session, engine
from mca.centrality.overridden_nx_straightness import euclidean_distance

import shapefile
from shapely.wkt import dumps, loads
from shapely.geometry import Point, LineString

# --- wxPython threadsafe  ---
import threading
import wx
from wx.lib.pubsub import Publisher

class GridNetwork(threading.Thread):

    def __init__(self, callback, pubDial, resolution, srs, projectName, obstacle_within=False, path=None):
        # in order to create a shapefile rather than a new project in mca destkop change default values above
        # path = /home/loic/data/grid_network.shp for instance
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

        self.callback = callback
        self.pubDial = pubDial
        self.srs = srs
        self.resolution = resolution
        self.obstacle_within = obstacle_within
        self.points_within_obstacles = list()
        self.obstacles = list()
        self.projectName = projectName
        self.path = path

        self.start()

    def run(self):
        if not self._stop.isSet():
            self.getExtent()
        if not self._stop.isSet():
            self.grid = Grid(self.xmin, self.ymin, self.xmax, self.ymax, self.resolution, self.srs)
        if not self._stop.isSet():
            self.intersect()
        if not self._stop.isSet():
            if self.obstacle_within:
                self.getObstacles()
        if not self._stop.isSet():
            self.createNetworkGrid()

        if not self._stop.isSet():
            # if no line where created, it is probably a projection issue
            if len(self.list_lines) == 0:
                txt = 'Grid creation stopped, resolution higher than the polygon extent.\n'
                wx.CallAfter(Publisher().sendMessage, "consoleAppend", txt)
                txt += 'Please chek that the provided resolution matches the unit of the project SRS.\n'
                txt += 'Problems often arise when the project SRS unit is in degree.'
                wx.CallAfter(Publisher().sendMessage, self.pubDial, txt)
            else:
                if self.path: # create a shapefile
                    self.createShp()
                else:
                    self.shp2db(self.srs)

    def stop(self):
        self._stop.set()

    def getExtent(self):
        conn = engine.connect()
        try:
            # polygon and obstacles are hard coded because they are always the same
            sql = 'SELECT ST_xmin(geom), ST_ymin(geom), ST_xmax(geom), ST_ymax(geom) FROM public.polygon'
            bbox = conn.execute(sql)
            for b in bbox:
                self.xmin, self.ymin, self.xmax, self.ymax = b[0], b[1], b[2], b[3]
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the extent extraction")
            self.stop()
        finally:
            conn.close()

    def intersect(self):
        wx.CallAfter(Publisher().sendMessage, "consoleAppend", 'Start intersecting the grid with the polygon...')
        try:
            sql = "SELECT ST_ASText(grid.points), ST_X(grid.points) as x, ST_Y(grid.points) as y FROM (SELECT unnest(array["
            last = len(self.grid.coordinates)
            i = 1
            for coord in self.grid.coordinates:
                sql += "ST_GeomFromText('%s', %s), " % (coord, self.srs)
                if i == last:
                    sql = sql + "ST_GeomFromText('%s', %s)]) AS points) AS grid, public.polygon " % (coord, self.srs)
                i += 1
            sql += "WHERE ST_Intersects(polygon.geom, grid.points) "
            sql += "ORDER BY x,y"
            self.sql_grid_coords = sql
    
            # If obstacle are defined -> remove points intersecting the obstacles
            if self.obstacle_within:
                wx.CallAfter(Publisher().sendMessage, "consoleAppend", 'Start intersecting the grid with the obstacles...')
                sql = "SELECT ST_ASText(grid.points)  FROM (SELECT unnest(array["
                i = 1
                for coord in self.grid.coordinates:
                    sql += "ST_GeomFromText('%s', %s), " % (coord, self.srs)
                    if i == last:
                        sql = sql + "ST_GeomFromText('%s', %s)]) AS points) AS grid, public.obstacles " % (coord, self.srs)
                    i += 1
                sql += "WHERE ST_Intersects(obstacles.geom, grid.points) "

                conn = engine.connect()
                pts_obstacles_coords = conn.execute(sql)
                for point in pts_obstacles_coords:
                    self.points_within_obstacles.append(loads(point[0]).to_wkt())
                wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Intersection of points with polygon(s) and obstacle(s) done...")
            else:
                wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Intersection of points with polygon(s) done...")
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the intersection of the grid points with the polygon and/or obstacles")
            self.stop()
        finally:
            if self.obstacle_within: conn.close()


    def getObstacles(self):
        conn = engine.connect()
        try:
            sql = "SELECT ST_AsText(obstacles.geom) FROM public.obstacles"
            obstacles = conn.execute(sql)
            for ob in obstacles:
                self.obstacles.append(loads(ob[0]))
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during retrieving the obstacles from the DB")
            self.stop()
        finally:
            conn.close() 

    def intersectsObstacles(self, line):
        for ob in self.obstacles:
            if ob.intersects(line):
                return True
        return False

    def createNetworkGrid(self):
        conn = engine.connect()
        try:
            grid_coords = conn.execute(self.sql_grid_coords)
            x = -1
            y = -1
            list_x = list()
            self.list_lines = list()
            for point in grid_coords:
                p = loads(point[0])
                if p.to_wkt() not in self.points_within_obstacles:
                    if p.x != x:
                        # initialiaze new column
                        x = p.x
                        y = p.y
                        left_point = Point(x - self.resolution, y).to_wkt()
                        list_x.append(p.to_wkt())
                        # add horizontal line at the left
                        if left_point in list_x and left_point not in self.points_within_obstacles:
                            line = LineString([(x - self.resolution, y), (x, y)])
                            # if the line created does not intersects the obstacle
                            # can happen often for a low resolution or if obstacles are lines
                            if not self.intersectsObstacles(line):
                                self.list_lines.append(line)
                    elif p.x == x:
                        dist = euclidean_distance(x, y, p.x, p.y)
                        left_point = Point(x - self.resolution, p.y).to_wkt()
                        # add vertical line at the bottom
                        if dist == self.resolution:
                            line = LineString([(x, y), (x, p.y)])
                            if not self.intersectsObstacles(line):
                                self.list_lines.append(line)
                        # add horizontal line at the left
                        if left_point in list_x and left_point not in self.points_within_obstacles:
                            line = LineString([(x - self.resolution, p.y), (x, p.y)])
                            if not self.intersectsObstacles(line):
                                self.list_lines.append(line)
                        list_x.append(p.to_wkt())
                        y = p.y
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", 'The grid network has been created')
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the grid creation")
            self.stop()
        finally:
            del self.sql_grid_coords
            conn.close()

    def shp2db(self, srs):
        conn = engine.connect()
        try:
            # Function use the create the topology in the BD
            trans = conn.begin()
            sql = 'CREATE TABLE public.%s (gid integer, geom geometry(LineString, %s), CONSTRAINT %s_pkey PRIMARY KEY (gid)) ' % (self.projectName, srs, self.projectName)
            sql += 'WITH (OIDS=FALSE); ALTER TABLE public.%s OWNER TO postgres;' % self.projectName
            conn.execute(sql)
    
            i = 1
            last = len(self.list_lines)
            sql = 'INSERT INTO public.%s VALUES ' % self.projectName
            for line in self.list_lines:
                if i == last:
                    sql += "(%s, ST_SetSRID(ST_GeometryFromText('%s'), %s))" % (i, line, srs)
                else:
                    sql += "(%s, ST_SetSRID(ST_GeometryFromText('%s'), %s)), " % (i, line, srs)
                i += 1
            conn.execute(sql)
            trans.commit()
            wx.CallAfter(Publisher().sendMessage, self.callback, None)
        except:
            print traceback.print_exc()
            trans.rollback()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the grid loading to the DB")
            self.stop()
        finally:
            conn.close()

    def createShp(self):
        try:
            # This method is not directly use in the application, but can be used to create shapefile by expert user
            w = shapefile.Writer(shapefile.POLYLINE)
            w.field('id', 'F', 50, 20)
            i = 1
            for line in self.list_lines:
                coordinates = list(line.coords)
                w.line(parts=[coordinates])
                w.record(i)
                i += 1
            w.save(self.path)
            wx.CallAfter(Publisher().sendMessage, "gridShpNetworkEnd", None)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the shapefile creation")
            self.stop()

