"""
Closeness centrality measures.

"""
#    Copyright (C) 2004-2010 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
import functools
import networkx as nx
import time
from mca.utils.utils import GetTextTime
import wx
from wx.lib.pubsub import Publisher

__author__ = "\n".join(['Aric Hagberg (hagberg@lanl.gov)',
                        'Pieter Swart (swart@lanl.gov)',
                        'Sasha Gutfraind (ag362@cornell.edu)'])
__all__ = ['closeness_centrality']


def closeness_centrality(G, v=None, distance=None, normalized=True, local=False, lengthG=None):
    """Compute closeness centrality for nodes.

    Closeness centrality at a node is 1/average distance to all other nodes.

    Parameters
    ----------
    G : graph
      A networkx graph
    v : node, optional
      Return only the value for node v
    distance : string key, optional (default=None)
      Use specified edge key as edge distance.
      If True, use 'weight' as the edge key.
    normalized : bool, optional
      If True (default) normalize by the graph size.
    local: specify whether the computed closeness is local or not
    lengthG: specify the size (nb of nodes) of the main Graph when computing local closeness for normalization

    Returns
    -------
    nodes : dictionary
      Dictionary of nodes with closeness centrality as the value.

    See Also
    --------
    betweenness_centrality, load_centrality, eigenvector_centrality,
    degree_centrality

    Notes
    -----
    The closeness centrality is normalized to to n-1 / size(G)-1 where
    n is the number of nodes in the connected part of graph containing
    the node.  If the graph is not completely connected, this
    algorithm computes the closeness centrality for each connected
    part separately.
    """
    if distance is not None:
        if distance is True: distance='weight'
        path_length=functools.partial(nx.single_source_dijkstra_path_length,
                                      weight=distance)
    else:
        path_length=nx.single_source_shortest_path_length

    if v is None:
        nodes=G.nodes()
    else:
        nodes=[v]
    closeness_centrality={}

    # initialiaze timer
    t0 = time.time()
    nb = len(G)
    iteration = nb/20
    progress = iteration
    i = 0
    percent = 5

    for n in nodes:
        sp=path_length(G,n)
        totsp=sum(sp.values())
        if totsp > 0.0 and len(G) > 1:
            closeness_centrality[n]= (len(sp)-1.0) / totsp
            # normalize to number of nodes-1 in connected part
            if normalized and local:
                s=(len(sp)-1.0) / ( lengthG - 1 )
                closeness_centrality[n] *= s
            elif normalized:
                s=(len(sp)-1.0) / ( len(G) - 1 )
                closeness_centrality[n] *= s
        else:
            closeness_centrality[n]=0.0

        if local==False:
            # print progress
            i = i + 1
            if i >= progress:
                progress = progress + iteration
                t1 = time.time()
                tf = t1 - t0
                percentage = int(round((float(i)/float(nb))*100, 0))
                txt = 'Closeness computation %s %% sor far in %s' %(percentage, GetTextTime(tf))
                wx.CallAfter(Publisher().sendMessage, "consoleAppend", txt)

    if v is not None:
        return closeness_centrality[v]
    else:
        return closeness_centrality

