
'''Applies real-time parameter changes to a tone.

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
from sysex_comms_internal import get_single_parameter, set_single_parameter
from tone_rw import tone_read
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



TONES = [(85, 16, "VOCAL CHOP SYNTH 1"),
         (85, 17, "VOCAL CHOP SYNTH 2"),
         (96, 36, "EDM LEAD SYNTH"),
         (96, 12, "EDM BRASS HIT"),
         (49, 1, "MELLOW STRINGS"),
         (6, 1, "HARPSICHORD 1")
         
         ]     # List of Patch, Bank pairs of available instruments. Maximum of 128

SELECTED_TONE = 0

CH = 0



def send(t):
  
  os.popen('amidi -p hw:1,0,0 --send-hex="' + binascii.hexlify(t, " ").decode('ascii').upper() + '"', "r").read()




# Define the device ID. Constructed as follows:
#    0x44       Manufacturer ID ( = Casio)
#    0x19 0x01  Model ID ( = CT-X3000 or CT-X5000)
#    0x7F       Device. This is a "don't care" value
#
DEVICE_ID = b"\x44\x19\x01\x7F"




def process_parameter(x, v):
  
  if x in [7,11,13,18,20]:   # Time parameter
  
    if v <= 10:
      y = [1023,944,800,831,797,778,769,760,752,744,736][v]
    elif v >= 128-10:
      y = 1024-[1023,944,800,831,797,778,769,760,752,744,736][128-v]  # First value in vector is not possible -- minimum is 80
    elif v == 64:
      y = 512
    elif v < 64:
      y = 736 - 3*(v-10)
    else:
      y = (1024-736) + 3*(118-v)
      
    return struct.pack('BB', y%128, y//128)
    
  
  if x in [6,10,12,17,19]:    # 8-bit parameter
    
    return struct.pack('BB', v%128, v//128)
    
  if x in [3,4,5,8,9,14,15,16]:    # 7-bit parameters
    
    return struct.pack('B', v%128)
    
  raise Exception
  





def length_of_parameter(x):
  
  if x == 20:
    return 2
  if x == 19:
    return 2
  return 1


def set_parameter(parameter, data,
                category=3,
                memory=3,
                parameter_set=32+CH,
                block=[0,0,0,0],
                block0 = 0,
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
  for blk_x in block:
    w += struct.pack('<BB', blk_x%128, blk_x//128)
  w += struct.pack('<BBHH', parameter%128, parameter//128, index, length-1)
  w += process_parameter(parameter, data)
  w += b'\xf7'
  return w





last_download = b''

TIME_BLOCK = 6






def do_time_block(tb, ctl_num, v):
  
  # tb: 
  #   0 = just sliders
  #   1 = short block
  #   2-6 = long blocks
  
  
  global TIME_BLOCK
  
  if tb == 0:
    
    if (ctl_num >= 11 and ctl_num <=18):
      
      p_num = [3, 4, 5, 8, 9, 14, 15, 16][ctl_num - 11]
      
      t = set_parameter(p_num, v, block0 = 0)
      print(binascii.hexlify(t, " ").decode('ascii').upper())
      send(t)
      
    return
    
    
  elif tb == 1:
    
    if (ctl_num >= 1 and ctl_num <= 3):
      
      block0 = ctl_num-1
      
      t = set_parameter(7, v, block0 = block0)
      print(binascii.hexlify(t, " ").decode('ascii').upper())
      send(t)
      
    

    elif (ctl_num >= 11 and ctl_num <=13):
      
      block0 = ctl_num-11
      
      t = set_parameter(19, v, block0 = block0)
      print(binascii.hexlify(t, " ").decode('ascii').upper())
      send(t)
      
    return



  else:


 
    
    if (ctl_num >= 1 and ctl_num <= 5) or ctl_num == 9:
      
      block0 = ctl_num-1
      if ctl_num == 9:
        block0 = 5
      
      t = set_parameter([11,13,18,20][tb-2], v, block0 = block0)
      print(binascii.hexlify(t, " ").decode('ascii').upper())
      send(t)
      
    

    elif (ctl_num >= 11 and ctl_num <=17):
      
      block0 = ctl_num-11
      
      t = set_parameter([10,12,17,19][tb-2], v, block0 = block0)
      print(binascii.hexlify(t, " ").decode('ascii').upper())
      send(t)
    
    return











def process(x):
  
  global last_download
  
  global TIME_BLOCK

  if x[0] == 0x99 and x[2] > 0:
    # Probably a pad. Treat it as a binary control
    
    for ctl in CONTROLS:
      if ctl[1][:3] == "Pad":
        if ctl[2] == x[1]:
          TIME_BLOCK = ctl[0] - 21
          
          print("Set new TIME BLOCK : {0}".format(TIME_BLOCK))
          
          return




  if (x[0]&0xF0) == 0x80 or (x[0]&0xF0) == 0x90 or (x[0]&0xF0) == 0xA0 or (x[0]&0xF0) == 0xD0 or (x[0]&0xF0) == 0xE0:
    
    t = struct.pack('B', x[0]&0xF0 + CH) + x[1:]
    
    send(t)
    return
    
  
  if (x[0]& 0xF0) == 0xC0:
    
    c = x[1]
    if c < len(TONES):
      
      t = struct.pack('BBBBBBBB', 0xB0 + CH, 0, TONES[c][1], 0xB0 + CH, 0x20, 0, 0xC0 + CH, TONES[c][0])
      
      send(t)
      
      print("Patch set to " + TONES[c][2])
      
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
    
    
    
    if x[1] >= 0x60 and x[1] <= 0x6E:
      
      # A filter control, or one of the parameters 200-202
      
      PARAM_NUM = [117,118,119,120,117,118,119,120,121,122,121,122,200,201,202][x[1]-0x60]
      BYTES = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1][x[1]-0x60]
      
      BLOCK = [0,0,0,0,1,1,1,1,0,0,1,1,0,0,0][x[1]-0x60]
    
      t = b'\xF0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00' + struct.pack('B', BLOCK) + b'\x00' + struct.pack('BB', PARAM_NUM%128, PARAM_NUM//128) + b'\x00\x00\x00\x00'
      
      
      
      DATA = 0
      if PARAM_NUM == 117:
        DATA = x[2]//16
      elif PARAM_NUM == 118:
        if x[2] <= 19:
          DATA = 0
        elif x[2] >= 107:
          DATA = 22
        else:
          DATA = (x[2] - 19) // 4
      elif PARAM_NUM == 119:
        if x[2] <= 40:
          DATA = 0
        elif x[2] >= 87:
          DATA = 24
        else:
          DATA = (x[2] - 39) // 2
      elif PARAM_NUM == 120:
        DATA = x[2]//8
      elif PARAM_NUM == 121:
        DATA = x[2]//64
      elif PARAM_NUM == 122:
        DATA = x[2]//16
      elif PARAM_NUM == 200:
        DATA = x[2]
      elif PARAM_NUM == 201 or PARAM_NUM == 202:
        DATA = x[2]//32

      
      t += struct.pack('B', DATA)
      
      for jjjj in range(BYTES-1):
        t += b'\x00'

      t += b'\xF7'
      

      send(t)
      
      print("\r    " + x.hex(' ').upper(), end="", flush=True)
      
      return
    
    
    
    
    
    
    
    
    
    
    for ctl in CONTROLS:
      
      if x[1] == ctl[2]:
        
        control = ctl[0]
        break
    
    
    if (control >0 and control <= 5) or (control == 9) or (control >= 11 and control <= 18):
      
      try:
        do_time_block(TIME_BLOCK, control, x[2])
      except IndexError:
        print("TIME_BLOCK = {0}".format(TIME_BLOCK))
        raise
      return
    
    
    if control >= 31 and control <= 34:
      # Button
      
      PARAM_NUM = [245,246,247,257][control-31]
      BYTES = [5,5,5,1][control-31]
      
      BLOCK = [0,0,0,0][control-31]
      t = b'\xF0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('B', BLOCK) + b'\x00' + struct.pack('BB', PARAM_NUM%128, PARAM_NUM//128) + b'\x00\x00\x00\x00'
      
      
      
      DATA = 0
      if x[2] >= 0x40:
        DATA = 1
      
      t += struct.pack('B', DATA)
      
      for jjjj in range(BYTES-1):
        t += b'\x00'

      t += b'\xF7'
      

      send(t)
      
      print(x.hex(' ').upper())
      
      return
    
    

    if control >= 1 and control <= 9:
      
      if True:
        # Rotary
        ###set_single_parameter(248 + (control-1) , x[2], memory=3, category=2)


        PARAM_NUM = [233,234,235,236,237,242,243,244,243][control-1]
        BITS = [7,7,7,7,7,7,7,7,7][control-1]
        
        #PARAM_NUM = [0,1,2,3][control-1]
        #BITS = [10, 10, 7, 7][control-1]

        
        BLOCK =  [0,0,0,0,0,0,0,0,1][control-1]
        t = b'\xF0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('B', BLOCK) + b'\x00' + struct.pack('BB', PARAM_NUM%128, PARAM_NUM//128) + b'\x00\x00\x00\x00'
        
        
        DATA = x[2]
        
        if PARAM_NUM == 242:
          
          if x[2] <= 0x20:
            DATA = 0
          elif x[2] <= 0x40:
            DATA = 1
          elif x[2] <= 0x60:
            DATA = 2
          else:
            DATA = 3
          
          
        
        
        if BITS >= 10:
          
          DATA = 8*x[2] + 3
          t += struct.pack('BB', DATA%128, DATA//128) + b'\xF7'
          
        else:
          
          t += struct.pack('B', DATA) + b'\xF7'
        

        send(t)
        
        print(x.hex(' ').upper())
        
        return
      
      else:
        
        
        PARAM_NUM = [248,249,250,251,252,253,254,255,256][control-1]
        BLOCK = [0,0,0,0,0,0,0,0,0][control-1]
        LEN = [1,1,1,1,1,1,1,1,1][control-1]
        
        
        t = b'\xF0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('B', BLOCK) + b'\x00' + struct.pack('BB', PARAM_NUM%128, PARAM_NUM//128) + b'\x00\x00\x00\x00' + struct.pack('B', x[2])

        if LEN > 1:
          
          t += b'\x00\xF7'
        else:
          t += b'\xF7'
        
        
        #DATA = 8*x[2] + 3
        
        #t = b'\xF0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('BB', PARAM_NUM%128, PARAM_NUM//128) + b'\x00\x00\x00\x00' + struct.pack('BB', DATA%128, DATA//128) + b'\xF7'
        
        send(t)
        
        print(x.hex(' ').upper())
        
        return
        
        
      
    if control == 49:  # "L9". Use this to trigger a download
      
      if x[2] > 0:
      
        print("Getting new mapping ...")
        
        new_download = tone_read(32)
        
        print("Got, size {0}".format(len(new_download)))
        
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










