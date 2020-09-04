#! /bin/usr/python3


# Import some standard modules
import json
import struct
import operator

# Import one non-standard module. Can be installed by:
#
#   pip3 install mido
#
import mido


# Default instrument allocations. Ordered by part number
instruments = [
  {'patch': 0,  'bank': 120},
  {'patch': 0,  'bank': 120},
  {'patch': 33, 'bank': 0},
  {'patch': 0,  'bank': 0},
  {'patch': 25, 'bank': 0},
  {'patch': 27, 'bank': 0},
  {'patch': 49, 'bank': 0},
  {'patch': 61, 'bank': 0}
]

# Set up a mixer table element for given part number. The file format
# gives us the capability to change all settings for each element also,
# but here just give the elements the same values.
def ac7make_mixer_element(pt, b):
  g = b''
  pt_patch = b['rhythm']['parts'][pt].get('patch', -1)
  pt_bank = b['rhythm']['parts'][pt].get('bank', -1)
  if pt_patch < 0 or pt_bank < 0:
    # Not specified correctly - use defaults for that part
    pt_patch = instruments[pt]['patch']
    pt_bank = instruments[pt]['bank']
  g = g + struct.pack('B', pt_patch)
  g = g + struct.pack('B', pt_bank)
  g = g + struct.pack('B', b['rhythm']['parts'][pt].get('volume', 100))  # volume
  g = g + struct.pack('B', 64 + b['rhythm']['parts'][pt].get('pan', 0))   # pan
  g = g + struct.pack('B', b['rhythm']['parts'][pt].get('reverb_send', 40))   # reverb send
  g = g + struct.pack('B', b['rhythm']['parts'][pt].get('chorus_send', 0))   # chorus send
  return(g)

def ac7make_mixer(b, addr):
  g1 = b'MIXR'
  g2 = b''
  g3 = b''
  number_of_parts = 96
  addr = addr + 10 + 4*number_of_parts
  for el in range(12):
    for pt in range(8):
      g4 = ac7make_mixer_element(pt, b)
      g3 = g3 + g4
      g2 = g2 + struct.pack('<I', addr)
      addr = addr + len(g4)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


# MIDI event to Casio event converter
def ac7make_mid2casio(msg):
  if msg.type == "note_on":
    vel = msg.velocity
    if vel == 0:  # velocity of 0 not allowed in Casio
      vel = 1
    return struct.pack('3B', round(24*msg.time), msg.note, vel)
  elif msg.type == 'note_off':
    return struct.pack('3B', round(24*msg.time), msg.note, 0)
  else:
    return b''

# Determine if the element should be omitted in total from the rhythm. Typically
# this is done for elements 7, 8, 9 & 10 and is possibly for compatibility
# with keyboards with only 2 variations.
def ac7make_element_has_drum(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)

def ac7make_element_has_other(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)



def ac7make_drum_element(pt, el, b):
  for track in b["rhythm"]["tracks"]:
    if track["part"]==1 or track["part"]==2:
      if track["part"]==(pt+1) and track["element"]==(el+1):
        #midi_file = mido.MidiFile(track["source_file"])
        g = b'\x00\xe5\x00'  # "Start user data" indicator
        #for msg in midi_file:
        #  if msg.type == 'note_on' or msg.type == 'note_off':
        #    if msg.channel == track["source_channel"]:
        #      g += ac7make_mid2casio(msg)
        g += b'\x00\x24\x4b\x0b\x24\x00\x57\x28\x3c\x0f\x28\x00\x53\x24\x48\x15\x24\x00\x44\x28\x40\x0c\x28\x00\x57\xfc\x00'
        #return  g + b'\x00\xfc\x00'
        return g
        
  #if el == 6 or el == 11:
  #  # For some reason, these tracks take an extra E5
  #  return b'\x00\xe5\x00\x80\xff\x04\x00\xfc\x00'
  
  # If we get down to here, no matching input has been found. Just return
  # an empty track that has only two elements:
  # 80 FF 04   -- wait whole length
  # 00 FC 00   -- end of track  
  return b'\x80\xff\x04\x00\xfc\x00'

