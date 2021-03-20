'''
Create a .RBK file with certain settings
'''

import struct
import binascii


# Define the keyboard type to create the registration for. It seems this doesn't
# matter too much.
TARGET_KEYBOARD = "CT-X700"

# A basic registration to use as a starting point
BASIC_REG = b'\x01\x0c            \x02\x01x\x03\x02\x0b\x07\x10\n\x00\x011\x01 \x01\x00\x01\x00\x00"\x04\x01\x01\x01\x00#\x04\x00\x00\xff\x00%\x04\x00\x00\x01\x01 \x01\x01!\x016\x0c\x01\x00\n\x01\x00\x0b\x01\x00\xf0\x02\x00\x04\xf0\x02\x01\x00\xf0\x02\x02\x04\xf0\x02\x03\x04\xf0\x02\x042\xf0\x02\x05\x00\xf0\x02\x06\x00\x04\x01\x00\x11\x05\x7f\x7f\x7f\x7fd\x12\x05@@@@@\x13\x05\x00\x00\x00\x00\x00\x14\x05\x00\x00\x00\x00\x00\x15\x05\x1e$\x07((\x16\x05\x00\x00\x00\x00\x00\x17\x05\x00\x00\x00\x00\x00\x1a\x05\x01\x00\x00\x00\x00\x18\x05\x02\x02\x02\x02\x02<\x01A4\x04\x00\x00\x00\x00=\x01\x00^\x02\x17\x10\x0e\x01\x00\r\x01\x00\x0f\x02\xff\xff\x81\x01\x00\t\x01\x00\x83\x01\x02\x84\x01d@\x01s\x85\x01\x00\x86\x01\x00\x87\x01\x00\xff\x00'



class Atom:
  Volumes = 0x11
  
  

def change_volumes(original, volumes):
  # original: a registration string to change
  # volumes: an array of up to 4 values to write into the 0x11 atom.
  
  i = 0
  while i < len(original):
    
    atom_type, atom_len = struct.unpack_from('<2B', original, i)
    if atom_type == Atom.Volumes:
      if len(volumes) > atom_len:
        raise Exception("Too many volume values")
      b = bytearray(original)
      for j, x in enumerate(volumes):
        
        b[i+2+j] = x
      return bytes(b)
    i += 2 + atom_len
  raise Exception("Didn't find volumes atom")


def make_rbk_file(regs):
  
  if len(regs) != 4:
    raise Exception("Need exactly 4 registrations to make an .RBK file. Got {0}".format(len(regs)))
    
  b = TARGET_KEYBOARD.encode('ascii').ljust(16, b'\x00')
  b += b'RBKH'
  b += struct.pack('<I', 0)
  
  for k, reg in enumerate(regs):
    
    reg[2:14] = "Regist    {0}".format(21+k).encode('ascii')
    
    b += b'REGH'
    b += struct.pack('<3I', 0, binascii.crc32(reg), len(reg))
    b += reg
    b += b'EODA'
    
  return b



if __name__=="__main__":

  #r = [change_volumes(BASIC_REG, [0x7F, 0x7F, 0x7F, 0x7F]),  # Reg 1 -- all volumes at default
  #     change_volumes(BASIC_REG, [0x7F, 0x50, 0x50, 0x50]),  # Reg 2 -- U1 slightly higher than others
  ##     change_volumes(BASIC_REG, [0x50, 0x7F, 0x50, 0x50]),  # Reg 3 -- U2 slightly higher than others
  #     change_volumes(BASIC_REG, [0x50, 0x50, 0x7F, 0x00])]  # Reg 4 -- L1 slightly higher than others

  r = [BASIC_REG, BASIC_REG, BASIC_REG, BASIC_REG]

  
  with open("002.RBK", "wb") as f1:
    f1.write(make_rbk_file(r))


