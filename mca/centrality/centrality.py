"""Meta class that allows computation of centrality indicators on georeferenced networks
"""

from mca.model.meta import address
from mca.model.model import Spatial_ref
from mca.utils.parameters import *
import shapefile
from shapely.wkb import loads
import traceback

# --- wxPython threadsafe  ---
import threading
import wx
from wx.lib.pubsub import Publisher

# --- overridden networkx ---
from overridden_nx_betweenness import betweenness_centrality as overridden_nx_betweenness_centrality
from overridden_nx_betweenness import edge_betweenness_centrality as overridden_nx_edge_betweenness_centrality
from overridden_nx_closeness import closeness_centrality as overridden_nx_closeness_centrality
from overridden_nx_straightness import straightness_centrality as overridden_nx_straightness_centrality

# --- sqlAlchemy dependencies ---
from sqlalchemy import Column, create_engine
from sqlalchemy.types import Integer
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy import Geometry, WKBSpatialElement, GeometryColumn

class Centrality(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

    # stop the process if error arises
    def stop(self):
        self._stop.set()

    def buildQuery(self):
        # Recreate the model for each instance of Centrality to map DB tables with the right schema
        # @see: Issue #28
        try:
            engine = create_engine(address, encoding='utf8')
            self.session = scoped_session(sessionmaker())
            Base = declarative_base(bind=engine)

            class Topology_data(Base):
                __tablename__ = 'topology'
                __table_args__ = ({'schema': 'topology', 'autoload': True})
                id = Column('id', Integer, primary_key=True)

            class Edge_data(Base):
                __tablename__ = 'edge_data'
                __table_args__ = ({'schema': get_param_selectedProjectName(), 'autoload': True, 'extend_existing': True})
                edge_id = Column('edge_id', Integer, primary_key=True)
                geom = GeometryColumn(Geometry)

            class Node(Base):
                __tablename__ = 'node'
                __table_args__ = ({'schema': get_param_selectedProjectName(), 'autoload': True, 'extend_existing': True})
                node_id = Column('node_id', Integer, primary_key=True)
                geom = GeometryColumn(Geometry)

            self.topology_data = Topology_data
            self.edge_data = Edge_data
            self.node_data = Node

            self.query = self.session.query(self.edge_data.edge_id, self.edge_data.start_node, self.edge_data.end_node, self.edge_data.geom.length.label('length'))
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the loading of the data model.")
            self.stop()

    def getEpsg(self):
        topo = self.session.query(self.topology_data.srid)
        topo = topo.filter(self.topology_data.name == get_param_selectedProjectName()).subquery('topo')
        query = self.session.query(Spatial_ref.srtext).filter(Spatial_ref.srid == topo.c.srid)
        for q in query:
            return q.srtext

    def createPrj(self):
        prj = open("%s.prj" % self.path_2_shp.strip('shp').strip('.'), "w")
        epsg = self.getEpsg()
        prj.write(epsg)
        prj.close()

    def consoleAppend(self, txt):
        wx.CallAfter(Publisher().sendMessage, "consoleAppend", txt)

    def consolePrintCreatedFiles(self):
        msg = 'The following files have been created in %s:\n' % self.path
        msg += '   - %s\n   - %s\n   - %s\n   - %s\n   - %s' % tuple([self.file_name + elem for elem in (fn_extensions + ['.log'])])
        self.consoleAppend(msg)

    def betweenness_centrality(self):
        weight = 'weight' if self.weighted else None
        self.c_values = overridden_nx_betweenness_centrality(self.G, k=self.k, normalized=self.normalized, weight=weight)

    def edge_betweenness_centrality(self):
        weight = 'weight' if self.weighted else None
        self.c_values = overridden_nx_edge_betweenness_centrality(self.G, k=self.k, normalized=self.normalized, weight=weight)

    def closeness_centrality(self, v=None, local=False, lengthG=None):
        weight = 'weight' if self.weighted else None
        self.c_values = overridden_nx_closeness_centrality(self.G, v=v, normalized=self.normalized, distance=weight, local=local, lengthG=lengthG)

    def straightness_centrality(self):
        self.c_values = overridden_nx_straightness_centrality(self.G, self.node_data, self.session, normalized=self.normalized, distance=True)


class NodeCentrality(Centrality):

    def createGraph(self):
        self.consoleAppend('Start creating the graph')
        for edge in self.query:
            if self.weighted:
                self.G.add_edge(edge.start_node, edge.end_node, weight=edge.length)
            else:
                self.G.add_edge(edge.start_node, edge.end_node)
        self.consoleAppend('Graph created')

    def createShp(self):
        self.consoleAppend('Start creating the shapfile')
        query = self.session.query(self.node_data.node_id, self.node_data.geom.wkb.label('wkb'))

        # Creation of the fields
        w = shapefile.Writer(shapefile.POINT)
        w.autoBalance = 1 #ensures gemoetry and attributes match
        w.field(self.column_name, 'F', 50, 20)

        for node in query:
            coordinates = list(loads(str(node.wkb)).coords)
            w.point(*coordinates[0])
            w.record(self.c_values[node.node_id])
 
        w.save(self.path_2_shp)

        # create the projection file
        self.createPrj()

        self.consoleAppend('Shapefile creation completed')


class NodeMeanCentrality(NodeCentrality):

    # Approximated values for edges based on node values
    # Overrides method declared in class NodeCentrality
    def createShp(self):
        self.consoleAppend('Start creating the shapfile')
        query = self.session.query(self.edge_data.edge_id, self.edge_data.start_node, self.edge_data.end_node, self.edge_data.geom.wkb.label('wkb'))

        # Creation of the fields
        w = shapefile.Writer(shapefile.POLYLINE)
        w.autoBalance = 1 #ensures gemoetry and attributes match
        w.field(self.column_name, 'F', 50, 20)

        for edge in query:
            coordinates = list(loads(str(edge.wkb)).coords)
            w.line(parts=[coordinates])
            # Take the average value of both nodes 
            mca_val = (self.c_values[edge.start_node] + self.c_values[edge.end_node]) / 2
            w.record(mca_val)

        w.save(self.path_2_shp)

        # create the projection file
        self.createPrj()

        self.consoleAppend('Shapefile creation completed')
