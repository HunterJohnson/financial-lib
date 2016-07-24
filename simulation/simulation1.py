# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:32:27 2015

@author: hhjohnso
simulation of financial network contagion with random nodes & weights
"""
import random as rand
import networkx as nx

x = 1000

while x > 0:
    
    n = rand.randrange(50,100) # arbitrary values --> test w/ non random input
    e=rand.randrange(200,400) 
         
    pre = [] # / tuple 
    post = []
    
    pre.append(n)

    #print str(n) + " nodes pre-shock"

    G=nx.gnm_random_graph(n,e,directed=True) 


    K = 0.5
    phi = 0.5
    #print str(K) + " this is K"
    #print str(phi) + " this is phi"

    for x in G.nodes():
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
        
    n1 = G.nodes
    post.append(n1)
    
    x -= 1


    