def ac7make_drum(b, addr):
  g1 = b'DRUM'
  g2 = b''
  g3 = b''
  
  number_of_parts = 0
  for el in range(12):
    if ac7make_element_has_drum(b, el):
      number_of_parts += 2
  addr = addr + 10 + 4*number_of_parts
  for el in range(12):
    if ac7make_element_has_drum(b, el):
      for pt in range(2):
        g4 = ac7make_drum_element(pt, el, b)
        g3 = g3 + g4
        g2 = g2 + struct.pack('<I', addr)
        addr = addr + len(g4)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


def ac7make_other_element(pt, el, b):
  # A default track that has three elements:
  # 02 70 00   -- something to do with break points, split tables, etc.
  # 80 FF 04   -- wait whole length
  # 00 FC 00   -- end of track
  if (el == 0 or el == 5 or el == 6 or el == 11):
    # An intro or outro element
    if (pt == 0):
      # Bass
      g1 = b'\x0b\x40\x00'
    else:
      # Chords
      g1 = b'\x0b\x70\x00'
    #if el == 6 or el == 11:
    #  g1 += b'\x00\xe5\x00'
  else:
    # An ordinary variation/fill
    if (pt == 0):
      # Bass
      g1 = b'\x00\x40\x00'
    else:
      # Chords
      g1 = b'\x02\x70\x00'
    if pt == 2 and el == 1:
      return b'\x02\x70\x00\x00\xe5\x00\x00\x24\x42\x00\x2b\x53\x00\x30\x47\x00\x34\x3e\x00\x37\x49\x00\x3c\x3a\x00\x34\x3e\x00\x30\x47\x00\x2b\x53\x8a\x37\x00\x01\x2b\x00\x00\x30\x00\x00\x3c\x00\x00\x30\x00\x00\x2b\x00\x02\x34\x00\x00\x34\x00\x01\x24\x00\x2f\x2b\x4f\x01\x37\x44\x01\x30\x4a\x00\x24\x47\x00\x3c\x3d\x00\x34\x3f\x1f\x30\x00\x01\x2b\x00\x01\x37\x00\x01\x24\x00\x00\x3c\x00\x02\x34\x00\x35\x24\x36\x00\x2b\x4c\x01\x37\x44\x00\x34\x3f\x00\x3c\x35\x00\x30\x50\x38\x2b\x00\x00\x37\x00\x00\x30\x00\x01\x34\x00\x01\x3c\x00\x01\x24\x00\x2c\xfc\x00'
  return g1 + b'\x80\xff\x04\x00\xfc\x00'

def ac7make_other(b, addr):
  g1 = b'OTHR'
  g2 = b''
  g3 = b''
  
  number_of_parts = 0
  for el in range(12):
    if ac7make_element_has_other(b, el):
      number_of_parts += 6
  addr = addr + 10 + 4*number_of_parts
  for el in range(12):
    if ac7make_element_has_other(b, el):
      for pt in range(6):
        g4 = ac7make_other_element(pt, el, b)
        g3 = g3 + g4
        g2 = g2 + struct.pack('<I', addr)
        addr = addr + len(g4)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)



drum_part_number = 0
other_part_number = 0
overall_part_number = 0

def ac7make_element_atom(in_val, in_str):
  return struct.pack('B', in_val) + struct.pack('B', len(in_str)) + in_str

def ac7make_element_block(b, el):
  g1 = b'ELMT'
  g2 = b''
  g2 = g2 + ac7make_element_atom(1, struct.pack('B', 34)) # ??
  measure_count = 1
  if el == 6 or el == 11:
    measure_count = 4
  g2 = g2 + ac7make_element_atom(6, struct.pack('B', measure_count))   # Number of measures
  
  global drum_part_number
  global other_part_number
  global overall_part_number
  
  g32 = b''
  
  drum_part_count = 0
  if ac7make_element_has_drum(b, el):
    drum_part_count = 2
  
  other_part_count = 0
  if ac7make_element_has_other(b, el):
    other_part_count = 6

  
  g2 += ac7make_element_atom(7, struct.pack('B', drum_part_count + other_part_count))   # Number of parts
  
  for i in range(drum_part_count):
    g32 += struct.pack('B', drum_part_number)
    g32 += b'\x80'  # Flags byte
    drum_part_number += 1

  for i in range(other_part_count):
    g32 += struct.pack('B', other_part_number)
    g32 += b'\x80'  # Flags byte
    other_part_number += 1
  
  g33 = b''
  
  for i in range(8):
    if i < (drum_part_count + other_part_count):
      g33 += struct.pack('B', overall_part_number)
      g33 += b'\x80'  # Flags byte
    # This one increments even if the parts aren't included
    overall_part_number += 1


  g34 = b''
  if (drum_part_count + other_part_count) > 0:
    g34 = b'\x0f'  # 0x0F = negative 1
    for i in range(drum_part_count + other_part_count - 1):
      g34 += struct.pack('B', i)
    
  g48 = b''
  for i in range(8):  # This one always has 8 elements
    g48 += struct.pack('B',  b['rhythm']['parts'][i].get('delay_send', 0))   # delay send


  g2 += ac7make_element_atom(32, g32) # Data offsets
  g2 += ac7make_element_atom(33, g33) # Mixer offsets
  g2 += ac7make_element_atom(34, g34) #??
  g2 += ac7make_element_atom(48, g48) # Delay send values

  g2 = g2 + ac7make_element_atom(253, b'') #??
  g2 = g2 + ac7make_element_atom(254, b'') #??
  g2 = g2 + ac7make_element_atom(255, b'') # End
  
  g1 = g1 + struct.pack('<H', 6 + len(g2)) 
  return g1 + g2



