"""
  Read & write TON files directly to the keyboard. Bulk uploads & downloads for
  some reason don't work, so it needs to be done parameter-by-parameter.
"""

import sys
import binascii
import struct
import time
import os

import pickle


## Functions:
#
#   tone_read(param_set, ...)
#   =========================
#
# Reads a tone from the "currently selected" memory segment (memory 3), and returns it
# in HBR form. This particular memory segment doesn't permit true HBR reads, so under
# the hood this is multiple single parameter reads. The same result could be
# achieved using internal.sysex_comms_internal.get_single_parameter() on every
# parameter, but that would be very slow -- about 90 seconds. This function takes
# only 10 seconds.
#
# Parameters:
#
#    param_set      The parameter set to read. Some possible values are:
#                      0-3   Keyboard tones
#                      8-15  Rhythm tones
#                      32-47 MIDI tones
#
# Returns:
#
#     HBR data as a byte-string
#
#
#
#   wrap_tone_file(x)
#   =================
#
# Wraps tone data in HBR format (for example, as returned by tone_read()) in file
# form that can be written to the keyboard over USB. Suitable for CT-X3000 or 
# CT-X5000.
#
# Parameter:
#
#    x             The HBR data as a byte-string
#
#
#  Returns:
#
#     File data as a byte-string
#





#### The below section taken from internal.sysex_comms_internal. Copied here in
#    order to make time optimisations to it


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
      raise Exception("SYSEX communication timed out. Exiting ...")


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
      w += struct.pack('<H', 0x7F7F & blk_x)
    w += struct.pack('<3H', parameter, index, length-1)
  if (tx):
    w += data
  w += b'\xf7'
  return w



def flush_port(f):
  # Flush the input queue
  parse_response(os.read(f, 20))
  time.sleep(0.02)


def get_single_parameter_time_optimised(f, parameter, category=3, memory=3, parameter_set=0, block0=0, block1=0, length=0, _debug=False):

  global type_1_rxed


  if _debug:
    t1 = time.time()

  # Flush the input queue - now don't!! This is very time-consuming
  
  #parse_response(os.read(f, 20))
  #time.sleep(0.02)
  
  if length>0:
    l = length
  else:
    l = 1
  
  
  type_1_rxed = b''

  # Read the parameter
  
  x1 = make_packet(parameter_set=parameter_set, category=category, memory=memory, parameter=parameter, block=[0,0,block1,block0], length=l)
  
  os.write(f, x1)
  time.sleep(0.01)
  
  
  if _debug:
    t2 = time.time()
  
  # Handle any response
  
  # The minimum length of a response packet is 26. The value "25" here ensures
  # that every response is split across 2 packets, which is optimal for speed.
  # (I think because otherwise the second read ends up waiting for the next b"\xfe"
  # MIDI clock, which can take many 10s of milliseconds).
  x2 = os.read(f,25)
  parse_response(x2)
  time.sleep(0.02)
  x3 = os.read(f,20)
  parse_response(x3)
  time.sleep(0.01)


  if _debug:
    t3 = time.time()
  
 
 
    print("Parameter {0} ([{1},{2}])".format(parameter, block1, block0))
    print("------------------------------------")
   
    
    print("     TX time: {0:.4f}".format(t2-t1))
    print("     RX time: {0:.4f} (lengths: {1}, {2})".format(t3-t2, len(x2), len(x3)))


    print("> " + str(binascii.hexlify(x1)))
    print("< " + str(binascii.hexlify(x2)))
    print("< " + str(binascii.hexlify(x3)))
  
  
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



PARAM_COUNT = 123  # Number of parameters. This is correct for CT-X3000/5000
TONE_CATEGORY = 3

# Return the number of blocks for a specific parameter
def block_count_for_parameter(p):
  if p >= 117 and p <= 122:
    return 2
  if p >= 85 and p <= 87:
    return 4
  if p >= 17 and p <= 20:
    return 7
  if p >= 10 and p <= 11:
    return 7
  if p >= 12 and p <= 13:
    return 7
  if p >= 6 and p <= 7:
    return 3
  if p >= 37 and p <= 40:
    return 7
  if p >= 30 and p <= 31:
    return 7
  if p >= 32 and p <= 33:
    return 7
  if p >= 26 and p <= 27:
    return 3
  return 1


# Number to single-byte parameter
def to_1b(v):
  return struct.pack('B', v)

# Number to dual-byte parameter
def to_2b(v):
  #return struct.pack('2B', v//128, v%128)
  return struct.pack('<H', v)

def check_less(v, mx):
  if v >= mx:
    print(v)
    raise Exception

