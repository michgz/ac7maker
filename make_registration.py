'''
Create a .RBK file with certain settings
'''

import struct
import binascii
from random import randint



# Registration format as it depends on the target keyboard
REGISTRATION_FORMATS = {
  'CT-X3000': {'bank_size': 8, 'file_version': 1},
  'CT-X5000': {'bank_size': 8, 'file_version': 1},
  'CT-X700':  {'bank_size': 4, 'file_version': 0},
  'CT-X800':  {'bank_size': 4, 'file_version': 0},  # ... presumed, not checked
  'CDP-S350': {'bank_size': 4, 'file_version': 1}
}




# A basic registration to use as a starting point. This comes from a X700 but
# seems to be accepted fine by other models.
#
BASIC_REG = b'\x01\x0c            \x02\x01x\x03\x02\x0b\x07\x10\n\x00\x011\x01 \x01\x00\x01\x00\x00"\x04\x01\x01\x01\x00#\x04\x00\x00\xff\x00%\x04\x00\x00\x01\x01 \x01\x01!\x016\x0c\x01\x00\n\x01\x00\x0b\x01\x00\xf0\x02\x00\x04\xf0\x02\x01\x00\xf0\x02\x02\x04\xf0\x02\x03\x04\xf0\x02\x042\xf0\x02\x05\x00\xf0\x02\x06\x00\x04\x01\x00\x11\x05\x7f\x7f\x7f\x7fd\x12\x05@@@@@\x13\x05\x00\x00\x00\x00\x00\x14\x05\x00\x00\x00\x00\x00\x15\x05\x1e$\x07((\x16\x05\x00\x00\x00\x00\x00\x17\x05\x00\x00\x00\x00\x00\x1a\x05\x01\x00\x00\x00\x00\x18\x05\x02\x02\x02\x02\x02<\x01A4\x04\x00\x00\x00\x00=\x01\x00^\x03\x17\x10\x00\x0e\x01\x00\r\x01\x00\x0f\x02\xff\xff\x81\x01\x00\t\x01\x00\x83\x01\x02\x84\x01d@\x01s\x85\x01\x00\x86\x01\x00\x87\x01\x00\xff\x00'




# Define the "atom" identifiers. For more values see "Documentation of Casio formats/Registration format.txt"
#
class Atom:
  Volumes = 0x11
  Rhythm_Number = 0x3
  Delay = 0x5E
  Reverb_Send = 0x15
  Delay_Send = 0x17
  
class DelayType:
  LongPan1 = 0x11
  

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

def change_reverb_and_delay_send(original, reverb_sends, delay_sends):
  i = 0
  b = bytearray(original)
  while i < len(b):
    
    atom_type, atom_len = struct.unpack_from('<2B', original, i)
    if atom_type == Atom.Reverb_Send:
      if len(reverb_sends) > atom_len:
        raise Exception("Too many reverb send values")
      for j, x in enumerate(reverb_sends):
        b[i+2+j] = x
    elif atom_type == Atom.Delay_Send:
      if len(delay_sends) > atom_len:
        raise Exception("Too many delay send values")
      for j, x in enumerate(delay_sends):
        b[i+2+j] = x
        
        
    i += 2 + atom_len
  return bytes(b)



def change_rhythm(original, new_rhythm):
  # original: a registration string to change
  # volumes: an array of up to 4 values to write into the 0x11 atom.
  
  i = 0
  while i < len(original):
    
    atom_type, atom_len = struct.unpack_from('<2B', original, i)
    if atom_type == Atom.Rhythm_Number:
      if 3 > atom_len:
        raise Exception("Too many rhythm values")
      b = bytearray(original)
      struct.pack_into('<H', b, i+2, new_rhythm)
      return bytes(b)
    i += 2 + atom_len
  raise Exception("Didn't find rhythm atom")



