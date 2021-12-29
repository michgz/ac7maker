#! /bin/usr/python3

##
#
# A library of functions for communicating with a CT-X3000 keyboard over
# the MIDI interface. Linux only. Assumes that there is only one MIDI
# connection, i.e. the device will be located at "/dev/midi1".
#
# Casio keyboards other than CT-X3000 may also work with some of the
# functions, but none have been tested.
#
#
#
## Functions:
#
#   upload_ac7_internal(param_set, data, ...)
#   =========================================
#
# Uploads a bulk (HBR) set of data to a parameter set. By default, the destination
# is Category 30, Memory 1 (i.e. user AC7 rhythms). By overloading those defaults
# any location that accepts bulk writes can be written to.
#
#   param_set_num:  Parameter set number to be written. The possible values here
#                   depend on category and memory, in the case of user rhythms it
#                   is 0-49 inclusive
#   data:           Byte array of HBR data to write
#
# Example:
#
#    upload_ac7_internal(62, 0x1C8*b'\x00', category=3, memory=1)
#    #   ^-- Deletes (overwrites) user tone 863
#
#
#
#   download_ac7_internal(param_set, ...)
#   =====================================
#
# Download a bulk (HBR) set of data from a parameter set. By default, the origin
# is Category 30, Memory 1 (i.e. user AC7 rhythms). By overloading those defaults
# any location that accepts bulk reads can be read from.

#   param_set_num:  Parameter set number to be read. The possible values here
#                   depend on category and memory, in the case of user rhythms it
#                   is 0-49 inclusive
#
#        Returns:
#
#                   Byte array of HBR data
#
# Example:
#
#    print(download_ac7_internal(0, category=2, memory=3)[0xE01])
#    #   ^-- Prints the current master volume setting.
#
#
#
#   set_single_parameter(parameter, data, ...)
#   ==========================================
#
# Download a single parameter to a parameter set in the keyboard. By default, the
# destination is Category 3, Memory 3, Parameter Set 0 (i.e. the tone currently
# playing in Upper Keyboard 1). By overloading those defaults any location that
# accepts single-parameter writes can be written to.
#
#   parameter:      Parameter to be written. The possible values here depend on
#                   category and memory, in the case of tones it is 
#                   is 0-122 inclusive
#   data:           A number value or byte array to write. Numbers can be used
#                   for a parameter of length 1, and bit stuffing will be applied
#                   as needed. Possible range is up to 0-4095 inclusive (may be
#                   less for certain parameters). Byte arrays should be the correct
#                   length for the parameter and already have bit stuffing applied
#                   as needed.
#
# Examples:
#
#    set_single_parameter(43, 5)
#    #   ^-- Causes the tone in Upper Keyboard 1 to play up +1 octave
#    set_single_parameter(3, 32, category=2)
#    #   ^-- Reduces master volume to 25%
#    set_single_parameter(0, b'ABCDEFGHIJK', parameter_set=8, category=3, memory=1)
#    #   ^-- Changes the name of user tone 809 to ABCDEFGHIJK
#
#
#
#   get_single_parameter(parameter, length=0, ...)
#   ==============================================
#
# Reads a single parameter in a parameter set. If the parameter is a string, set
# "length" to be a positive integer up to the length of the parameter -- for
# example, if reading tone name (parameter 0), "length" must be in range 1-11
# inclusive. If "length" is not set, the parameter will be read as a number.
#
#
# Examples:
#
#    print(get_single_parameter(0, parameter_set=0, category=3, memory=1, length=11))
#    #   ^-- Prints the name of user tone 801 (likely to be "No Name    " or similar)
#    print(get_single_parameter(20, parameter_set=0, category=3, memory=1, block0=1))
#    #   ^-- Prints the internally stored version of tone 801's "Attack time" parameter
#
#
#
#   Common Parameters
#   =================
#
# All functions take these optional parameters:
#
#    fd      - device name to use. Default is '/dev/midi1'. To see what devices
#              are currently available on your (Linux) system, call:
#
#                ls /dev/midi*
#
#
#    fs      - device (file) stream to use. Default is None. If None, then parameter
#              fd will be the name of the device opened for the communications.
#              If non-None, it is expected that it is a stream which is already
#              open in Raw read/write mode.
#              This is useful for calling these functions in the middle of doing
#              other MIDI communications, without needing to close and re-open the
#              stream.
#
#              The general pattern for use is:
#
#                 import os
#                 _fs = os.open('/dev/midi1', os.O_RDWR)
#                 function_to_call(.... , fs=_fs)
#                 os.close(_fs)
#