def tone_read(parameter_set, memory=3, _debug=False):
  
  
  if True:
  
    if _debug:
      t1 = time.time()
  
    # Open the device
    f = os.open(DEVICE_NAME, os.O_RDWR)  
    
    flush_port(f)
  
    y = []
    for p in range(0, PARAM_COUNT):
      
      z = []
      if p != 0 and p != 84:  # Name or DSP name. They will be filled with default values only, so don't need to read
        for b in range(block_count_for_parameter(p)):
          length = 0
          if p == 87:
            length = 10
          z.append(get_single_parameter_time_optimised(f, p, length=length, memory=memory, category=TONE_CATEGORY, parameter_set=parameter_set, block0=b, _debug=_debug))
      
      y.append(z)

    # Close the device
    os.close(f)

    if _debug:
      t2 = time.time()
      print(" tone_read() function: time elapsed {0:.3f} seconds".format(t2-t1))
      
    
    with open('{0:03d}_PICKLE.bin'.format(parameter_set+801), 'wb') as f8:
      pickle.dump(y, f8)
  
  

  else:
    
    with open('{0:03d}_PICKLE.bin'.format(parameter_set+801), 'rb') as f9:
      y = pickle.load(f9)

  
  x = bytearray(b'\x00' * 0x1C8)
  
  # Name
  x[0x1A6:0x1B6] = b'                '

  for (a, b) in [(0, 0x00), (20, 0x88)]:
    
    x[b+0x00:b+0x02] = to_2b(y[a+7][0])
    x[b+0x02:b+0x04] = to_2b(y[a+6][0])
    x[b+0x04:b+0x06] = to_2b(y[a+7][1])
    x[b+0x06:b+0x08] = to_2b(y[a+6][1])
    x[b+0x08:b+0x0A] = to_2b(y[a+7][2])
    x[b+0x0A:b+0x0C] = to_2b(y[a+6][2])

    x[b+0x0C:b+0x0E] = to_2b(y[a+11][0])
    x[b+0x0E:b+0x10] = to_2b(y[a+10][0])
    x[b+0x10:b+0x12] = to_2b(y[a+11][1])
    x[b+0x12:b+0x14] = to_2b(y[a+10][1])
    x[b+0x14:b+0x16] = to_2b(y[a+11][2])
    x[b+0x16:b+0x18] = to_2b(y[a+10][2])
    x[b+0x18:b+0x1A] = to_2b(y[a+11][3])

    x[b+0x1A:b+0x1C] = to_2b(y[a+10][3])
    x[b+0x1C:b+0x1E] = to_2b(y[a+11][4])
    x[b+0x1E:b+0x20] = to_2b(y[a+10][4])
    x[b+0x20:b+0x22] = to_2b(y[a+11][5])
    x[b+0x22:b+0x24] = to_2b(y[a+10][5])
    x[b+0x24:b+0x26] = to_2b(y[a+11][6])
    x[b+0x26:b+0x28] = to_2b(y[a+10][6])

    x[b+0x7C] = y[a+8][0] 
    x[b+0x7D] = y[a+9][0] 
    x[b+0x7E:b+0x7F] = to_1b(y[a+14][0])
    x[b+0x7F:b+0x80] = to_1b(y[a+15][0])
    x[b+0x80:b+0x81] = to_1b(y[a+16][0])

    x[b+0x28:b+0x2A] = to_2b(y[a+13][0])
    x[b+0x2A:b+0x2C] = to_2b(y[a+12][0])
    x[b+0x2C:b+0x2E] = to_2b(y[a+13][1])
    x[b+0x2E:b+0x30] = to_2b(y[a+12][1])
    x[b+0x30:b+0x32] = to_2b(y[a+13][2])
    x[b+0x32:b+0x34] = to_2b(y[a+12][2])
    x[b+0x34:b+0x36] = to_2b(y[a+13][3])
    x[b+0x36:b+0x38] = to_2b(y[a+12][3])
    x[b+0x38:b+0x3A] = to_2b(y[a+13][4])
    x[b+0x3A:b+0x3C] = to_2b(y[a+12][4])
    x[b+0x3C:b+0x3E] = to_2b(y[a+13][5])
    x[b+0x3E:b+0x40] = to_2b(y[a+12][5])
    x[b+0x40:b+0x42] = to_2b(y[a+13][6])
    x[b+0x42:b+0x44] = to_2b(y[a+12][6])

    x[b+0x44:b+0x46] = to_2b(y[a+18][0])
    x[b+0x46:b+0x48] = to_2b(y[a+17][0])
    x[b+0x48:b+0x4A] = to_2b(y[a+18][1])
    x[b+0x4A:b+0x4C] = to_2b(y[a+17][1])
    x[b+0x4C:b+0x4E] = to_2b(y[a+18][2])
    x[b+0x4E:b+0x50] = to_2b(y[a+17][2])
    x[b+0x50:b+0x52] = to_2b(y[a+18][3])
    x[b+0x52:b+0x54] = to_2b(y[a+17][3])
    x[b+0x54:b+0x56] = to_2b(y[a+18][4])
    x[b+0x56:b+0x58] = to_2b(y[a+17][4])
    x[b+0x58:b+0x5A] = to_2b(y[a+18][5])
    x[b+0x5A:b+0x5C] = to_2b(y[a+17][5])
    x[b+0x5C:b+0x5E] = to_2b(y[a+18][6])
    x[b+0x5E:b+0x60] = to_2b(y[a+17][6])

    x[b+0x60:b+0x62] = to_2b(y[a+20][0])
    x[b+0x62:b+0x64] = to_2b(y[a+19][0])
    x[b+0x64:b+0x66] = to_2b(y[a+20][1])
    x[b+0x66:b+0x68] = to_2b(y[a+19][1])
    x[b+0x68:b+0x6A] = to_2b(y[a+20][2])
    x[b+0x6A:b+0x6C] = to_2b(y[a+19][2])
    x[b+0x6C:b+0x6E] = to_2b(y[a+20][3])
    x[b+0x6E:b+0x70] = to_2b(y[a+19][3])
    x[b+0x70:b+0x72] = to_2b(y[a+20][4])
    x[b+0x72:b+0x74] = to_2b(y[a+19][4])
    x[b+0x74:b+0x76] = to_2b(y[a+20][5])
    x[b+0x76:b+0x78] = to_2b(y[a+19][5])
    x[b+0x78:b+0x7A] = to_2b(y[a+20][6])
    x[b+0x7A:b+0x7C] = to_2b(y[a+19][6])

    x[b+0x82:b+0x84] = to_2b(y[a+2][0])
    x[b+0x84:b+0x85] = to_1b(y[a+3][0])
    x[b+0x85:b+0x86] = to_1b(y[a+4][0])
    x[b+0x86:b+0x87] = to_1b(y[a+5][0])
    x[b+0x87] = y[a+1][0]
    

  x[0x110] = y[56][0]
  x[0x111] = y[57][0]
  x[0x112] = y[58][0]
  x[0x113] = y[60][0]
  x[0x114] = y[61][0]
  x[0x115] = y[62][0]
  x[0x116] = y[63][0]
  x[0x117] = y[64][0]
  x[0x118] = y[65][0]
  

  x[0x119] = y[67][0]
  x[0x11A] = y[68][0]
  x[0x11B] = y[69][0]
  x[0x11C] = y[70][0]

  x[0x11D] = y[71][0]
  x[0x11E] = y[72][0]
  x[0x11F] = y[73][0]
  x[0x120] = y[74][0]

  x[0x121:0x122] = to_1b(y[75][0])
  x[0x122:0x123] = to_1b(y[76][0])
  x[0x123:0x124] = to_1b(y[77][0])

  x[0x180:0x181] = to_1b(y[93][0])
  x[0x181:0x182] = to_1b(y[97][0])
  x[0x182:0x183] = to_1b(y[98][0])

  x[0x184:0x188] = struct.pack('<I', y[100][0])
  x[0x188:0x18C] = struct.pack('<I', y[101][0])
  x[0x18C] = y[102][0]
  x[0x18D:0x18E] = to_1b(y[103][0])
  x[0x18E:0x18F] = to_1b(y[104][0])
  x[0x18F:0x190] = to_1b(y[105][0])
  x[0x190:0x194] = struct.pack('<I', y[106][0])
  x[0x194:0x195] = to_1b(y[107][0])
  x[0x195:0x196] = to_1b(y[108][0])

  x[0x1B6:0x1B7] = to_1b(y[45][0])
  x[0x1B7:0x1B8] = to_1b(y[46][0])
  x[0x1B8:0x1B9] = to_1b(y[47][0])
  x[0x1B9:0x1BA] = to_1b(y[48][0])
  x[0x1BA:0x1BB] = to_1b(y[49][0])
  x[0x1BB:0x1BC] = to_1b(y[50][0])
  x[0x1BC:0x1BD] = to_1b(y[51][0])
  x[0x1BD:0x1BE] = to_1b(y[52][0])
  x[0x1BE:0x1BF] = to_1b(y[53][0])
  x[0x1BF:0x1C0] = to_1b(y[54][0])

  x[0x1C0:0x1C1] = to_1b(y[78][0])
  x[0x1C1:0x1C2] = to_1b(y[79][0])
  
  x[0x124] = 0xFF  # ??
  
  # DSP parameters
  
  x[0x126:0x136] = b'                ' # Name
  for j in range(4):
    x[0x136+j*0x12:0x138+j*0x12] = struct.pack('<H', y[85][j])
    if y[86][j] != 0:
      raise Exception
    # where is parameter 86?
    if len(y[87][j]) > 0 and len(y[87][j]) < 16:
      x[0x138+j*0x12:0x138+len(y[87][j])+j*0x12] = y[87][j]

  # Bit field parameters
  
  
  check_less(y[109][0], 2)
  check_less(y[111][0], 2)
  check_less(y[112][0], 2)
  
  if y[109][0]:
    x[0x196] = 1
  x[0x197] = y[110][0]
  if y[111][0]:
    x[0x198] = 1
  if y[112][0]:
    x[0x199] = 1

  v = 0
  check_less(y[113][0], 2)
  check_less(y[114][0], 2)
  check_less(y[115][0], 2)
  check_less(y[116][0], 4)
  if y[113][0]:
    v += 1
  if y[114][0]:
    v += 0x10
  if y[115][0]:
    v += 0x20
  v += 0x40*(y[116][0] % 4)
  x[0x19A] = v

  v = 0
  check_less(y[94][0], 16)
  check_less(y[95][0], 2)
  check_less(y[96][0], 2)
  check_less(y[99][0], 2)
  if y[99][0]:
    v += 1
  if y[96][0]:
    v += 0x04
  if y[95][0]:
    v += 0x08
  v += 0x10*(y[94][0] % 16)
  x[0x17E] = v

  v = 0
  check_less(y[88][0], 2)
  check_less(y[89][0], 2)
  check_less(y[90][0], 2)
  check_less(y[91][0], 2)
  check_less(y[92][0], 4)
  if y[91][0]:
    v += 0x02
  if y[90][0]:
    v += 0x04
  if y[89][0]:
    v += 0x08
  v += 0x20*(y[92][0] % 4)
  if y[88][0]:
    v += 0x80
  x[0x17F] = v

  v = 0
  check_less(y[55][0], 2)
  check_less(y[80][0], 2)
  check_less(y[81][0], 2)
  check_less(y[82][0], 2)
  check_less(y[83][0], 2)
  if y[83][0]:
    v += 0x01
  if y[82][0]:
    v += 0x02
  if y[81][0]:
    v += 0x04
  if y[80][0]:
    v += 0x08
  if y[55][0]:
    v += 0x80
  x[0x1A4] = v

  v = 0
  check_less(y[41][0], 2)
  check_less(y[42][0], 2)
  check_less(y[43][0], 8)
  check_less(y[44][0], 2)
  if y[44][0]:
    v += 0x01
  v += 2*(y[43][0] % 8)
  if y[42][0]:
    v += 0x40
  if y[41][0]:
    v += 0x80
  x[0x1A5] = v
  
  v = 0
  check_less(y[59][0], 16)
  check_less(y[66][0], 16)
  v += 16*(y[59][0] % 16)
  v += (y[66][0] % 16)
  x[0x124] = v


  # Filters

  check_less(y[117][0], 16)
  check_less(y[118][0], 64)
  check_less(y[119][0], 64)
  check_less(y[120][0], 16)
  check_less(y[121][0], 2)
  check_less(y[122][0], 8)
  check_less(y[117][1], 16)
  check_less(y[118][1], 64)
  check_less(y[119][1], 64)
  check_less(y[120][1], 16)
  check_less(y[121][1], 2)
  check_less(y[122][1], 8)
  
  x[0x19C] = (y[117][0] % 16) + 16*(y[118][0] % 16)
  x[0x1A0] = (y[117][1] % 16) + 16*(y[118][1] % 16)

  x[0x19D] = ((y[118][0]//16) % 4) + 4*(y[119][0] % 64)
  x[0x1A1] = ((y[118][1]//16) % 4) + 4*(y[119][1] % 64)

  x[0x19E] = (y[122][0] % 8) + 8*(y[121][0] % 2) + 16*(y[120][0] % 16)
  x[0x1A2] = (y[122][1] % 8) + 8*(y[121][1] % 2) + 16*(y[120][1] % 16)



  return x


def wrap_tone_file(x):
  y = b'CT-X3000'
  y += struct.pack('<2I', 0, 0)
  y += b'TONH'
  y += struct.pack('<3I', 0, binascii.crc32(x), len(x))
  y += x
  y += b'EODA'
  return y
  


if __name__=="__main__":
  sys.stdout.buffer.write(wrap_tone_file(tone_read(12)))

