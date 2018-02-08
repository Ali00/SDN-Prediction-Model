import pox.lib.packet as pkt
import zmq  # Here we get ZeroMQ
import threading
from collections import deque  # Standard python queue structure
import json
import ast
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.recoco import Timer
from collections import defaultdict
from pox.openflow.discovery import Discovery
from pox.lib.util import dpid_to_str
import time
from datetime import datetime
from itertools import tee, izip
from matplotlib import pylab
from pylab import *
import igraph
from igraph import *
import numpy as np
import networkx as nx, igraph as ig
from random import randint
from collections import defaultdict
from itertools import tee, izip
import fnss
from fnss.units import capacity_units, time_units
import fnss.util as util
import sched
from threading import Timer
#calling disjoint path algorithm fuction as follows:
from disjoint_paths import edge_disjoint_shortest_pair
#-----------------------------------------------------

log = core.getLogger()
# Setup the ZeroMQ endpoint URL.
PUB_URL = "tcp://*:5555"  # Used for publishing information
REQ_URL = "tcp://*:5556"  # Used to receive requests

#f_link=[]               # To hold the link failure two nodes
#current_path=[]         # To hold the primary shortest path between any two nodes (e.g. 2 and 33)
#new_path=[]             # To hold the new sub_path (after link failure) based on one cluster/clique
#membership=None         # To hold the clusters
PATHS = []               # List holds all pairs that Definition of "corse"has path between them
L_PATHS = []             # List that holds the Labeled pairs that uses a sub-optimal path
d  = defaultdict(list)   # d is the dictionary that holds all the simple paths
d_2 = defaultdict(list)  # d2 is the dictionary that holds all the only optimal shortest paths
d_3 = defaultdict(list)  # d3 is the dictionary that holds all the optimal and sub-optimal shortest paths
c = 0                    # Global counter to be used as a condition
cc = 0                   # Global counter to be used as a condition
topology = None          # Global variable to hold the global network topology view
F_SET =[]                # Failure set that holds the actual failed links
#scheduler = sched.scheduler(time.time, time.sleep)
#--------------------------------------------------------------------------------------------
class GraphPrediction(EventMixin):
    G = nx.Graph()
    #scheduler = sched.scheduler(time.time, time.sleep)

    #----------------------------------------------------------------------------------------
    def __init__(self):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.PUB)  # Set up the ZMQ publisher "socket"
        self.socket.bind(PUB_URL)
        #self.scheduler = sched.scheduler(time.time, time.sleep)
    #----------------------------------------------------------------------------------------
        def startup():
            core.openflow.addListeners(self, priority = 0)
            core.openflow_discovery.addListeners(self)
        core.call_when_ready(startup, ('openflow','openflow_discovery'))
        print "init completed"
    #----------------------------------------------------------------------------------------
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '  Function that receives a link as a pair and then  '
    '  Checking the current pair with the current list   '
    '                                                    '
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def Check(self, Pair, List_of_pairs = [], *args):
        Flag = False
        for x in List_of_pairs:
            if set (x) == set (Pair):
               Flag = True
               break
        return Flag
    #----------------------------------------------------------------------------------------
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' Function that receives a path like : (A,B,C) And return pair  '
    ' of nodes as a link edges like : (A,B),(B,C).                  '
    '                                                               '
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def pairwise(self,iterable):
         a, b = tee(iterable)
         next(b, None)
         return izip(a, b)
    #---------------------------------------------------------------------------------------- 
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' Function that search about the any received pair of nodes     '
    ' then replace their past route (path) with a new one in d_2    '
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def replace_dictionary_values(self, key_to_find, new_route):
        #key_to_find -->  is the pair that need to be replaced with a new route
        global d_3

        for key in d_3.keys():
            if key == key_to_find:
               d_3[key] = new_route
               print 'The new updated route of', key_to_find, 'is:', d_3[key]

    #---------------------------------------------------------------------------------------- 
    '''''''''''''''''''''''''''''''''''''''''''''''''''''
    'Function that receives the predicted link and check'
    'if its belongs to F_SET , if so then all potential '
    'paths that associated with this link will be marked'
    'as sub-optimal by adding into L_PATHS set          '
    '''''''''''''''''''''''''''''''''''''''''''''''''''''
    def Prediction_Checker(self, P_Link, Potentials = [], *args):
        global L_PATHS
        global F_SET
        global d_3, d_2
        global topology

        topology = fnss.from_autonetkit(self.G)
        fnss.set_weights_constant(topology, 1)

        print 'Hi, Im Prediction_Checker function ... '
        F = self.Check (P_Link, F_SET)
        if F == True:
           print 'True Positive, the link is in F_SET'
        else:
           print 'False Positive, its false alarm'
           print 'The false Potential paths are: \n ', Potentials
           print 'Will remove from the labeled paths L_PATHS'

           while (len(Potentials)!=0):
               src = Potentials[0][0]
               dst = Potentials[0][1]
               Two_disjoint_paths = edge_disjoint_shortest_pair(topology, src, dst)
               self.replace_dictionary_values(Potentials[0], Two_disjoint_paths[0])
               L_PATHS.remove(Potentials[0])
               Potentials.pop(0)
           print '**Potentials now is -->', Potentials
           print '**The updated L_PATHS is -->', L_PATHS

    #---------------------------------------------------------------------------------------- 
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    ' Function that called when there is a un-predicted link failure '
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def Down(self, Down_link):

        global PATHS, L_PATHS
        global topology
        global d_3
        Temp = []
        faild_paths = []
        shortest_p = []
        d_f = defaultdict(list) #Temporary dictionary to holds the unavalable Flows(paths)
        topology = fnss.from_autonetkit(self.G)
        fnss.set_weights_constant(topology, 1)

        print 'We are inside Down function now . . . '
        #First step --> cutting each path in d_3 into set of pairs (e.g. [1,2,3] = [(1,2),(2,3)] in store in d_f
        for i in range (len(d_3)):
            for pair in self.pairwise(d_3.values()[i]):
                d_f[d_3.keys()[i]].append(pair)
        #print 'The current d_f is', d_f
        #Second step --> check if the faild link is involved in the current paths of d_f
        for i in range (len(d_f)):
            Temp =  list(d_f.values())[i]
            Flag = self.Check (tuple(Down_link), Temp)
            if Flag == True:
               faild_paths.append(list(d_f.keys())[i])
               L_PATHS.append(list(d_f.keys())[i]) #Adding those potential paths as a labeled ones to L_PATHS set

        #Step three --> find an alternative path (with dijkstra) for all the affected paths in the faild_paths
        if not faild_paths:
               print 'There are no affected paths at the moment when the ', Down_link , 'fails'
               print faild_paths
        else:
               print 'The affected paths are: \n', faild_paths
               print 'There are currently', len(faild_paths), 'paths suffering from service unavailability'

        for i in range(len(faild_paths)):
            src = faild_paths[i][0]
            dst = faild_paths[i][1]
            new_p = nx.shortest_path(self.G, source= src, target = dst) #alternative shortest path with dijkstra
            self.replace_dictionary_values(faild_paths[i], new_p)

        for i in d_3:
            print 'Routes after update', d_3[i]
        print 'There are currently', len(L_PATHS), 'labeled paths'

    #---------------------------------------------------------------------------------------- 

    def prepare_link_failure(self, edge):

        global  PATHS, L_PATHS
        global d
        global d_2
        global d_3
        global topology
        #global scheduler
        scheduler = sched.scheduler(time.time, time.sleep)

        #Dis-joint paths procedure
        topology = fnss.from_autonetkit(self.G)
        fnss.set_weights_constant(topology, 1)

        #for i in range(len(PATHS)):
            #src = PATHS[i][0] 
            #dst = PATHS[i][1]
            #print edge_disjoint_shortest_pair(topology, src, dst)
        #End of Dis-joint paths procedure

        # Procedure of detecting the paths whose includes the predected link
        print "The link that will faile is  = {}".format(edge)
        print "POX is now calling the function prepare_link_failure"
        #Step 1
        for i in range (len(d_3)):
            #p= nx.shortest_path(self.G, source= PATHS[i][0], target = PATHS[i][1]) #shortest path of each pair
            #p = edge_disjoint_shortest_pair(topology, PATHS[i][0], PATHS[i][1])
            for pair in self.pairwise(d_3.values()[i]):
                d[d_3.keys()[i]].append(pair)
        #Step 2
            #for pair in self.pairwise(p[0]):
                #d[PATHS[i]].append(pair)
        TMP=[]
        POTENTIAL_PATHS = []
        Two_disjoint_paths = []
        The_Link = ast.literal_eval(edge) # To convert the link from Unicode to Tuple object
        for i in range (len(d)):
            TMP =  list(d.values())[i]
            Flag = self.Check (The_Link , TMP)
            if Flag == True:
               POTENTIAL_PATHS.append(list(d.keys())[i])
               L_PATHS.append(list(d.keys())[i]) #Adding those potential paths as a labeled ones to L_PATHS set

        if not POTENTIAL_PATHS:
               print 'There are no Potential paths that affected from the link', The_Link , 'failure'
               print POTENTIAL_PATHS
        else:
               print 'The potential paths are: \n', POTENTIAL_PATHS
               print 'There are currently', len(POTENTIAL_PATHS), 'Potential paths'

        for i in range(len(POTENTIAL_PATHS)):
            src = POTENTIAL_PATHS[i][0]
            dst = POTENTIAL_PATHS[i][1]
            try:
                # When there is a proactive recovery for the current flow
                Two_disjoint_paths = edge_disjoint_shortest_pair(topology, src, dst)
                self.replace_dictionary_values(POTENTIAL_PATHS[i], Two_disjoint_paths[1])
            except:
                   print 'There is no disjoint path currently for the flow --> ', POTENTIAL_PATHS[i]
                   # When there is no proactive recovery for this flow 


        Timer(135, self.Prediction_Checker, (The_Link, POTENTIAL_PATHS,)).start() # After 2.25 min check if the predicted link in F_SE$

        for i in d_3:
            print 'Routes after update', d_3[i]
        print 'There are currently', len(L_PATHS), 'labeled paths'
        self.socket.send_string("There is a link predicted to fail soon.")  # Publish status

    #----------------------------------------------------------------------------------------

    def updater(self, State, link):
        global F_SET
        global d_2
        global d_3
        global L_PATHS
        global topology
        topology = fnss.from_autonetkit(self.G)
        fnss.set_weights_constant(topology, 1)

        print 'Im your updater function . . . '

        if State == True:
           print 'Its an added event of the link', link

           if not F_SET:   #Means the failure set is curently empty
                 print 'F_SET is empty now . . . '
           else:
                 F_SET.remove(link)

           if not L_PATHS :
              print 'There is no labeled/sub-optimal paths now ...'

           else:
              print 'The current sub-optimal path pairs are \n', L_PATHS
              i=0  # counter
              #for i in range (len(L_PATHS)):
              while (i < len(L_PATHS)):
                  Observer = True
                  Moderator = True

                  print ' i now is :', i
                  print 'The L_PATHS[i] is ', L_PATHS[i]
                  if len(d_3[(L_PATHS[i])]) > len(d_2[(L_PATHS[i])]):
                     #check the sub-optimals against the optimals (first condition)
                     Observer = False
                     print 'The pair', L_PATHS[i], 'is currently sub-optimal and need to be replaced'
                     st = L_PATHS[i][0]
                     tr = L_PATHS[i][1]
                     Dis_j = edge_disjoint_shortest_pair(topology, st, tr)
                     #print 'Dis_j[0]= ', Dis_j[0]
                     #print 'd_2[(L_PATHS[i])] =', d_2[(L_PATHS[i])]
                     #print 'len Dis_j[0]=', len(Dis_j[0]), 'and len(d_2[(L_PATHS[i])])= ', len(d_2[(L_PATHS[i])]) 
                     if len(Dis_j[0]) == len(d_2[(L_PATHS[i])]):
                        print 'Matched the condition 1 . . . '
                        self.replace_dictionary_values(L_PATHS[i], Dis_j[0]) # Go back to the optimal path flow_b1
                        print 'Replaced Succefully and', L_PATHS[i], 'Get Removed from -->  L_PATHS set'
                        L_PATHS.pop(i) #To remove the labeled pair from the sub-optimal list
                        Moderator = False
                        print 'L_PATHS currently has', len(L_PATHS), 'pair'
                        print L_PATHS

                  if (len(d_3[(L_PATHS[i])]) == len(d_2[(L_PATHS[i])])) and (Observer==True):
                     #check the sub-optimals against the optimals when first condition doesn not match
                     print ' Matched the condition 2 \n The sub-optimal and optimal has same number of hops'
                     print L_PATHS[i], 'Get removed'
                     L_PATHS.pop(i) #To remove the labeled pair from the sub-optimal list
                     Moderator = False
                     print 'L_PATHS currently has', len(L_PATHS), 'pair'
                     print L_PATHS

                  if (len(d_3[(L_PATHS[i])]) < len(d_2[(L_PATHS[i])])) and (Observer==True):
                     #This condition tackle the case when the current path (in d_3) has lenght less than the optimal one (in d_2)  
                     print ' Matched the condition 3 \n The sub-optimal has less length than the optimal'
                     print 'state of d_2', d_2[(L_PATHS[i])]
                     print 'state of d_3', d_3[(L_PATHS[i])]
                     d_2[(L_PATHS[i])] = d_3[(L_PATHS[i])]
                     print 'After change, d_2 becomes = ', d_2[(L_PATHS[i])]
                     print '***********************************************'
                     print L_PATHS[i], 'Get removed'
                     L_PATHS.pop(i) #To remove the labeled pair from the sub-optimal list
                     Moderator = False
                     print 'L_PATHS currently has', len(L_PATHS), 'pair'
                     print L_PATHS

                  if Moderator == True:
                     i = i+1


        print 'Currently, there are ', len(L_PATHS), 'of sub-optimal paths in L_PATHS'

        if State == False:
           print 'Its a remove event of link', link
           F_SET.append(link)
           #scheduler.enter(5, 1, self.Down, (link,))
           #scheduler.run()
           time.sleep(3)
           self.Down(link)

    #----------------------------------------------------------------------------------------

    def _handle_LinkEvent(self, event):

        l = event.link
        sw1 = l.dpid1
        sw2 = l.dpid2
        pt1 = l.port1
        pt2 = l.port2
        self.G.add_node( sw1 )
        self.G.add_node( sw2 )
        #global f_link
        global PATHS
        global c
        global cc
        global d_2
        global d_3
        global topology
        shortest_p=[]

        if event.added:
            self.G.add_edge(sw1,sw2)
            topology = fnss.from_autonetkit(self.G)
            link_x = [sw2,sw1]
            TT = True
        if event.removed:
            try:
                self.G.remove_edge(sw1,sw2)
                topology = fnss.from_autonetkit(self.G)
                print sw1, "---", sw2, "fails"
                link_x = [sw1,sw2]
                TT = False
            except:
                print "remove edge error"
        try:

             T = True
             N= nx.number_of_nodes(self.G)
             print "Number of nodes", N
             E= nx.number_of_edges(self.G)
             print "Number of Edges", E

             if (N == 26) and (E == 42) and (cc > 0):
                 self.updater(TT, link_x)

                 #if (TT == True) :
                    #print 'Its an added event'

             if (N == 26) and (E < 42) and (cc > 0):
                 self.updater(TT, link_x)

                 #if (TT == True):
                    #print 'its an added event'
                 #if (TT == False):
                    #print 'its a removed event'

             if (N == 26) and (E == 42) and (cc==0):
                 cc = cc + 1    # Now cc=1 
                 print "Graph is ready now . . . "
                 print "Graph nodes are: ",self.G.nodes()

             #------------------------------------------------------------------------------------------------------------    
                 Nodes= nx.nodes(self.G)
                 Edges= nx.edges(self.G)
                 # The below Procedure is to check whether there is a path between all possible pairs in the Network Graph
                 if c == 0:  # This is a condition to run the procedure only once
                    c+=1
                    for i in range (nx.number_of_nodes(self.G)):
                        for j in range (nx.number_of_nodes(self.G)):
                              if Nodes[i] != Nodes[j]:
                                 T= nx.has_path(self.G, Nodes[i], Nodes[j])
                                 Flg = self.Check ((Nodes[i], Nodes[j]) , PATHS)
                                 if (T==True) and (Flg==False):  # Condition for path existence and not exists in PATHS list
                                     p= nx.dijkstra_path(self.G, Nodes[i], Nodes[j])
                                     if len(p) > 2:
                                        PATHS.append(tuple((Nodes[i],Nodes[j])))
                    print 'All Possible PATHS are :'
                    for i in range (len(PATHS)):
                        print PATHS[i]

                 topology = fnss.from_autonetkit(self.G)
                 fnss.set_weights_constant(topology, 1)

                 for i in range (len(PATHS)):
                     source = PATHS[i][0]
                     destination = PATHS[i][1]
                     shortest_p = edge_disjoint_shortest_pair(topology, source, destination)
                     sh_path = shortest_p[0] #first shortest path of "SPb" according to the paper.
                     #sh_path= nx.shortest_path(self.G, source= PATHS[i][0], target = PATHS[i][1]) #shortest path of each pair
                     d_2[(PATHS[i])] = (sh_path)

                 print '------------------------------------------'
                 print 'The number of the all possible paths are: ', len(PATHS)
                 print '------------------------------------------'

                 for i in d_2:
                     print 'The optimal shortest path of the ', i, 'is : ', d_2[i]

                 print '------------------------------------------'
                 print 'The number of the all optimal shortest paths are: ', len(d_2)
                 print '------------------------------------------'

                 d_3 = d_2.copy()  # Creat a copy of d_2 to make changes of the sub-optimal paths

             #------------------------------------------------------------------------------------------------------------     
        except:
            print "no such complete Graph yet..."

#******************************************************************
def request_dispatcher():

    print "Starting request dispatcher..."
    context = zmq.Context.instance()
    socket = context.socket(zmq.REP)
    socket.bind(REQ_URL)
    while True:
        req_obj = socket.recv_json()
        print("Received request in dispatcher")
        if "type" not in req_obj:
            socket.send_json({"type": "Error", "what": "Unknown message, no 'type' field."})
            continue
        app = core.GraphPrediction
        type = req_obj["type"]
        #------------------------------------------------------------
        if type == "LinkFailure":

            Link = req_obj["link"]    # To get the link who will fail in the next future time         
            core.callLater(app.prepare_link_failure, Link)
            socket.send_json({"type": "processing", "what": req_obj})
        else:
            socket.send_json({"type": "Error", "what": "Unknown message type."})
        #------------------------------------------------------------

#*********************************************************************
def launch():

    thread = threading.Thread(target=request_dispatcher)

    thread.daemon = True

    thread.start()

    core.registerNew(GraphPrediction)
