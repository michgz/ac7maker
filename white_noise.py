#! /usr/bin/env python3

import sysex_comms
import ac7maker
import json
import copy



#vals = [0,7,14,21,28,35,42,49,56,63,70,77,84,91,98,105,112,119,126,127]
#vals = [0,15,28,41,54,67,80,93,106,119,127] 
#vals = [0,56,83,127]
vals = [0,7,15]
#vals = [0,25,50,75,100,127]
#vals = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

with open("example-2.json", "r") as f1:
  b = json.load(f1)
  
  bb = copy.deepcopy(b)
  bb["rhythm"]["elements"][1]["var_35"] = []
  c = ac7maker.ac7maker(bb)
  print("Uploading to {0}".format(294))
  sysex_comms.upload_ac7(294, c)  
  
  for pp in range(len(vals)):
    b["rhythm"]["elements"][1]["var_35"][5] = vals[pp]
    print(b["rhythm"]["elements"][1]["var_35"])
    c = ac7maker.ac7maker(b)
    print("Uploading to {0}".format(295+pp))
    sysex_comms.upload_ac7(295+pp, c)
    
    
    