def change_delay_type(original, new_delay):
  # original: a registration string to change
  # new_delay: a value to write into the 0x5E atom.
  
  i = 0
  while i < len(original):
    
    atom_type, atom_len = struct.unpack_from('<2B', original, i)
    if atom_type == Atom.Delay:
      b = bytearray(original)
      if atom_len >= 3:
        struct.pack_into('<B', b, i+2+2, new_delay)
      elif atom_len == 2:
        # Need to insert in the middle
        before = b[0:i+2+2]
        after = b[i+2+2:]
        b = before + struct.pack('<B', new_delay) + after
        
        # Change length
        b[i+1] += 1
        i += 1
        
      else:
        raise Exception("Wrong length of 0x5E atom")
      return bytes(b)
    i += 2 + atom_len
  raise Exception("Didn't find delay type atom")



# Parses a binary string as read from a .RBK file into an array of REGH units.
# Ignores the keyboard_name variable, any is accepted.
def parse_rbk_file(bin_str, UNUSED__keyboard_name="CT-X700"):
  
  i = 16
  
  if bin_str[i:i+4] != b'RBKH':
    raise Exception("Incorrect format. Expected RBKH")
  
  i += 8
  
  
  regs = []
  while i < len(bin_str):
  
    if bin_str[i:i+4] != b'REGH':
      raise Exception("Incorrect format. Expected REGH")
    i += 8
    crc , length = struct.unpack_from('<2I', bin_str, i)
    i += 8
    reg = bin_str[i:i+length]
    
    if binascii.crc32(reg) != crc:
      raise Exception(f"CRC mismatch at offset {i-4}")
      
    regs.append(reg)
    i += length
    
    if bin_str[i:i+4] != b'EODA':
      raise Exception("Incorrect format. Expected EODA")
      
    i += 4

  return regs




# Make an array of REGH units into a binary string that can be written to an
# .RBK file
def make_rbk_file(regs, keyboard_name="CT-X700"):
  
  fmt = REGISTRATION_FORMATS[keyboard_name]
  
  if len(regs) > fmt['bank_size']:
    raise Exception(f"Need at most {fmt['bank_size']} registrations to make an .RBK file. Got {len(regs)}")
  else:
    # Too few registrations. Pad it by copying the first one
    while len(regs) < fmt['bank_size']:
      regs.append(regs[0])
    
  b = keyboard_name.encode('ascii').ljust(16, b'\x00')
  b += b'RBKH'
  b += struct.pack('<I', fmt['file_version'])
  
  for reg in regs:
    
    b += b'REGH'
    b += struct.pack('<3I', fmt['file_version'], binascii.crc32(reg), len(reg))
    b += reg
    b += b'EODA'
    
  return b



if __name__=="__main__":
  
  # Use the first registration from "Delay2" as our starting point
  with open("cdp-reg/Delay2.RBK", "rb") as f1:
    basic_reg = parse_rbk_file(f1.read())[0]
  
  
  # Change the reverb and delay send values for U1 part
  r = [change_reverb_and_delay_send(basic_reg, [0],   [0]  ),
       change_reverb_and_delay_send(basic_reg, [127], [0]  ),
       change_reverb_and_delay_send(basic_reg, [0],   [127]),
       change_reverb_and_delay_send(basic_reg, [127], [127])]


  # Save in CT-x700 format
  with open("002.RBK", "wb") as f1:
    f1.write(make_rbk_file(r))

  # Save the same thing in CT-X3000 format
  with open("002-X3000.RBK", "wb") as f1:
    f1.write(make_rbk_file(r, "CT-X3000"))
    
    
  # Now change reverb and delay send, and also the delay type
  r = [change_delay_type(change_reverb_and_delay_send(basic_reg, [0],   [0]  ),  DelayType.LongPan1),
       change_delay_type(change_reverb_and_delay_send(basic_reg, [127], [0]  ),  DelayType.LongPan1),
       change_delay_type(change_reverb_and_delay_send(basic_reg, [0],   [127]),  DelayType.LongPan1),
       change_delay_type(change_reverb_and_delay_send(basic_reg, [127], [127]),  DelayType.LongPan1)]
  
  
  # Save in CT-x700 format
  with open("003.RBK", "wb") as f1:
    f1.write(make_rbk_file(r))

  # Save the same thing in CT-X3000 format
  with open("003-X3000.RBK", "wb") as f1:
    f1.write(make_rbk_file(r, "CT-X3000"))
