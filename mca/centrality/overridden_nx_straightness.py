"""
Straightness centrality measures.

"""

import functools
import networkx as nx
from geoalchemy import *
import wx
from wx.lib.pubsub import Publisher

import time
from math import sqrt
from mca.utils.utils import GetTextTime

__all__ = ['straightness_centrality']

def straightness_centrality(G, Node, Session, distance=True, normalized=True):

    if distance is True:
        distance='weight'
    path_length = functools.partial(nx.single_source_dijkstra_path_length,
                                      weight=distance)

    nodes = G.nodes()

    straightness_centrality = {}
    # TODO one request to get all the coordinates only
    # edges_coordinates = init_coordinates()

    # initialiaze timer
    t0 = time.time()
    nb = len(G)
    iteration = nb/20
    progress = iteration
    i = 0
    percent = 5

    # Initialize dictionary containing all the node id and coordinates
    coord_nodes = get_nodes_coords(Node, Session)

    for n in nodes:
        straightness = 0
        sp = path_length(G,n)
        if len(sp) > 0 and len(G) > 1:
            # start computing the sum of euclidean distances
            source = get_source(n, Node, Session)
            # if the source is not a virtual node
            if source is not None:
                for target in sp:
                    if n != target and target in coord_nodes:
                        network_dist = sp[target]
                        euclidean_dist = euclidean_distance(*coord_nodes[n]+coord_nodes[target])
                        straightness = straightness + ( euclidean_dist / network_dist )
                straightness_centrality[n]= straightness * ( 1.0 / (len(G)-1.0) )
                # normalize to number of nodes-1 in connected part
                if normalized:
                    s = ( len(G) - 1.0 ) / ( len(sp) - 1.0 )
                    straightness_centrality[n] *= s
        else:
            straightness_centrality[n]=0.0

        # print progress
        i = i + 1
        if i >= progress:
            progress = progress + iteration
            t1 = time.time()
            tf = t1 - t0
            percentage = int(round((float(i)/float(nb))*100, 0))
            txt = 'Straightness computation %s %% sor far in %s' %(percentage, GetTextTime(tf))
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", txt)

    return straightness_centrality


def get_source(node_id, Node, Session):
    query = Session.query(Node.geom.x.label('x'), Node.geom.y.label('y')).filter(Node.node_id == node_id)
    for q in query:
        return {'x': q.x, 'y': q.y}

def get_nodes_coords(Node, Session):
    coord_nodes = dict()
    query = Session.query(Node.node_id, Node.geom.x.label('x'), Node.geom.y.label('y'))
    for q in query:
        coord_nodes[q.node_id] = q.x, q.y
    return coord_nodes

def euclidean_distance(xs, ys, xt, yt):
    """ xs stands for x source and xt for x target """
    return sqrt((xs - xt)**2 + (ys - yt)**2)
