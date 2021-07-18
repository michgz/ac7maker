'''
Set User Tone 801 to point to a custom wavetable
'''



import os
import os.path
import struct
import time
import textwrap



import sys

# We're importing from a sibling directory.
sys.path.append('..')
sys.path.append('../internal')


from internal.sysex_comms_internal import upload_ac7_internal, download_ac7_internal


def Initial_Setup():
  '''Sets User Tone 801 and the custom Category 5 slot to point to the custom
  Category 12 slot. This only needs to be called once -- it's even maintained
  across power-off!
  '''
  
  TARGET_USER_TONE = 801
  
  # Use CALIBRATION SINE as a basis.
  with open(os.path.join("..", "calibration tones", "CALSINE.TON"), "rb") as f1:
    u = bytearray(f1.read()[0x20:-4])
    

  u[0x86] = 64   # set velocity sense to 0. That helps in certain cases...
  u[0x82:0x84] = struct.pack("<H", 900)  # 900 is the custom Category 5 slot
  u[0x10A:0x10C] = struct.pack("<H", 0)  # second pointer is empty.

  upload_ac7_internal(TARGET_USER_TONE-801, u, memory=1, category=3)
  
  # Now construct a bare-bones Category 5 parameter set, pointing at the custom
  # slot
  
  v = b''
  for i in range(8):
    if i == 0:
      x = 1500    # 1500 is the custom Category 12 slot
    else:
      x = 0    # all but the first pointer is empty
    v += struct.pack("<HBBBB", x, 0, 127, 0, 127)
  # Now the stuff at the end. Don't know what any of this stuff is.
  v += b'\x40\x40\x40\x80\x4A\x40\x40\x40'
  v += b'\x40\x80\x40\x40\x40\x40\x80\x40'
  v += b'\x40\x00\x80\x02\x00\x00'
  
  upload_ac7_internal(0, v, memory=1, category=5)



def Set_Wavetable(CAT12_NUM):
  '''Reads the Category 12 wavetable, adjusts it, and writes it to the custom
  slot
  '''
  
  
  # First, read the starting set. Try to find a cached copy if available.
  if os.path.isfile(os.path.join("..", "CAT12_DATA", "{0}.bin".format(CAT12_NUM))):
    with open(os.path.join("..", "CAT12_DATA", "{0}.bin".format(CAT12_NUM)), "rb") as f2:
      x = f2.read()
  else:
    x = download_ac7_internal(CAT12_NUM, memory=0, category=12)
    if len(x) == 0x294:
      if not os.path.isdir(os.path.join("..", "CAT12_DATA")):
        os.mkdir(os.path.join("..", "CAT12_DATA"))
      with open(os.path.join("..", "CAT12_DATA", "{0}.bin".format(CAT12_NUM)), "wb") as f3:
        f3.write(x)

  # Now construct a simplified version
  y = b'\x00\x00\x40\x00\x00\x20\x00\x02\x00\x20\x00\x02\x00\x20\x00\x02'
  
  # Find the first layer which covers middle C
  j = -1
  MIDDLE_C = 60
  for i in range(16):
    cc = struct.unpack_from("BB", x, 0x10+4+10*i)
    if MIDDLE_C >= cc[0] and MIDDLE_C <= cc[1]:
      j = i
      break
  if j < 0:
    j = 0  # failed to find. Just use the first one
    
  
  for i in range(16):

    if i == 0:
      z = struct.unpack_from("<H", x, 0x10+j*10)[0]
    else:
      z = 0
    y += struct.pack("<HBBBBBBBB", z, 0, 0, 0, 127, 128, 128, 64, 128)


  
  y += x[0xB0:0x27C]
  y += struct.pack("24B", 127, 2, 128, 2, 2, 127, 2, 2, 127, 2, 127, 2, 127, 2, 2, 2, 127, 2, 2, 127, 64, 0, 127, 2)


  upload_ac7_internal(0, y, memory=1, category=12)




if __name__ == "__main__":
  
  # Check if the initial setup needs to be done by using a "marker" file. Delete
  # it to force a re-initialisation
  
  if not os.path.isfile("melody_wavetable.py.lock.txt"):

    Initial_Setup()

    with open("melody_wavetable.py.lock.txt", "w") as f4:
      f4.write("INITIALISED\n")
  
  Set_Wavetable(1419)

