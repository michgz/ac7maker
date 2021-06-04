
'''For investigating similarities between the "Delay" DSP and the delay effect engine.

Based on input from a MIDI controller. This has been specifically written
for a Roland A-series controller with custom control maps.
'''

import sys

# We're importing from a sibling directory.
sys.path.append('..')
sys.path.append('../internal')

import struct
import time
import os
import os.path
import datetime
import random
from sysex_comms_internal import download_ac7_internal
from sysex_comms_internal import get_single_parameter, set_single_parameter, SysexTimeoutError
import threading
import queue
import subprocess
import select
import sys
import binascii


DEVICE_OUTPUT = '/dev/midi1'   # The CT-X3000
DEVICE_NAME = "hw:2,0,1"   # The Roland A-x00

'''
Make sure the control map is set to "1 CT-X Map".
'''


# Roland control map 1 after using "roland_apro.py" to assign:

CONTROLS = [
 (1, "Rotary1", 0x10),
 (2, "Rotary2", 0x11),
 (3, "Rotary3", 0x12),
 (4, "Rotary4", 0x13),
 (5, "Rotary5", 0x05),
 (6, "Rotary6", 0x4C),
 (7, "Rotary7", 0x4D),
 (8, "Rotary8", 0x4E),
 (9, "Rotary9", 0x0A),

 (11, "Slider1", 0x49),
 (12, "Slider2", 0x02),
 (13, "Slider3", 0x04),
 (14, "Slider4", 0x0C),
 (15, "Slider5", 0x0D),
 (16, "Slider6", 0x5C),
 (17, "Slider7", 0x5E),
 (18, "Slider8", 0x5F),
 (19, "Slider9", 0x07),
 
 (21, "Pad1", 0x24),
 (22, "Pad2", 0x26),
 (23, "Pad3", 0x2A),
 (24, "Pad4", 0x2E),
 (25, "Pad5", 0x2B),
 (26, "Pad6", 0x2F),
 (27, "Pad7", 0x32),
 (28, "Pad8", 0x31),
 
 (31, "Button1", 0x50),
 (32, "Button2", 0x51),
 (33, "Button3", 0x52),
 (34, "Button4", 0x53),
 
 (41, "Tranport1", 0x78),
 (42, "Tranport2", 0x79),
 (43, "Tranport3", 0x7A),
 (44, "Tranport4", 0x7B),
 (45, "Tranport5", 0x7C),
 (46, "Tranport6", 0x7D),
 (47, "Tranport7", 0x7E),
 (48, "Tranport8", 0x7F),
 (49, "Tranport9", 0x40)]



TONES = [(0, 5, "GRAND PIANO WIDE"),
         (19, 35, "ORGAN FLUTE"),
         (61, 2, "BRASS"),
         (80, 35, "8BIT WAVE"),
         (0, 120, "STD. KIT 1") 


         ]     # List of Patch, Bank pairs of available instruments. Maximum of 128

SELECTED_TONE = 0

CH = 0   # MIDI channel



def send(t):
  
  os.popen('amidi -p hw:1,0,0 --send-hex="' + binascii.hexlify(t, " ").decode('ascii').upper() + '"', "r").read()
  
  #print(" >>>     " + t.hex(' ').upper())
  




# Define the device ID. Constructed as follows:
#    0x44       Manufacturer ID ( = Casio)
#    0x19 0x01  Model ID ( = CT-X3000 or CT-X5000)
#    0x7F       Device. This is a "don't care" value
#
DEVICE_ID = b"\x44\x19\x01\x7F"




