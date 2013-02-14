#topology.py

from mca.utils.db_utils import *
from mca.model.meta import *
import sys
import time
import re
import traceback

# --- wxPython threadsafe  ---
import threading
import wx
from wx.lib.pubsub import Publisher


class Topology(threading.Thread):

    def __init__(self, name, projection, author, tolerance, kind, resolution, callback):
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

        self.callback = callback
        self.name = name
        self.projection = projection
        self.author = author
        self.tolerance = tolerance
        self.kind = kind
        self.resolution = resolution

        self.start() # start the thread

    def stop(self):
        self._stop.set()

    def run(self):
        self.create()

        if not self._stop.isSet():
            self.addGeometries()

        if not self._stop.isSet():
            wx.CallAfter(Publisher().sendMessage, self.callback, None)

    def create(self):
        connection = engine.connect()
        trans = connection.begin()
        try:
            toposql = "SELECT topology.CreateTopology('%s', %s, %s)" %(self.name, self.projection, self.tolerance)
            id = connection.execute(toposql).scalar()
            connection.execute("INSERT INTO topology.meta values ('%s', '%s', now(), %s, '%s', %s)" %(id, self.author, self.tolerance, self.kind, self.resolution))
            trans.commit()
        except:
            trans.rollback()
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the topology creation")
            self.stop()
        finally:
            connection.close()

    def addGeometries(self):
        connection = engine.connect()
        trans = connection.begin()
        try:
            geosql = "SELECT topology.ST_CreateTopoGeo('%s',ST_Collect(st_force_2d(%s))) from %s" %(self.name, geometryColumn, self.name)
            connection.execute(geosql)
            trans.commit()
        except:
            trans.rollback()
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during add geometries")
            self.stop()
        finally:
            connection.close()



class CleanNodesDegree2(threading.Thread):

    def __init__(self, name, callback):
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

        self.callback = callback
        self.name = name

        self.start() # start the thread

    def stop(self):
        self._stop.set()

    def run(self):
        self.edge2 = list(self.getEdgesDegree2())
        if len(self.edge2) == 0: print 'No nodes degree 2'
        self.healEdges()

        if not self._stop.isSet():
            wx.CallAfter(Publisher().sendMessage, self.callback, "")

    def getEdgesDegree2(self): # ByPostgis
        nodes = engine.execute("SELECT node_id from %s.node" %self.name)
        for n in nodes:
            nid = n.items()[0][1]
            edges = list(engine.execute("SELECT topology.GetNodeEdges('%s', %d)" %(self.name, nid)))
            degree = len(edges)
            if degree == 2:
                yield (re.search(r'\(\d,-?(\d+)\)', edges[0][0]).group(1), re.search(r'\(\d,-?(\d+)\)', edges[1][0]).group(1))

    def healEdges(self):
        rmEdges = {}
        connection = engine.connect()
        try:
            for ed0, ed1 in self.edge2:
                while ed0 in rmEdges:
                    ed0 = rmEdges[ed0]
                while ed1 in rmEdges:
                    ed1 = rmEdges[ed1]
                if ed0 != ed1: # in case of a loop
                    trans = connection.begin()
                    sql = "SELECT topology.ST_NewEdgeHeal('%s', %s, %s)" %(self.name, ed0, ed1)
                    newEdgeId = connection.execute(sql).scalar()
                    trans.commit()
                    rmEdges[ed0] = newEdgeId
                    rmEdges[ed1] = newEdgeId
        except:
            print rmEdges
            trans.rollback()
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the clean nodes of degree 2")
            self.stop()
        finally:
            connection.close()
