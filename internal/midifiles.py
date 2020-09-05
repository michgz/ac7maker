# A library of functions for reading, parsing and writing MIDI files.

import struct


def consume_midi_time(b, pos):
  p = pos
  v = 0
  while True:
    x = b[p]
    p += 1
    v = 0x80*v + (0x7F&x)
    if (x&0x80)==0x00:
      # End
      return (v, p)
  print("Got to end!")

def consume_midi_event(b, pos):
  p = pos
  if b[p] == 0xFF:
    # Meta-event
    n = b[p+2]
    return (b[p+1], p+3+n)
  elif b[p] == 0xF0:
    # System exclusive
    n = b[p+1]
    return (0, p+2+n)
  elif b[p]&0xF0 == 0xB0:
    # Controller
    return (0xB0, p+3)
  elif b[p]&0xF0 == 0xC0:
    # Patch change
    return (0xC0, p+2)
  elif b[p]&0xF0 == 0x80:
    # Note off
    return (0x80, p+3)
  elif b[p]&0xF0 == 0x90:
    # Note on
    return (0x90, p+3)
    
  return (0,p)
    
  
def process_track(b):
    
    pos = 0
    while pos < len(b):
    
      (c, pos) = consume_midi_time(b, pos)
      (d, pos) = consume_midi_event(b, pos)
      print("{0:02X} {1:02X}".format(c,d))
    print("-- end of track --")


  
  


def midifile_read(b):
  pos = 0
  if b[pos+0:pos+4] != b'MThd':
    # Bad input
    return b''
  x = struct.unpack('>I', b[pos+4:pos+8])[0]  # Length of header
  num_trks = struct.unpack('>H', b[pos+10:pos+12])[0]  # Number of tracks in file
  
  pos += 8 + x
  
  for t in range(num_trks):
    if b[pos+0:pos+4] != b'MTrk':
      print("Expected 'MTrk' at position {0}, got '{1}'".format(pos, b[pos+0:pos+4]))
      # Bad input
      return b''

    x = struct.unpack('>I', b[pos+4:pos+8])[0]  # Length of track
    trk = process_track(b[pos+8:pos+8+x])
    #print(x)
    
    pos += 8 + x
    





if __name__=="__main__":
  with open("MLTREC10.MID", "rb") as f1:
    b = f1.read()
  midifile_read(b)
