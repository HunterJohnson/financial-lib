# -*- coding: utf-8 -*-
"""
Created on Sun Mar 01 19:26:14 2015
@author: Hunter
simulation of fnancial network  with 3d matplotlib graph
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import cm
import random as rand
from mpl_toolkits.mplot3d import Axes3D

""" LOOP 100K-1MM SIMULATIONS @ varying K/phi - optimize for max n nodes"""

n = rand.randrange(50,100) # arbitrary values --> test w/ non random input
e=rand.randrange(400,800) 

print str(n) + " nodes pre-shock"

G=nx.gnm_random_graph(n,e,directed=True) 

print "-----------Edge Weights--------"

for (u, v) in G.edges():     # edge weights
    G[u][v]["weighte"] = rand.randrange(1000,100000)   
   # print G[u][v]["weighte"]


print "----------Node Weights-----------"
x = 0


while x < len(G):                 # node weights  .... for x in G.nodes()?
    G.node[x]["weightn"] = rand.randrange(100000,1000000)
   # print G.node[x]["weightn"]
    x += 1
    

print "----------first graph-----------"
#nx.draw_circular(G)     # First graph (pre-shock)


# For each node calc cv/ ev values from paper
# decrease CV (net) by phi(EV), where phi is severity of shock 
# K - fraction of n nodes to be shocked 0-1 (random subset)



K = 0.7
phi = 0.7
print str(K) + " this is K"
print str(phi) + " this is phi"

for x in G.nodes():    # calc cv


    incoming = G.in_edges(x)
    
    sumi = 0
    for(u,v) in incoming:
        sumi += G[u][v]["weighte"]
        
    outgoing = G.out_edges(x)
    
    sumo = 0
    for(u,v) in outgoing:
        sumo += G[u][v]["weighte"]
        
    G.node[x]["cv"] = (G.node[x]["weightn"] + sumi) - sumo # effective share
  
  
    if(rand.randrange(1,100) > K*100) and (G.node[x]["cv"] > 0):
        G.node[x]["cv"] = (G.node[x]["cv"] * phi)
        
    if(G.node[x]["cv"] < 0):
        G.remove_node(x)

        
    """ select random subset of size (K * n nodes) where 0 < K < 1
        reduce subset cvs by phi 
    """



print str(len(G.nodes())) + " nodes post-shock"

print "----------new graph (after shock)-----------"
#nx.draw_circular(G)   

"""   ---- analysis : plot parameters (x) vs. number of surviving nodes (y)
"""

#node survial


x = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]    # K
y = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]    # phi
z = [0.944,0.925,0.908,0.899,0.891,0.885,0.880,0.873,0.859,0.842]       # surviving nodes

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection='3d')
ax.plot_trisurf(x,y,z, cmap=cm.jet, linewidth=0.2)
plt.show()



# more calculations

sume = 0.0 # interbank exposure / sum edges
for(u,v) in G.edges():
    sume += G[u][v]["weighte"]

print "-------Total Interbank Exposure = " + str(sume)

sumn = 0.0 # total nodes

for x in G.nodes():
    sumn += G.node[x]["weightn"]

ta = sume + sumn
y = sumn / ta
print "-------Total External Asset = " + str(sumn)
print "-------Total Asset = " + str(ta)
print "-------Y-ratio (equity to asset) = " + str(y)

"""
implement insolvency propagation equation (shocks on nodes) from paper
Node weights = bank capital/reserve
edge weights = value of interbank loans
Incoming = borrowed | Outgoing = lent
"""
