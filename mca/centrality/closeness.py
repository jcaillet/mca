"""Closeness Centrality on geographical networks
"""

import os
import time
from mca.utils.utils import GetTextTime
from mca.centrality.centrality import Centrality, NodeCentrality, NodeMeanCentrality
from mca.utils.parameters import *

import shapefile
from shapely.wkb import loads
import networkx as nx
import functools
import traceback

# --- wxPython threadsafe  ---
from threading import Thread
import wx
from wx.lib.pubsub import Publisher


class LocalCloseness(NodeCentrality):

    def createSubGraphs(self):
        r""" Create a sub graph for all nodes

        Returns
        -------
        self.localGraphs : dictionary
            Dictionary of nodes with local graph as the value.
        """
        self.localGraphs = {} # store one Graph per node

        # find the sub graph of all nodes contained in the radius
        for n in self.G.nodes():
            self.localNodes = [n]
            self.getLocalNeighbours(n, 0)
            #print 'local nodes: %s' %self.localNodes
            self.localGraphs[n] = self.G.subgraph(self.localNodes)

        self.consoleAppend('Subgraphs created')

    def getLocalNeighbours(self, n, dist):
        r""" Get all nodes until the given distance on the network

        Recursive function.

        Parameters
        ----------
        n : node
          The node from which find the close neighbours
        dist : distance
          the distance already travel to come in the n node

        Returns
        -------
        self.localNodes : array
            Array of nodes distant of dist or less
        """
        edges = self.G[n]
        for e in edges.items():
            to = e[0]
            if not(to in self.localNodes):
                w = e[1][0]['weight']
                d = dist + w
                if d <= self.radius:
                    self.localNodes.append(to)
                    self.getLocalNeighbours(to, d)
                #else:
                    #print 'too far'
            #else:
                #print 'already done'
        #print 'end for %s' %n

    def computeCC(self):
        r""" Compute centrality on all sub graph

        Returns
        -------
        self.c_values : float with closeness centrality as the value.
        """
        self.consoleAppend('Start computing closeness centrality on nodes')

        # initialiaze timer
        t0 = time.time()
        nb = len(self.localGraphs.items())
        iteration = nb/20
        progress = iteration
        i = 0
        percent = 5
        lengthG=len(self.G)

        self.all_c_values = {}
        for n, localG in self.localGraphs.items():
            # self.G is passed in the method overriden_closeness_centrality in centrality.py
            self.G = localG
            self.closeness_centrality(v=n, local=True, lengthG=lengthG)
            self.all_c_values[n] = self.c_values

            # print progress
            i = i + 1
            if i >= progress:
                progress = progress + iteration
                t1 = time.time()
                tf = t1 - t0
                percentage = int(round((float(i)/float(nb))*100, 0))
                txt = 'Closeness computation %s %% sor far in %s' %(percentage, GetTextTime(tf))
                self.consoleAppend(txt)

        self.c_values = self.all_c_values
        self.consoleAppend('Closeness centrality values have been computed')
        # One does not need the graph anymore
        del self.G


class NodeLocalCloseness(LocalCloseness):

    def __init__(self, path, radius, fileName, callback, weighted=True, normalized=True, local=True):
        Centrality.__init__(self) # init Worker Thread Class
        self.radius = radius
        self.callback = callback
        self.weighted = weighted
        self.normalized = normalized
        self.local = local
        self.column_name = 'closeness'
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
            self.createSubGraphs()
            self.computeCC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of local closeness on edges.")
            self.stop()

class EdgeLocalCloseness(NodeMeanCentrality, LocalCloseness):

    def __init__(self, path, radius, fileName, callback, weighted=True, normalized=True, local=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.radius = radius
        self.callback = callback
        self.weighted = weighted
        self.normalized = normalized
        self.local = local
        self.column_name = 'closeness'
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
            self.createSubGraphs()
            self.computeCC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of local edge closeness.")
            self.stop()


class NodeCloseness(NodeCentrality):

    def __init__(self, path, fileName, callback, weighted=True, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.weighted = weighted
        self.normalized = normalized
        self.column_name = 'closeness'
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
            self.computeCC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of node closeness.")
            self.stop()

    def computeCC(self):
        self.consoleAppend('Start computing closeness centrality on nodes')
        self.closeness_centrality()
        self.consoleAppend('Closeness centrality values on nodes have been computed')
        # One doesn't need the graph anymore
        del self.G


class EdgeCloseness(NodeMeanCentrality):

    def __init__(self, path, fileName, callback, weighted=True, normalized=True):
        Centrality.__init__(self) # init Worker Thread Class

        self.callback = callback
        self.weighted = weighted
        self.normalized = normalized
        self.column_name = 'closeness'
        self.path = path
        self.file_name = fileName
        self.path_2_shp = os.path.join(self.path, self.file_name) + '.shp'
        self.path_2_log = os.path.join(self.path, self.file_name) + '.log'

        self.G = nx.Graph()
        self.buildQuery()

        self.start() # start the thread

    def run(self):
        try:
            self.createGraph()
            self.computeCC()
            self.createShp()
            self.consolePrintCreatedFiles()
            wx.CallAfter(Publisher().sendMessage, self.callback, self.path_2_log)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the computation of edge closeness.")
            self.stop()

    def computeCC(self):
        self.consoleAppend('Start computing closeness centrality on edges')
        self.closeness_centrality()
        self.consoleAppend('Closeness centrality values on edges have been computed')
        # One doesn't need the graph anymore
        del self.G
