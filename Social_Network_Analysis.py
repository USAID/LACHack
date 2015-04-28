#!/usr/bin/python

###############################################################################
# Social Network Analysis
#
# This code is designed to work with the XLSX data exported from Crimson 
# Hexagon, and provides a few (potentially) useful social network measures. 
# It constructs a social network based on retweet relationships -- nodes in 
# the network are unique Twitter handles and directed edges are retweets.
# 
# To run it, you'll need to install the NetworkX library; you can find 
# installation instructions and (rather good) usage documentation at 
# https://networkx.github.io/
###############################################################################

import xlrd
import networkx as nx
from sys import argv,exit
import operator
import matplotlib.pyplot as plt

###############################################################################
# load_tw_data()
#
# Given the array returned by sys.argv, loads exported tweets into a NetworX
# DiGraph object with annotated nodes and edges. Note that edges point toward
# the re-tweeting author -- frequently-retweeted handles should have a very 
# high out-degree.
###############################################################################
def load_tw_data(argv):
  G = nx.DiGraph()
  for f in argv[1:]:
    book = xlrd.open_workbook(f)
    sh = book.sheet_by_index(0)
    for i in range(1,sh.nrows):
      tweet = sh.cell_value(rowx=i,colx=3)
      ts = tweet.split()
      if ("RT" in ts[0]) and (ts[1][0] == '@'):
        source = tweet.split()[1]
        if source[-1] == ':':   # strip trailing colon
          source = source[:-1]
        author = sh.cell_value(rowx=i,colx=4)
        name = sh.cell_value(rowx=i,colx=5)
        loc = sh.cell_value(rowx=i,colx=6)       
        klout = sh.cell_value(rowx=i,colx=8)
        gender = sh.cell_value(rowx=i,colx=12)
        date = sh.cell_value(rowx=i,colx=1)
        content = sh.cell_value(rowx=i,colx=3)
        G.add_node(author,name=name,loc=loc,klout=klout,gender=gender)
        G.add_edge(source,author,date=date,content=content)
  return G

###############################################################################
# top_pagerank()
#
# Output the nodes with the highest PageRank. This will return nodes that are 
# good sources of information that is often passed along by others. You can 
# read more about the PageRank algorithm at 
# http://en.wikipedia.org/wiki/PageRank
###############################################################################
def top_pagerank(G,n=20):
  iG = nx.DiGraph() # invert G
  for (n1,n2) in G.edges():
    iG.add_edge(n2,n1)
  pr = nx.pagerank(iG)
  if len(pr) < n:
    n = len(pr)
  sorted_pr = sorted(pr.items(),key=operator.itemgetter(1),reverse=True)
  print "Handle\tPageRank"
  for i in range(n):
    h = sorted_pr[i][0]
    print "\t".join(str(x) for x in [h,pr[h]])

###############################################################################
# top_pagerank()
#
# Output the nodes with the highest betweenness centrality. This can tell us
# which nodes are important "connectors" who interact with people who might
# not otherwise be connected. You can read more about betweenness centrality
# at: http://en.wikipedia.org/wiki/Betweenness_centrality
###############################################################################
def top_centrality(G,n = 20):
  c = nx.betweenness_centrality(G)
  sorted_c = sorted(c.items(),key=operator.itemgetter(1),reverse=True)
  in_deg = G.in_degree()
  out_deg = G.out_degree()
  if len(in_deg) < n:
    n = len(in_deg)
  print "Rank\tHandle\tcentrality\tin_deg\tout_deg"
  for i in range(n):
    h = sorted_c[i][0]
    print "\t".join(str(x) for x in [i+1,h,c[h],in_deg[h],out_deg[h]])

###############################################################################
# strongly_connected()
#
# In a directed graph, a set of nodes is strongly-connected if one can start
# at any of these nodes and arrive at any other. A social network with a large
# strongly-connected component shows a conversation where everyone is giving
# and receiving information, a small strongly-connected component indicates a
# "conversation" that is dominated by broadcasting, not information-sharing.
# http://en.wikipedia.org/wiki/Strongly_connected_component
###############################################################################
def strongly_connected(G,n = 20):
  sg = sorted(nx.strongly_connected_components(G), key = len, reverse=True)
  sg0 = G.subgraph(sg[0])
  print len(sg0),"of",len(G),"nodes in largest SCC"
  print "Highest-PageRank nodes in SCC:"
  top_pagerank(sg0)

###############################################################################
# simple_directed(G)
# 
# Given a directed graph G, plots a simple vizualization of the first 
# connected component. If no filename is provided, display to the screen.
#
# You'll probably see a lot of fan-shaped features (especially near the edges); 
# these are retweets radiating out from a single source. Directed edges
# are indicated by a thicker line at one end of the edge -- this can be a
# little hard to see for large graphs.
##############################################################################
def simple_directed(G, fname = ''):
  ug = nx.Graph(G.edges())
  sg = sorted(nx.connected_component_subgraphs(ug), key = len, reverse=True)
  # create subgraph with directed edges but no attributes (for plotting)
  # This is a little klugey; it would be better if problematic 
  # characters weren't loaded into graph attributes in the first place.
  sg0 = G.subgraph(sg[0])
  for n in sg0.nodes(data=True):
    for k in n[1].keys():
      del sg0.node[n[0]][k]
  nx.set_edge_attributes(sg0,'date','')
  nx.set_edge_attributes(sg0,'content','')
  pos=nx.graphviz_layout(sg0)
  nx.draw_networkx_edges(sg0,pos,alpha=0.2)
  if fname == '':
    plt.show()
  else:   
    plt.savefig(fname)

###############################################################################
# simple_undirected(G)
# 
# Given a directed graph G, plots a simple vizualization of the first 
# connected component, projected onto an undirected graph. If no filename is 
# provided, display to the screen. 
##############################################################################
def simple_undirected(G, fname = ''):
  ug = nx.Graph(G.edges())
  sg = sorted(nx.connected_component_subgraphs(ug), key = len, reverse=True)
  pos=nx.graphviz_layout(sg[0])
  nx.draw_networkx_edges(sg[0],pos,alpha=0.2)
  if fname == '':
    plt.show()
  else:   
    plt.savefig(fname)


###############################################################################
# Main program
###############################################################################
if __name__ == '__main__':
  # Load data
  G = load_tw_data(argv)
  # Create graph; report basic statistics
  ug = nx.Graph(G.edges())
  sg = sorted(nx.connected_component_subgraphs(ug), key = len, reverse=True)
  print "Nodes: ",len(G.nodes())
  print "Edges: ",len(G.edges())
  print "Connected component nodes: ",len(sg[0].nodes())
  print "Connected component edges: ",len(sg[0].edges())
  # Report high-PageRank nodes 
  print
  top_pagerank(G)
  # Report high-centrality nodes
  print
  top_centrality(G)
  # Report strongly-connected component
  print
  strongly_connected(G)
  # Show plot
  simple_undirected(G)
  