def ac7make_time_signature(s):
  # Takes a string as input. The following is a complete list of possible
  # inputs:
  #   2/4 3/4 4/4 5/4 6/4 7/4 8/4
  #   2/8 3/8 4/8 5/8 6/8 7/8 8/8 9/8 10/8 11/8 12/8 13/8 14/8 15/8 16/8
  # 
  # TODO: could make a bit more robust
  num = int(s.split('/')[0])
  den = int(s.split('/')[1])
  if num < 2 or num > 16:
    raise Exception
  x = 0x00
  if den == 4:
    if num > 8:
      raise Exception
    x = 0x02
  elif den == 8:
    x = 0x03
  else:
    # Only allowed denominators are 4 or 8
    raise Exception
  return x + 8*num


def ac7make_element(b, addr):
  number_of_parts = 12
  addr = addr + 7 + 4*number_of_parts
  
  # Magic number for "elements"
  g0 = struct.pack('<I', 0x07ffffff)
  
  g2 = b''
  g2 = g2 + b'\x00\x0c'   # Name length (12 bytes)
  # Ensure the name is exactly 8 bytes long, with the final character
  # being a space.
  g2 += b['rhythm'].get('name', "No Name")[:7].ljust(8, ' ').encode('ascii')
  # Now pad with 4 more bytes to get to 12 bytes. We can probably have
  # longer names, but they won't be displayed on the CT-X anyway.
  #
  # The first byte here must be 0x00 (null terminator), others don't seem to matter.
  g2 += b'\x00\x01\x00\x00'
  g2 = g2 + ac7make_element_atom(1, struct.pack('B', ac7make_time_signature(b['rhythm'].get('time_signature', '4/4')))) # Time signature.
  g2 = g2 + ac7make_element_atom(2, struct.pack('B', 120)) # Tempo bpm
  g2 = g2 + ac7make_element_atom(9, struct.pack('B', b['rhythm'].get('volume', 127)))   # Overall volume
  g2 = g2 + ac7make_element_atom(64, struct.pack('B', 23)) # Reverb type. TODO: how does this relate to CT-X numbering?
  g2 = g2 + ac7make_element_atom(65, struct.pack('B', 2)) # Chorus type. TODO: how does this relate to CT-X numbering?
  g2 = g2 + ac7make_element_atom(66, struct.pack('B', 4)) # Delay type. TODO: how does this relate to CT-X numbering?
  
  # The following stuff is optional. I don't know what it is...
  if True:
    g2 = g2 + ac7make_element_atom(17, b'\x06\x01') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x07\x12') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x08\x13') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x09\x22') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x0A\x23') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x0B\x31') # ??

  g2 = g2 + ac7make_element_atom(255, b'') # End

  addr = addr + len(g2)

  # Set the part counters to 0, as they need to be retained throughout
  # the loop
  global drum_part_number
  global other_part_number
  global overall_part_number
  
  drum_part_number = 0
  other_part_number = 0
  overall_part_number = 0

  g1 = b''
  g3 = b''
  for el in range(12):
    g4 = ac7make_element_block(b, el)
    g3 = g3 + g4
    g1 = g1 + struct.pack('<I', addr)
    addr = addr + len(g4)
  g0 = g0 + struct.pack('<H', 7 + len(g1) + len(g2) + len(g3))
  g0 = g0 + struct.pack('B', number_of_parts)
  return g0 + g1 + g2 + g3