import time
import os
import os.path
import struct
import sys
import binascii
import shelve



from internal.midi7bit import midi_7bit_to_8bit
from internal.midi7bit import midi_8bit_to_7bit


# Define the Linux device name. Assumes this is the only MIDI connection
DEVICE_NAME = "/dev/midi1"

# Define the device ID. Constructed as follows:
#    0x44       Manufacturer ID ( = Casio)
#    0x19 0x01  Model ID ( = CT-X3000 or CT-X5000)
#    0x7F       Device. This is a "don't care" value
#
DEVICE_ID = b"\x44\x19\x01\x7F"






is_busy = False
must_send_ack = False
have_got_ack = False
have_got_ess = False

so_far = b''

total_rxed = b''

type_1_rxed = b''

def handle_pkt(p):
  global is_busy
  global must_send_ack
  global have_got_ack
  global have_got_ess
  global total_rxed
  global type_1_rxed
  if len(p) < 7:
    print("BAD PACKET!!")
    return
  if p[0] != 0xF0 or p[1] != 0x44 or p[4] != 0x7F or p[-1] != 0xF7:
    print("BAD PACKET!!")
    return
  type_of_pkt = p[5]
  if type_of_pkt == 0xB:
    is_busy = True
  else:
    is_busy = False
    if type_of_pkt == 0xA:
      have_got_ack = True
    if type_of_pkt == 0xD:
      have_got_ack = True
      have_got_ess = True
      
      
  if type_of_pkt == 3 or type_of_pkt == 5:   # This takes a CRC
    c = struct.unpack('<5B', p[-6:-1])
    crc_compare = c[0] + (1<<7)*c[1] + (1<<14)*c[2] + (1<<21)*c[3] + (1<<28)*c[4]
    if binascii.crc32(p[1:-6]) == crc_compare:
      must_send_ack = True
      if type_of_pkt == 5:
        have_got_ack = True # This one must look like an ACK
        mm = midi_7bit_to_8bit(p[12:-6])
        total_rxed += mm
    else:
      print("BAD CRC!!!")


  if type_of_pkt == 1:
    v = p[24:-1]
    type_1_rxed = v


def parse_response(b, *, _debug=False):
  global so_far
  
  in_pkt = True
  if len(so_far) == 0:
    in_pkt = False
  
  for i in range(len(b)):
    x = b[i]
    if in_pkt:
      if x == 0xF7:
        so_far += b'\xf7'
        # Have completed. Do something!
        if _debug:
          print(so_far.hex(" ").upper())
        handle_pkt(so_far)
        in_pkt = False
        so_far = b''
      elif x == 0xF0:
        # Error! but start a new packet
        so_far = b'\xf0'
      elif x >= 0x80:
        # Error!
        in_pkt = False
        so_far = b''
      else:
        so_far += b[i:i+1]
    else:
      if x == 0xF0:
        so_far = b'\xf0'
        in_pkt = True

class SysexTimeoutError(Exception):
  pass

def wait_for_ack(f):
  global have_got_ack
  have_got_ack = False
  st = time.monotonic()
  while True:
    parse_response(os.read(f, 20))
    if have_got_ack:
      # Success!
      return
    time.sleep(0.02)
    if time.monotonic() > st + 4.0:
      # Clean up. We're exiting with an exception, but just in case a higher-
      # level process catches the exception we should have the port closed.
      os.close(f)
      # Timed out. Completely exit the program
      raise SysexTimeoutError("SYSEX communication timed out. Exiting ...")


