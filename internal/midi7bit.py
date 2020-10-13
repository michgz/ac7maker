##
#
# Functions for encoding and decoding MIDI-style 7-bit byte strings.
#

import struct



def midi_7bit_to_8bit(b):

  r = 0  # remainder
  n = 0  # position of split
  i = 0  # pointer to input
  c = b'' # output
  
  
  while i<len(b):

    x = b[i]
  
    if x >= 128:
      raise Exception("Not valid 7-bit data at position {0} : {1:02X}!".format(i, x))

    if n == 0 or n == 8:
      r = x
      n = 0
    elif n == 1:
      c += struct.pack('<B', ((x&0x01)<<7) + r)
      r = x//2
    elif n == 2:
      c += struct.pack('<B', ((x&0x03)<<6) + r)
      r = x//4
    elif n == 3:
      c += struct.pack('<B', ((x&0x07)<<5) + r)
      r = x//8
    elif n == 4:
      c += struct.pack('<B', ((x&0x0f)<<4) + r)
      r = x//16
    elif n == 5:
      c += struct.pack('<B', ((x&0x1f)<<3) + r)
      r = x//32
    elif n == 6:
      c += struct.pack('<B', ((x&0x3f)<<2) + r)
      r = x//64
    elif n == 7:
      c += struct.pack('<B', ((x&0x7f)<<1) + r)
      r = 0
    i += 1
    n += 1
  if r != 0:
    raise Exception("Left over data! Probably an error")
  
  return c
  
  
  



def midi_8bit_to_7bit(b):
  r = 0  # remainder
  n = 0  # position of split
  i = 0  # pointer to input
  c = b'' # output
  
  while i<len(b):
    if n == 0 or n == 7:
      n = 0
      c += struct.pack('<B', 0x1*(b[i] & 0x7f))
      r = (b[i] & 0x80)//0x80
    elif n == 1:
      c += struct.pack('<B', r + 0x2*(b[i] & 0x3f))
      r = (b[i] & 0xc0)//0x40
    elif n == 2:
      c += struct.pack('<B', r + 0x4*(b[i] & 0x1f))
      r = (b[i] & 0xe0)//0x20
    elif n == 3:
      c += struct.pack('<B', r + 0x8*(b[i] & 0x0f))
      r = (b[i] & 0xf0)//0x10
    elif n == 4:
      c += struct.pack('<B', r + 0x10*(b[i] & 0x07))
      r = (b[i] & 0xf8)//0x8
    elif n == 5:
      c += struct.pack('<B', r + 0x20*(b[i] & 0x03))
      r = (b[i] & 0xfc)//0x4
    elif n == 6:
      c += struct.pack('<B', r + 0x40*(b[i] & 0x01))
      c += struct.pack('<B', (b[i] & 0xfe)//0x2)
      r = 0
    n += 1
    i += 1
  if n < 7:
    c += struct.pack('<B', r)
  return c
  



if __name__=="__main__":
  
  # Unit tests

  test_in = b'\x41\x43\x30\x37\x58\x5F\x00\x00\x1C\x00\x00' 
  test_out = midi_8bit_to_7bit(test_in)

  s = ''
  for t in test_out:
    s += "{0:02X} ".format(t)
    
  print(s)





  test_in = b'\x41\x06\x41\x39\x03\x6B\x17\x00\x00\x38\x00\x00'
  test_out = midi_7bit_to_8bit(test_in)

  s = ''
  for t in test_out:
    s += "{0:02X} ".format(t)
    
  print(s)

