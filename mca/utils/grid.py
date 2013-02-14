import shapefile
from shapely.geometry import Point

class Grid(object):

    def __init__(self, xmin, ymin, xmax, ymax, resolution, srs, path=None):
        # in order to create a shapefile rather than a new project in mca destkop change default values above
        # path = /home/loic/data/grid.shp for instance
        # Initialize parameters 
        self.xmin = float(xmin)
        self.ymin = float(ymin)
        self.xmax = float(xmax)
        self.ymax = float(ymax)
        self.resolution = float(resolution)
        self.srs = srs
        self.rows = self.getRows()
        self.columns = self.getColumns()
        self.path = path

        self.createGrid()

    def createGrid(self):
        self.coordinates = list()
        width = self.xmin + (self.resolution*self.rows)
        height = self.ymin + (self.resolution*self.columns)
        xmin = self.xmin
        ymin = self.ymin
        i = 1

        while xmin <= width:
            j = 1
            ymin = self.ymin
            while ymin <= height:
                if self.path:
                    self.coordinates.append(Point(xmin, ymin))
                else:
                    self.coordinates.append(Point(xmin, ymin).to_wkt())
                j += 1
                ymin += self.resolution
            i += 1
            xmin += self.resolution

        if self.path:
            self.createShp()

    def getRows(self):
        return round((self.xmax - self.xmin) / self.resolution, 0)

    def getColumns(self):
        return round((self.ymax - self.ymin) / self.resolution, 0)

    def createShp(self):
        w = shapefile.Writer(shapefile.POINT)
        w.field('id', 'F', 50, 20)
        i = 1
        for point in self.coordinates:
            coordinates = list(point.coords)
            w.point(*coordinates[0])
            w.record(i)
            i += 1 
        w.save(self.path)
