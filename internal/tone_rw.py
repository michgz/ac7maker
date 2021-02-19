"""
  Read & write TON files directly to the keyboard. Bulk uploads & downloads for
  some reason don't work, so it needs to be done parameter-by-parameter.
"""

import sys
from sysex_comms_internal import get_single_parameter
import binascii
import struct


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
  if p >= 10 and p <= 13:
    return 3
  if p >= 6 and p <= 7:
    return 3
  return 1


# Number to single-byte parameter
def to_1b(v):
  return struct.pack('B', v)

# Number to dual-byte parameter
def to_2b(v):
  return struct.pack('2B', v//128, v%128)

def tone_read(parameter_set, memory=3):
  
  y = []
  for p in range(1, PARAM_COUNT):   # don't read parameter 0. It's the name, and it's not important.
    
    z = []
    if p != 84:  # DSP name
      for b in range(block_count_for_parameter(p)):
        z.append(get_single_parameter(p, memory=memory, category=TONE_CATEGORY, parameter_set=parameter_set, block0=b))
    
    y.append(z)
    
  x = b'\x00' * 0x1A0
  
  # Name
  x[0x186:0x192] = b'            '

  for (a, b) in [(0, 0x00), (20, 0x88)]:
    
    x[b+0x00:b+0x02] = to_2b(y[a+7][0])
    x[b+0x02:b+0x04] = to_2b(y[a+6][0])
    x[b+0x04:b+0x06] = to_2b(y[a+7][1])
    x[b+0x06:b+0x08] = to_2b(y[a+6][1])
    x[b+0x08:b+0x0A] = to_2b(y[a+7][2])
    x[b+0x0A:b+0x0C] = to_2b(y[a+6][2])
    x[b+0x0C:b+0x0E] = to_2b(y[a+6][1])

    x[b+0x0E:b+0x10] = to_2b(y[a+10][0])
    x[b+0x10:b+0x12] = to_2b(y[a+11][0])
    x[b+0x12:b+0x14] = to_2b(y[a+10][1])
    x[b+0x14:b+0x16] = to_2b(y[a+11][1])
    x[b+0x16:b+0x18] = to_2b(y[a+10][2])
    x[b+0x18:b+0x1A] = to_2b(y[a+11][2])

    x[b+0x1C] = y[a+8][0]
    x[b+0x1D] = y[a+9][0]
    x[b+0x7E] = to_1b(y[a+14][0])
    x[b+0x7F] = to_1b(y[a+15][0])
    x[b+0x80] = to_1b(y[a+16][0])

    x[b+0x28:b+0x2A] = to_2b(y[a+13][0])
    x[b+0x2A:b+0x2C] = to_2b(y[a+12][0])
    x[b+0x2C:b+0x2E] = to_2b(y[a+13][1])
    x[b+0x2E:b+0x30] = to_2b(y[a+12][1])
    x[b+0x30:b+0x32] = to_2b(y[a+13][2])
    x[b+0x32:b+0x34] = to_2b(y[a+12][2])

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

    x[b+0x82:b+0x84] = to_2b(y[a+2])
    x[b+0x84] = to_1b(y[a+3])
    x[b+0x85] = to_1b(y[a+4])
    x[b+0x86] = to_1b(y[a+5])
    x[b+0x87] = y[a+1]
    

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

  x[0x121] = y[75][0]
  x[0x122] = y[76][0]
  x[0x123] = y[77][0]

  x[0x180] = to_1b(y[93][0])
  x[0x181] = to_1b(y[97][0])

  x[0x182] = to_1b(y[98][0])



  x[0x18C] = y[102][0]
  x[0x18D] = to_1b(y[103][0])
  x[0x18E] = to_1b(y[104][0])
  x[0x18F] = to_1b(y[105][0])
  x[0x194] = to_1b(y[107][0])
  x[0x195] = to_1b(y[108][0])

  
  x[0x1B6] = y[45][0]
  x[0x1B7] = y[46][0]
  x[0x1B8] = y[47][0]
  x[0x1B9] = y[48][0]
  x[0x1BA] = y[49][0]
  x[0x1BB] = y[50][0]
  x[0x1BC] = y[51][0]
  x[0x1BD] = y[52][0]
  x[0x1BE] = y[53][0]
  x[0x1BF] = y[54][0]

  x[0x1C0] = to_1b(y[78][0])
  x[0x1C1] = to_1b(y[79][0])


  # DSP parameters
  
  x[0x126:0x115] = b'                ' # Name
  for j in range(4):
    x[0x136+j*0x12] = y[85][j]
    x[0x137+j*0x12] = to_1b(y[86][j])

  # Filters
  
  x[0x19C] = (y[117][0] % 16) + 16*((y[118][0]//4) % 16)
  x[0x1A0] = (y[117][1] % 16) + 16*((y[118][1]//4) % 16)

  x[0x19D] = (y[118][0] % 4) + 4*(y[119][0] % 64)
  x[0x1A1] = (y[118][1] % 4) + 4*(y[119][1] % 64)

  x[0x19E] = (y[122][0] % 8) + 8*(y[121][0] % 2) + 16*(y[120][0] % 16)
  x[0x1A3] = (y[122][1] % 8) + 8*(y[121][1] % 2) + 16*(y[120][1] % 16)


  return x


def wrap_tone_file(x):
  y = b'CT-X3000        '
  y += b'TONH'
  y += struct.pack('<3I', 0, binascii.crc32(x), len(x))
  y += x
  y += b'EODA'
  return y 
  



if __name__=="__main__":
  sys.stdout.buffer.write(wrap_tone_file(tone_read(0)))

