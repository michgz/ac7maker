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
## Dependencies:
#
# Needs crcmod. Install using:
#
#     pip3 install crcmod
#
#
## Functions:
#
#   upload_ac7(dest_num, data)
#   ==========================
#
# Uploads an AC7 rhythm to the keyboard. Parameters:
#
#   dest_num:  Number of the destination. Must lie in the user area, i.e.
#               values 294-343 inclusive.
#   data:      Byte array to write to the destination. It is in "HBR"
#               format, which is identical to the format of an .AC7 file
#               as saved by the keyboard. It should be possible to just
#               read an .AC7 file and upload it with no modification.
#
# Example:
#
#    with open("MyRhythm.AC7", "rb") as f:
#      x = f.read()
#    upload_ac7(294, x)
#
#
#   download_ac7(src_num)
#   =====================
#
# Downloads an AC7 rhythm from the keyboard. Parameter:
#
#   src_num:   Number of the source. Must lie in the user area, i.e.
#               values 294-343 inclusive.
#
#       Returns:
#
#   Byte array in "HBR" format. That is, it is identical to the format
#     of an .AC7 file as saved by the keyboard. It should be possible to
#     write to an .AC7 file which can be loaded into a keyboard by USB.
#
# Example:
#
#    with open("MyRhythm.AC7", "wb") as f:
#      f.write(download_ac7(294))
#

import time
import os
import struct
import sys
import crcmod



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

def handle_pkt(p):
  global is_busy
  global must_send_ack
  global have_got_ack
  global have_got_ess
  global total_rxed
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
    crc = crcmod.predefined.PredefinedCrc('crc-32')
    crc.update(p[1:-6])
    c = struct.unpack('<5B', p[-6:-1])
    crc_compare = c[0] + (1<<7)*c[1] + (1<<14)*c[2] + (1<<21)*c[3] + (1<<28)*c[4]
    if crc.crcValue == crc_compare:
      must_send_ack = True
      if type_of_pkt == 5:
        have_got_ack = True # This one must look like an ACK
        mm = midi_7bit_to_8bit(p[12:-6])
        total_rxed += mm
    else:
      print("BAD CRC!!!")



def parse_response(b):
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
      # Timed out. Completely exit the program
      print("SYSEX communication timed out. Exiting ...")
      sys.exit(0)


def make_packet(tx=False,
                category=30,
                memory=1,
                parameter_set=0,
                block=[0,0,0,0],
                parameter=0,
                index=0,
                length=1,
                command=-1,
                sub_command = 3,
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
  
  if command == 5:
    w += struct.pack('<2B', length%128, length//128)
    w += midi_8bit_to_7bit(data)
    crc = crcmod.predefined.PredefinedCrc('crc-32')
    crc.update(w[1:])
    w += midi_8bit_to_7bit(struct.pack('<I', crc.crcValue))
    w += b'\xf7'
    return w
    
  elif (command >= 2 and command < 8) or command == 0xD or command == 0xE: # OBR/HBR doesn't have the following stuff

    pass

    
  else:
    if len(block) != 4:
      print("Length of block should be 4, was {0}; setting to all zeros".format(len(block)))
      block = [0,0,0,0]
    for blk_x in block:
      w += struct.pack('<H', 0x7F7F & blk_x)
    w += struct.pack('<3H', parameter, index, length-1)
  if (tx):
    w += data
  w += b'\xf7'
  return w



def upload_ac7_internal(param_num, data, memory_num=1, category_num=30):

  # Open the device
  f = os.open(DEVICE_NAME, os.O_RDWR)


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
    
    
    pkt = make_packet(parameter_set=param_num, category=category_num, memory=memory_num, command=5, length=len_remaining, data = data[i:i+len_remaining])
    #print(pkt)
    os.write(f, pkt)
    wait_for_ack(f)
    i += len_remaining



  # Send ESS (no ACK expected)
  #print("Sending ESS")
  os.write(f, make_packet(parameter_set=param_num, category=30, memory=memory_num, command=0xd))
  time.sleep(0.3)

  # Send EBS (no ACK expected)
  #print("Sending EBS")
  os.write(f, make_packet(parameter_set=param_num, category=30, memory=memory_num, command=0xe))
  time.sleep(0.3)

  os.close(f)







def download_ac7_internal(param_num, memory_num=1, category_num=30):

  global have_got_ess
  global total_rxed

  # Open the device
  f = os.open(DEVICE_NAME, os.O_RDWR)


  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.4)


  total_rxed = b''


  # Send the SBS command

  pkt = make_packet(command = 8, sub_command = 2)
  #print(pkt)
  os.write(f, pkt)  # SBS(HBR)
  wait_for_ack(f)


  pkt = make_packet(command = 4, parameter_set=param_num, category=category_num, memory=memory_num)
  #print(pkt)
  os.write(f, pkt)  # HBR


  have_got_ess = False


  while True:


    wait_for_ack(f)
    
    if have_got_ess:
      break
    
    
    pkt = make_packet(parameter_set=param_num, category=30, memory=memory_num, command=0xa)
    os.write(f, pkt)



  # Send EBS (no ACK expected)
  os.write(f, make_packet(parameter_set=param_num, category=30, memory=memory_num, command=0xe))
  time.sleep(0.3)

  os.close(f)
  
  return total_rxed


if __name__=="__main__":
  raise Exception
