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
  evt = b[p]
  if evt == 0xFF:
    # Meta-event
    n = b[p+2]
    if b[p+1]==0x51 and n==3:
      # Tempo
      x = 0x10000*b[p+3] + 0x100*b[p+4] + b[p+5]
      tempo = round(60000000.0 / float(x))
      # Note this is tempo per quarter note. Depending on the time signature,
      # may need to adjust to eighth notes.
      e = {'event':'tempo_change', 'absolute_time':0, 'value':tempo}
      return (e, p+3+n)
    elif b[p+1]==0x2F and n==0:
      e = {'event':'track_end', 'absolute_time':0}
      return (e, p+3+n)
    else:
      e = {'event':'metadata', 'absolute_time':0, 'data': b''}
    return (e, p+3+n)
  elif evt == 0xF0:
    # System exclusive
    n = b[p+1]
    e = {'event':'sysex', 'absolute_time':0, 'data': b''}
    return (e, p+2+n)
  else:
    if evt&0xF0 == 0xB0:
      # Controller
      e = {'event':'control_change', 'absolute_time':0, 'channel':evt&0x0F, 'controller':b[p+1], 'value':b[p+2]}
      return (e, p+3)
    elif evt&0xF0 == 0xC0:
      # Patch change
      e = {'event':'patch_change', 'absolute_time':0, 'channel':evt&0x0F, 'patch':b[p+1]}
      return (e, p+2)
    elif evt&0xF0 == 0x80:
      # Note off
      e = {'event':'note_off', 'absolute_time':0, 'channel':evt&0x0F, 'note':b[p+1], 'velocity':b[p+2]}
      return (e, p+3)
    elif evt&0xF0 == 0x90:
      # Note on
      e = {'event':'note_on', 'absolute_time':0, 'channel':evt&0x0F, 'note':b[p+1], 'velocity':b[p+2]}
      return (e, p+3)
    elif evt&0xF0 == 0xE0:
      # Pitch bend
      e = {'event':'pitch_bend', 'absolute_time':0, 'channel':evt&0x0F, 'bend':b[p+1]}
      return (e, p+3)
    
  print("Unknown event {0:02X}".format(evt))
  sys.exit(0)

  
def process_track(b):
    
    pos = 0
    total_time = 0
    trk = []
    while pos < len(b):
    
      (c, pos) = consume_midi_time(b, pos)
      (d, pos) = consume_midi_event(b, pos)
      total_time += c
      d['absolute_time'] = total_time / 20.0
      print("{0:02X} {1}".format(c,d['event']))
      trk.append(d)
    print("-- end of track --; end time = {0:X}".format(total_time))
    return trk




def midifile_read(b):
  pos = 0
  if b[pos+0:pos+4] != b'MThd':
    # Bad input
    return b''
  x = struct.unpack('>I', b[pos+4:pos+8])[0]  # Length of header
  num_trks = struct.unpack('>H', b[pos+10:pos+12])[0]  # Number of tracks in file
  division = struct.unpack('>H', b[pos+12:pos+14])[0]  # Number of ticks per quarter note (1 quarter note = 24 MIDI clocks)
  print("Division = {0}".format(division))
  
  trks = []
  
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
    
    trks.append(trk)
    
  return trks
    





if __name__=="__main__":
  with open("MLTREC10.MID", "rb") as f1:
  #with open('Alan Walker - Faded (Original Mix) (midi by Carlo Prato) (www.cprato.com).mid','rb') as f1:
    b = f1.read()
  midifile_read(b)
