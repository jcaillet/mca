"""Betweenness Centrality on geographical networks
"""

import os
from mca.centrality.centrality import Centrality, NodeCentrality, NodeMeanCentrality
from mca.utils.parameters import *
import traceback

from sqlalchemy import func
import shapefile
from shapely.wkb import loads

import networkx as nx

# --- wxPython threadsafe  ---
from threading import Thread
import wx
from wx.lib.pubsub import Publisher


class NodeBetweenness(NodeCentrality):

    def __init__(self, path, fileName, callback, k=None, weighted=True, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class
        self.callback = callback
        self.k = k
        self.weighted = weighted
        self.normalized = normalized
        self.column_name = 'betweenness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.G = nx.MultiGraph()
        self.buildQuery()
        self.start()

    def run(self):
        try:
            self.createGraph()
            self.computeBC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of node betweenness")
            self.stop()

    def computeBC(self):
        self.consoleAppend('Start computing betweenness centrality on nodes')
        self.betweenness_centrality()
        self.consoleAppend('Betweenness computation done')
        del self.G


class EdgeMeanBetweenness(NodeMeanCentrality):

    def __init__(self, path, fileName, callback, k=None, weighted=True, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.k = k
        self.weighted = weighted
        self.normalized = normalized
        self.column_name = 'betweenness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.G = nx.MultiGraph()
        self.buildQuery()
        self.start()

    def run(self):
        try:
            self.createGraph()
            self.computeBC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of edge mean betweenness")
            self.stop()

    def computeBC(self):
        self.consoleAppend('Start computing betweenness centrality')
        self.betweenness_centrality()
        self.consoleAppend('Betweenness computation done')
        del self.G


class EdgeBetweenness(Centrality):

    def __init__(self, path, fileName, callback, k=None, weighted=True, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.k = k
        self.weighted = weighted
        self.normalized = normalized
        self.column_name = 'betweenness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.G = nx.Graph()
        self.buildQuery()
        self.start()

    def run(self):
        try:
            self.createGraph()
            self.computeBC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of edge betweenness")
            self.stop()


    def createGraph(self):
        # Get the highest node id
        query = self.session.query(func.max(self.edge_data.start_node), func.max(self.edge_data.end_node))
        for q in query:
            counter = max(q) + 1

        self.consoleAppend('Start creating the graph')
        self.virtual_edges = dict()
        for edge in self.query:
            key1 = edge.start_node, edge.end_node
            key2 = edge.end_node, edge.start_node
            # Edge has not been added to the graph yet has not been added
            if self.G.get_edge_data(*key1) is None or self.G.get_edge_data(*key2) is None:
                if self.weighted:
                    self.G.add_edge(edge.start_node, edge.end_node, weight=edge.length)
                else:
                    self.G.add_edge(edge.start_node, edge.end_node)
            else:
                # Add a vitual node
                if self.weighted:
                    self.G.add_edge(edge.start_node, counter, weight=edge.length/2)
                    self.G.add_edge(counter, edge.end_node, weight=edge.length/2)
                else:
                    self.G.add_edge(edge.start_node, counter)
                    self.G.add_edge(counter, edge.end_node)

                vedge = edge.start_node, counter
                # vedge1 bc value is equal to vegde2 bc value by definition -> only one edge vedge
                self.virtual_edges[key1] = vedge
                self.virtual_edges[key2] = vedge
                counter = counter + 1
        self.consoleAppend('Graph created')

    def computeBC(self):
        self.consoleAppend('Start computing betweenness centrality on egdes')
        self.edge_betweenness_centrality()
        self.consoleAppend('Betweenness computation done')
        # One doesn't need the graph anymore
        del self.G

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

            # Create key tuple with start_node and end_node values
            key1 = edge.start_node, edge.end_node
            key2 = edge.end_node, edge.start_node

            # Check if edge has been split in 2 virtual edges
            if key1 in self.virtual_edges:
                vkey = self.virtual_edges[key1]
                w.record(self.c_values[vkey])
            elif key2 in self.virtual_edges:
                vkey = self.virtual_edges[key2]
                w.record(self.c_values[vkey])
            else:
                if key1 in self.c_values:
                    w.record(self.c_values[key1])
                elif key2 in self.c_values:
                    w.record(self.c_values[key2])

        w.save(self.path_2_shp)

        # create the projection file
        self.createPrj()

        self.consoleAppend('Shapefile creation completed')
