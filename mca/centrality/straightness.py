"""Straightness Centrality on geographical networks
"""

import os
from mca.centrality.centrality import Centrality, NodeCentrality, NodeMeanCentrality
from mca.utils.parameters import *
import traceback

import shapefile
from shapely.wkb import loads
import networkx as nx

# --- wxPython threadsafe  ---
from threading import Thread
import wx
from wx.lib.pubsub import Publisher


class NodeStraightness(NodeCentrality):

    def __init__(self, path, fileName, callback, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.weighted = True
        self.normalized = normalized
        self.column_name = 'straightness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.G = nx.MultiGraph()
        self.buildQuery()

        self.start() # start the thread

    def run(self):
        try:
            self.createGraph()
            self.computeSC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the loading of the computation of edge straightness.")
            self.stop() 

    def computeSC(self):
        self.consoleAppend('Start computing straightness centrality on nodes')
        self.straightness_centrality()
        self.consoleAppend('Straightness centrality values on nodes have been computed')
        # One doesn't need the graph anymore
        del self.G


class EdgeStraightness(NodeMeanCentrality):

    def __init__(self, path, fileName, callback, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.normalized = normalized
        self.column_name = 'straightness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.weighted = True
        self.G = nx.Graph()
        self.buildQuery()

        self.start() # start the thread

    def run(self):
        try:
            self.createGraph()
            self.computeSC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the loading of the computation of node straightness.")
            self.stop()

    def computeSC(self):
        self.consoleAppend('Start computing straightness centrality on egdes')
        self.straightness_centrality()
        self.consoleAppend('Straightness centrality values on edges have been computed')
        # One doesn't need the graph anymore
        del self.G
