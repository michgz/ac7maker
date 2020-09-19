#! /usr/bin/env python3

import sysex_comms
import ac7maker
import json
import copy



vals = [41]

with open("example-3.json", "r") as f1:
  b = json.load(f1)
  n = 294
  
  bb = copy.deepcopy(b)
  bb["rhythm"]["elements"][1]["var_33"] = []
  c = ac7maker.ac7maker(bb)
  print("Uploading to {0}".format(n))
  sysex_comms.upload_ac7(n, c)
  n += 1
  
  bb = copy.deepcopy(b)
  for pp in range(len(vals)):
    bb["rhythm"]["elements"][1]["var_33"][4] = vals[pp]
    print(bb["rhythm"]["elements"][1]["var_33"])
    c = ac7maker.ac7maker(bb)
    with open("abc.AC7", "wb") as f2:
      f2.write(c)
    print("Uploading to {0}".format(n))
    sysex_comms.upload_ac7(n, c)
    n += 1
    
    
    

