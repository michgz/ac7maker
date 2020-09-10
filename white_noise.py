#! /usr/bin/env python3

import sysex_comms
import ac7maker
import json





with open("example-2.json", "r") as f1:
  b = json.load(f1)
  
  for pp in range(20):
    b["rhythm"]["elements"][1]["var_35"][3] = 4*pp+3
    print(b["rhythm"]["elements"][1]["var_35"])
    c = ac7maker.ac7maker(b)
    print("Uploading to {0}".format(294+pp))
    sysex_comms.upload_ac7(294+pp, c)