def ac7maker(f, b):
  
  # Size of the header. 'AC07' plus start address of each block (4 bytes),
  # plus end address (4 bytes)
  addr = 0x1C
  
  g1 = b''
  
  g1 += struct.pack('<I', addr)
  g5 = ac7make_element(b, 0)
  addr += len(g5)
  
  g1 += struct.pack('<I', addr)

  g2 = ac7make_mixer(b, addr)

  addr += len(g2)

  g1 += struct.pack('<I', addr)
  g3 = ac7make_drum(b, addr)
  addr += len(g3)

  g1 += struct.pack('<I', addr)
  g4 = ac7make_other(b, addr)
  addr += len(g4)

  # End-of-list indicator
  g1 += struct.pack('<I', 0xffffffff)

  g1 = b'AC07' + struct.pack('<I', addr) + g1

  f.write(g1 + g5 + g2 + g3 + g4)
  
  
# Following https://github.com/shimpe/ac7parser/Ac7CasioEventAnalyzer.py
# Note that '-' as a synonym for flat has been retained, but it leads to
# ambiguity if octave is 1 or -1. Consider removing.

chromatic_scale = [['c', 'b#', 'dbb', 'd--'],  # one row contains all synonyms (i.e. synonym for our purpose)
                   ['c#', 'bx', 'db', 'd-'],
                   ['d', 'cx', 'ebb', 'e--'],
                   ['d#', 'eb', 'e-', 'fbb', 'f--'],
                   ['e', 'dx', 'fb', 'f-'],
                   ['f', 'e#', 'gbb', 'g--'],
                   ['f#', 'ex', 'gb', 'g-'],
                   ['g', 'fx', 'abb', 'a--'],
                   ['g#', 'ab', 'a-'],
                   ['a', 'gx', 'bbb', 'b--'],
                   ['a#', 'bb', 'b-', 'cbb', 'c--'],
                   ['b', 'ax', 'cb', 'c-']]

corner_case_octave_lower = {"b#", "bx"}
corner_case_octave_higher = {"cb", "c-", "cbb", "c--"}


def read_music(f):
  dd = []
  while True:
    s = f.readline()
    if not s:
      break
    h1 = s.split()
    if len(h1) != 4:
      raise Exception
    d = dict()
    vel = int(h1[2])
    if vel == 0:
      # The Casio format doesn't allow 0 velocity (but MIDI does!)
      raise Exception
    d['velocity'] = vel

    u = h1[0].split('.')
    if len(u) == 2:
      d['time'] = 24*(4*(int(u[0]) -1) + int(u[1]) -1)
    elif len(u) == 3:
      d['time'] = 24*(4*(int(u[0]) -1) + int(u[1]) -1) + int(u[2])
    else:
      raise Exception
      
    u = h1[3].split('.')
    if len(u) == 1:
      d['duration'] = 24*int(u[0])
    elif len(u) == 2:
      d['duration'] = 24*int(u[0]) + int(u[1])
    else:
      raise Exception

    if h1[1].endswith("-1"):
      octave = -1
      s = h1[1][0:-2]
    else:
      octave = int(h1[1][-1:])
      s = h1[1][0:-1]
    
    n = 0
    note = -2
    for t in chromatic_scale:
      if s in t:
        note = n
      n = n + 1
    if note == -2:
      # Not found
      raise Exception
    
    if s in corner_case_octave_lower:
      octave += 1
    elif s in corner_case_octave_higher:
      octave -= 1
    d['pitch'] = note + (octave + 1)*12

    # Add the note-on event, making a deep copy
    dd.append(dict(d))
    # Now add the note-off event!
    d['velocity'] = 0
    d['duration'] = 0
    dd.append(d)
  return sorted(dd, key=operator.itemgetter('time'))






#for msg in mido.MidiFile('MLTREC02.MID'):
#  print(msg)









#with open("pt2el3.txt", "r") as f3:
#  c = read_music(f3)
#  print(c)


with open("example.json", "r") as f1:
  b = json.load(f1)
  print(b)
  print(b['target_model'])
  
with open("aa.AC7", "wb") as f2:
  ac7maker(f2, b)