def process_parameter(x, v):
  
  
  
  byte_count = 1
  if x in [0,1,97,135,197,259,260,268,269,277,278,286,602,614,615]:
    byte_count = 2
  elif x in [85,133]:
    byte_count = 3
  elif x in [267,276,285,287,325,326,327,622]:
    byte_count = 5
  
  
  if byte_count == 1:
    return struct.pack('B', v%128)
  elif byte_count == 2:
    return struct.pack('BB', v%128, v//128)
  elif byte_count == 3:
    return struct.pack('BBB', v%128, (v//128)%128, v//(128*128))
  elif byte_count == 4:
    return struct.pack('BBBB', v%128, (v//128)%128, v//(128*128),0)
  elif byte_count == 5:
    return struct.pack('BBBBB', v%128, (v//128)%128, v//(128*128),0,0)
    
    
    
  raise Exception
  



def set_parameter(parameter, data,
                category=3,
                memory=3,
                parameter_set=32+CH,
                block=[0,0,0,0],
                block0 = 0,
                block1 = 0,
                index=0,
                length=1,
                command=-1,
                sub_command=3):


  w = b'\xf0' + DEVICE_ID
  command = 1
  w += struct.pack('<B', command)

  w += struct.pack('<2B', category, memory)
  w += struct.pack('<2B', parameter_set%128, parameter_set//128)
  
  if len(block) != 4:
    print("Length of block should be 4, was {0}; setting to all zeros".format(len(block)))
    block = [0,0,0,0]
  block[3] = block0
  block[2] = block1
  for blk_x in block:
    w += struct.pack('<BB', blk_x%128, blk_x//128)
  w += struct.pack('<BBHH', parameter%128, parameter//128, index, length-1)
  w += process_parameter(parameter, data)
  w += b'\xf7'
  return w





last_download = b''

TIME_BLOCK = 0
CURRENT_DSP = [0x00 ,0x3b ,0x36 ,0x6e ,0x6e ,0x01 ,0x60 ,0x7f ,0x00 ,0x6e ,0x6e ,0x5a ,0x07 ,0x62]


def set_current_dsp(parameter=87,
                category=3,
                memory=3,
                parameter_set=32+CH+1,
                block=[0,0,0,0],
                block0 = 0,
                block1 = 0,
                index=0,
                length=14,
                command=-1,
                sub_command=3):
  
  global CURRENT_DSP

  #set_single_parameter(4, struct.pack('14B', *CURRENT_DSP), category=16, memory=3, parameter_set=5, block0=0)
  
  w = b'\xf0' + DEVICE_ID
  command = 1
  w += struct.pack('<B', command)

  w += struct.pack('<2B', category, memory)
  w += struct.pack('<2B', parameter_set%128, parameter_set//128)
  
  if len(block) != 4:
    print("Length of block should be 4, was {0}; setting to all zeros".format(len(block)))
    block = [0,0,0,0]
  block[3] = block0
  block[2] = block1
  for blk_x in block:
    w += struct.pack('<BB', blk_x%128, blk_x//128)
  w += struct.pack('<BBHH', parameter%128, parameter//128, index, length-1)
  w += struct.pack('14B', *CURRENT_DSP)
  w += b'\xf7'
  return w


def change_time_block(tb):
  
  if tb == 0:
    # Delay
    print("TIME_BLOCK = Delay")
    send(struct.pack('BBB', 0xB0 + CH, 0x5B, 0x00))
    send(struct.pack('BBB', 0xB0 + CH, 0x5D, 0x00))
    send(struct.pack('BBB', 0xB0 + CH, 0x5E, 0x40))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5B, 0x00))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5D, 0x00))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5E, 0x00))

  elif tb == 1:
    # Chorus
    print("TIME_BLOCK = Chorus")
    send(struct.pack('BBB', 0xB0 + CH, 0x5B, 0x00))
    send(struct.pack('BBB', 0xB0 + CH, 0x5D, 0x40))
    send(struct.pack('BBB', 0xB0 + CH, 0x5E, 0x00))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5B, 0x00))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5D, 0x00))
    send(struct.pack('BBB', 0xB0 + CH+1, 0x5E, 0x00))

  else:
    print("TIME_BLOCK = {0}".format(tb))







def process(x):
  
  global last_download
  
  global TIME_BLOCK
  global TIME_BLOCK_LAYER
  global DO_TIMES
  global CURRENT_DSP

  if x[0] == 0x99 and x[2] > 0:
    # Probably a pad. Treat it as a binary control
    
    for ctl in CONTROLS:
      if ctl[1][:3] == "Pad":
        if ctl[2] == x[1]:
          TIME_BLOCK = ctl[0] - 21
          
          change_time_block(TIME_BLOCK)
          
          return




  if (x[0]&0xF0) == 0x80 or (x[0]&0xF0) == 0x90:
    
    
    # Artificially create a "split keyboard"
    if x[1] <=48:
      t = struct.pack('BB', (x[0]&0xF0) + CH+1, x[1] + 24) + x[2:]
    else:
      t = struct.pack('B', (x[0]&0xF0) + CH) + x[1:]
    
    send(t)
    return



  if (x[0]&0xF0) == 0xA0 or (x[0]&0xF0) == 0xD0 or (x[0]&0xF0) == 0xE0:
    
    t = struct.pack('B', x[0]&0xF0 + CH) + x[1:]
    
    send(t)
    return
    
  
  if (x[0]& 0xF0) == 0xC0:
    
    c = x[1]
    if c < len(TONES):
      
      t = struct.pack('BBBBBBBB', 0xB0 + CH, 0, TONES[c][1], 0xB0 + CH, 0x20, 0, 0xC0 + CH, TONES[c][0])
      
      send(t)
      
      print("Patch set to " + TONES[c][2])
      
      
      # Now re-set-up the second instrument.
      #x = get_single_parameter(228, category=2, memory=3, block0=32+CH)
      
      
      # Set to user tone 801. It doesn't matter what it is, but it must have 895
      # set as the DSP chain with all but the first Bypassed.
      t = struct.pack('BBBBBBBB', 0xB0 + CH+1, 0, 65, 0xB0 + CH+1, 0x20, 0, 0xC0 + CH+1, 0 + c)
      
      send(t)
      
      change_time_block(TIME_BLOCK)
      
      
      # Now set up the DSP
      
      CURRENT_DSP = [0x00 ,0x3b ,0x36 ,0x6e ,0x6e ,0x01 ,0x60 ,0x7f ,0x00 ,0x6e ,0x6e ,0x5a ,0x07 ,0x62]
      
      #set_single_parameter(228, x, category=2, memory=3, block0=32+CH+1)
      
      
      z = get_single_parameter(2, category=16, memory=3, parameter_set=5, block0=0)
      print("DSP type = {0}".format(z))
      
      
      # Set up the "Return" parameters on delay (they are known)
      t = set_parameter(107, 127, memory=3, category=2, parameter_set=0, block0=1)
      send(t)

      t = set_parameter(108, 0, memory=3, category=2, parameter_set=0, block0=1)
      send(t)

      t = set_parameter(106, 0, memory=3, category=2, parameter_set=0, block0=1)
      send(t)

      
      t = set_current_dsp()
      send(t)
      
      print(t.hex(' ').upper())


      return

  # If we get to this point, it must be a control
  
  control = -1
  
  if x[0] == 0xFC:
    
      # All notes off
    
      t = struct.pack('BBB', 0xB0 + CH, 120, 0)
      
      send(t)
      
      print("All Notes Off")
      
      return
  
  
  if (x[0]& 0xF0) == 0xB0 and len(x) >= 3:
    
    #print(binascii.hexlify(x, " ").decode('ascii').upper())
    
    
    if x[1] == 0x01:
      # Modulation wheel event - pass on
      
      t = struct.pack('BBB', 0xB0 + CH, 0x01, x[2])
      send(t)
      
      return



    if x[1] == 0x78 or x[1] == 0x7B:
      # "All sounds off" event - pass on
      
      t = struct.pack('BBB', 0xB0 + CH, x[1], x[2])
      send(t)
      
      return



    if x[1] == 0x50:
      
      # Button 1
      return



    if x[1] == 0x51:
      
      # Button 2
      return


    if x[1] == 0x52:  # Button 3 

      return



    if x[1] == 0x53:  # Button 4 
      
      return


    for ctl in CONTROLS:
      
      if x[1] == ctl[2]:
        
        control = ctl[0]
        break




    if TIME_BLOCK == 3:
      
      y = x[2]
      v = -1
      BLOCK0 = 0
      BLOCK1 = 0
      
      if (control >= 11 and control <= 19):
        
        v = [262,262,262,262,262,262,271,271,280][control - 11]
        BLOCK0 = [0,0,1,1,2,2,0,0,0][control - 11]
        BLOCK1 = [0,1,0,1,0,1,0,1,0][control - 11]
        
      elif (control >= 1 and control <= 9):
        
        v = [271,271,271,271,271,271,271,271,280][control - 1]
        BLOCK0 = [1,1,2,2,3,3,4,4,1][control - 1]
        BLOCK1 = [0,1,0,1,0,1,0,1,0][control - 1]
        
      
      if v >= 0:
        
        
        t = set_parameter(v, y, memory=3, category=2, parameter_set=0, block0=BLOCK0, block1=BLOCK1)

        send(t)
        
        print(t.hex(' ').upper())
        
        return
      
      
      

    if (control >= 11 and control <= 19) or (control >= 1 and control <= 9):

      y = x[2]
      v = -1
      
      d = -1


          
      if TIME_BLOCK == 0:
        #Delay
        if (control >= 11 and control <= 19):
          #v = [98,99,100,101,102,103,104,105,107][control - 11]
          
          
          v = [98,-1,99,-1,100,-1,104,-1,102][control - 11]
          d = [-1,1,-1,2,-1,3,-1,4,-1][control - 11]
          
          
          # 104 & 4 seem similar

          
        elif control == 1:
          # delay type
          v = 96
          y = (x[2]  + x[2]//4)//8
        elif control == 2:
          v = 97
          y = x[2] * 8 + random.randint(0,7)  # dithered. This isn't the full extent of the parameter, goes about 32x this
          
        elif control == 3:
          
          d = 12
          y = int(float(x[2]) * 1099. / 127. )
          
        elif control >= 4 and control <= 8:
          
          
          v = [103, -1, 101, -1, 105][control - 4]
          d = [-1, 6, -1, 7, -1][control - 4]
          

          # 101   R level
          # 102   L level
          
          
        elif control == 9:
          
          d = 5
          y = x[2]//64


      elif TIME_BLOCK == 1:
        #Chorus
        if (control >= 11 and control <= 18):
          v = [81,82,83,84,86,87,88,89][control - 11]
        elif control == 1:
          # chorus type
          v = 80
          y = x[2]//8
        elif control == 2:
          v = 85
          y = 3+x[2]*8


      if v >= 0:
        
        t = set_parameter(v, y, memory=3, category=2, parameter_set=0, block0=1)

        send(t)
        
        print(t.hex(' ').upper())
        
        return
        
        
      elif d >= 0:
        
        if d == 12:
          
          CURRENT_DSP[12] = y//100
          CURRENT_DSP[13] = y%100
          
          t = set_current_dsp()
          send(t)
          
          print(t.hex(' '))
          
          return
          
        else:
          
          CURRENT_DSP[d] = y
          
          t = set_current_dsp()
          send(t)
          
          print(t.hex(' '))
          
          return
          








      
    if control == 49:  # "L9". Use this to trigger a download
      
      if x[2] > 0:
      
        print("Getting new mapping ...")
        
        try:
          new_download = b''
          for iii in range(8):
            new_download += download_ac7_internal(iii, memory=3, category=16)
        
          print("Got, size {0}".format(len(new_download)))
        except SysexTimeoutError:
          # sometimes the download reads a -1 value. Catch it here, so it doesn't
          # crash the MIDI comms that are ongoing
          print("Crashed out with an error! Try again..")
          new_download = b''
        
        if len(new_download) > 0:
          if len(last_download) > 0:
          
            print("Found comparison")
          
            with open('/tmp/1', 'wb') as f1:
              f1.write(last_download)
            with open('/tmp/2', 'wb') as f2:
              f2.write(new_download)
            os.system('hexdump -Cv /tmp/1 > /tmp/3')
            os.system('hexdump -Cv /tmp/2 > /tmp/4')
            os.system('meld /tmp/3 /tmp/4')
            
              
        
        
          last_download = new_download



f_in = os.popen("amidi -d -p " + DEVICE_NAME, "r")

while True:
  f_in.readline()
  # The amidi output is "reverse linefeed", the linefeed comes immediately before any
  # data. So we must read the line first, then 8 bytes are immediately available
  m = f_in.read(2)
  t = bytes.fromhex(m)
  if len(t) == 1:
    expected_len = 0   # used for unknown
    
    if (t[0]& 0xF0) == 0x80:
      expected_len = 3
    elif (t[0]& 0xF0) == 0x90:
      expected_len = 3
    elif (t[0]& 0xF0) == 0xA0:  # aftertouch
      expected_len = 3
    elif (t[0]& 0xF0) == 0xB0:  # CC
      expected_len = 3
    elif (t[0]& 0xF0) == 0xC0:
      expected_len = 2
    elif (t[0]& 0xF0) == 0xD0:   # Aftertouch
      expected_len = 2
    elif (t[0]& 0xF0) == 0xE0:  # Pitch bend
      expected_len = 3
    elif t[0] == 0xFA:
      expected_len = 1
    elif t[0] == 0xFB:
      expected_len = 1
    elif t[0] == 0xFC:
      expected_len = 1
    
    
    if expected_len > 0:
      
      m = f_in.read(3*(expected_len-1))
      t += bytes.fromhex(m)

      process(t)
      


f_in.close()
f_out.close()
sys.exit(0)





q = queue.Queue()


def reading_thread():
  
  # Borrow amidi stuff from "mido" code


  _poller = select.poll()
  _proc = subprocess.Popen(['amidi', '-d',
                            '-p', DEVICE_NAME],
                             stdout=subprocess.PIPE)

  _poller.register(_proc.stdout, select.POLLIN)



  def _read_message():
    line = _proc.stdout.readline().strip().decode('ascii')
    if line:
      #print(line)
      return line
    else:
      # The first line is sometimes blank.
      #print("Is Blank")
      return None


  while True:

    x = _poller.poll(0)
    if x:
      print(x)
      msg = _read_message()
      if msg is None:
        msg = _read_message()
      if msg is not None:
        q.put(msg)
        #print(msg)








threading.Thread(target=reading_thread).start()


f = os.open(DEVICE_OUTPUT, os.O_RDWR)

while True:
  b = q.get()
  os.write(f, bytes.fromhex(b))
  #print(b)
  q.task_done()


os.close(f)