def make_packet(tx=False,
                category=30,
                memory=1,
                parameter_set=0,
                block=[0,0,0,0],
                parameter=0,
                index=0,
                length=1,
                command=-1,
                sub_command=3,
                data=b''):


  w = b'\xf0' + DEVICE_ID
  if command < 0:
    if (tx):
      command = 1
    else:
      command = 0
  w += struct.pack('<B', command)

  if command == 0x8:
    return w + struct.pack('<B', sub_command) + b'\xf7'

  w += struct.pack('<2B', category, memory)
  w += struct.pack('<2B', parameter_set%128, parameter_set//128)

  if command == 0xA:
    return w + b'\xf7'
  
  elif command == 5:
    w += struct.pack('<2B', length%128, length//128)
    w += midi_8bit_to_7bit(data)
    crc_val = binascii.crc32(w[1:])
    w += midi_8bit_to_7bit(struct.pack('<I', crc_val))
    w += b'\xf7'
    return w

  elif (command >= 2 and command < 8) or command == 0xD or command == 0xE: # OBR/HBR doesn't have the following stuff

    pass

    
  else:
    if len(block) != 4:
      print("Length of block should be 4, was {0}; setting to all zeros".format(len(block)))
      block = [0,0,0,0]
    for blk_x in block:
      w += struct.pack('<BB', blk_x%128, blk_x//128)
    w += struct.pack('<BBHH', parameter%128, parameter//128, index, length-1)
  if (tx):
    w += data
  w += b'\xf7'
  return w



def set_single_parameter(parameter, data, category=3, memory=3, parameter_set=0, block0=0, block1=0, *, fd=DEVICE_NAME, fs=None, _debug=False):

  global type_1_rxed

  # Open the device (if needed)
  if fs is None:
    f = os.open(fd, os.O_RDWR)
  else:
    f = fs


  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.4)

  # Prepare the input
  d = b''
  l = 1

  if isinstance(data, type(0)):
    # The input is an integer. The "length" parameter passed to make_packet must be
    # 1, but we don't know how many bytes of bit-stuffed data the keyboard is actually
    # expecting. Read the current value to find that out.
    #
    # The values are cached in a shelving database to speed things up. Reading out
    # is quite a slow operation, so we want to do it as little as possible.
    
    
    KEY= f"{category:d},{parameter:d}"
    SHELVE_DB = os.path.join(os.path.dirname(__file__), "ctx_parameter_lengths.shelve")
    key_len = None
    
    with shelve.open(SHELVE_DB) as db:
      if KEY in db.keys():
        key_len = db[KEY]
    
    if key_len is None:
      type_1_rxed = b''

      # Read the current parameter value
      os.write(f, make_packet(parameter_set=parameter_set, category=category, memory=memory, parameter=parameter, block=[0,0,block1,block0], length=1))
      time.sleep(0.1)
      
      # Handle any response
      parse_response(os.read(f, 20))
      time.sleep(0.2)
      parse_response(os.read(f, 20))
      time.sleep(0.01)
      
      if len(type_1_rxed)<1 or len(type_1_rxed)>5:
        os.close(f)
        raise SysexTimeoutError("Not able to read out value to write")
      else:
        key_len = len(type_1_rxed)
        
        with shelve.open(SHELVE_DB) as db:
          db[KEY] = key_len
    
    
    # Now do the bit-stuffing
    for i in range(key_len):
      d = d + struct.pack('B', data&0x7F)
      data = data//0x80
    l = 1   # length is always 1 for numeric inputs

  else:
    # Assume the input is a byte array
    d = data
    l = len(d)
  

  # Write the parameter
  os.write(f, make_packet(tx=True, parameter_set=parameter_set, category=category, memory=memory, parameter=parameter, block=[0,0,block1,block0], length=l, data=d))
  time.sleep(0.1)
  
  # Handle any response -- don't expect one
  parse_response(os.read(f, 20))
  time.sleep(0.01)

  # Close the device
  if fs is None:
    os.close(f)





def get_single_parameter(parameter, category=3, memory=3, parameter_set=0, block0=0, block1=0, length=0, *, fd=DEVICE_NAME, fs=None, _debug=False):

  global type_1_rxed

  # Open the device (if needed)
  if fs is None:
    f = os.open(fd, os.O_RDWR)
  else:
    f = fs


  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.4)
  
  if length>0:
    l = length
  else:
    l = 1
  
  
  type_1_rxed = b''

  # Read the parameter
  os.write(f, make_packet(parameter_set=parameter_set, category=category, memory=memory, parameter=parameter, block=[0,0,block1,block0], length=l))
  time.sleep(0.1)
  
  # Handle any response
  parse_response(os.read(f, 20), _debug=_debug)
  time.sleep(0.2)
  parse_response(os.read(f, 20), _debug=_debug)
  time.sleep(0.01)

  # Close the device
  if fs is None:
    os.close(f)
  
  
  # Now decode the response. Value of "length" determines whether to regard it as
  # a string or a number
  if length > 0:
    # Regard the response as a string
    if len(type_1_rxed)>0:   # should maybe check this is equal to length??
      return type_1_rxed
    else:
      return b''   # Error! Nothing read
  else:
    # Regard the response as a number
    f = -1
    if len(type_1_rxed)>0:
      # A number has been received. Decode it.
      if len(type_1_rxed) == 1:
        f = struct.unpack('<B', type_1_rxed)[0]
      elif len(type_1_rxed) == 2:
        g = struct.unpack('<2B', type_1_rxed)
        if g[0] >= 128 or g[1] >= 128:
          raise Exception("Invalid packed value")
        f = g[0] + 128*g[1]
      elif len(type_1_rxed) == 3:
        g = struct.unpack('<3B', type_1_rxed)
        if g[0] >= 128 or g[1] >= 128 or g[2] >= 128:
          raise Exception("Invalid packed value")
        f = g[0] + 128*g[1] + 128*128*g[2]
      elif len(type_1_rxed) == 4:
        g = struct.unpack('<4B', type_1_rxed)
        if g[0] >= 128 or g[1] >= 128 or g[2] >= 128  or g[3] >= 128:
          raise Exception("Invalid packed value")
        f = g[0] + 128*g[1] + 128*128*g[2] + 128*128*128*g[3]
      elif len(type_1_rxed) == 5:
        g = struct.unpack('<5B', type_1_rxed)
        if g[0] >= 128 or g[1] >= 128 or g[2] >= 128  or g[3] >= 128 or g[4] >= 16:
          raise Exception("Invalid packed value")
        f = g[0] + 128*g[1] + 128*128*g[2] + 128*128*128*g[3] + 128*128*128*128*g[4]
      else:
        #raise Exception("Too long to be a number")
        pass
    return f






def upload_ac7_internal(param_set, data, memory=1, category=30, *, fd=DEVICE_NAME, fs=None, _debug=False):

  # Open the device (if needed)
  if fs is None:
    f = os.open(fd, os.O_RDWR)
  else:
    f = fs


  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.4)


  # Send the SBS command
  pkt = make_packet(command = 8, sub_command = 3)
  #print(pkt)
  os.write(f, pkt)  # SBS(HBS)
  wait_for_ack(f)


  i = 0
  while i < len(data):
    # Send a HBS packet:
    # Category 30 = Rhythms
    # Parameter set: indicates the specific rhythm
    # Memory 1 = user rhythm space
    
    len_remaining = len(data) - i
    if len_remaining > 0x80:
      len_remaining = 0x80 
    
    
    pkt = make_packet(parameter_set=param_set, category=category, memory=memory, command=5, length=len_remaining, data = data[i:i+len_remaining])
    #print(pkt)
    os.write(f, pkt)
    wait_for_ack(f)
    i += len_remaining



  # Send ESS (no ACK expected)
  #print("Sending ESS")
  os.write(f, make_packet(parameter_set=param_set, category=category, memory=memory, command=0xd))
  time.sleep(0.3)

  # Send EBS (no ACK expected)
  #print("Sending EBS")
  os.write(f, make_packet(parameter_set=param_set, category=category, memory=memory, command=0xe))
  time.sleep(0.3)

  if fs is None:
    os.close(f)







def download_ac7_internal(param_set, memory=1, category=30, *, fd=DEVICE_NAME, fs=None, _debug=False):

  global have_got_ess
  global total_rxed

  # Open the device (if needed)
  if fs is None:
    f = os.open(fd, os.O_RDWR)
  else:
    f = fs


  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.4)


  total_rxed = b''


  # Send the SBS command

  pkt = make_packet(command = 8, sub_command = 2)
  #print(pkt)
  os.write(f, pkt)  # SBS(HBR)
  wait_for_ack(f)


  pkt = make_packet(command = 4, parameter_set=param_set, category=category, memory=memory)
  #print(pkt)
  os.write(f, pkt)  # HBR


  have_got_ess = False


  while True:


    wait_for_ack(f)
    
    if have_got_ess:
      break
    
    
    pkt = make_packet(parameter_set=param_set, category=category, memory=memory, command=0xa)
    os.write(f, pkt)



  # Send EBS (no ACK expected)
  os.write(f, make_packet(parameter_set=param_set, category=category, memory=memory, command=0xe))
  time.sleep(0.3)

  if fs is None:
    os.close(f)
  
  return total_rxed


if __name__=="__main__":
  raise Exception
