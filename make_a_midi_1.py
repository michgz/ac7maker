#! /bin/usr/python3


# Import some standard modules
import json
import struct
#import operator
import sys



def make_time(t):
  if t<=127:
    return struct.pack('<1B', t)
  else:
    return struct.pack('<2B', 0x80 | (t>>7), t&0x7F)

def make_midi_from_tracks(tt):
  b = b'MThd'
  b += struct.pack('>I', 6)
  b += struct.pack('>H', 1)  # Type of MIDI file. Currently only type 1
  b += struct.pack('>H', len(tt))   # Number of tracks
  b += struct.pack('>H', 0x01E0)    # Ticks per quarter note
  for trk in tt:
    b += b'MTrk' + struct.pack('>I', len(trk)) + trk
  return b


trks = []

trk = b''
trk += make_time(0) + b'\xff\x58\x04\x04\x02\x18\x08'   # Time signature
trk += make_time(0) + b'\xff\x51\x03\x07\xa1\x20'   # Tempo to 120 bpm
trk += make_time(1920) + b'\xff\x2f\x00'  # EOT

trks.append(trk)


trk = b''

trk += make_time(0) + b'\xb0\x07\x7f'    # Volume
trk += make_time(0) + b'\xb0\x0a\x40'    # Pan
trk += make_time(0) + b'\xb0\x00\x0F\x00\xb0\x20\x00\x00\xc0\x60'   # Set patch to EDM SE WHITE

trk += make_time(0) + b'\x90\x48\x4e'  # Note on
trk += make_time(1440) + b'\x80\x48\x7f'  # Note off
trk += make_time(480) + b'\xff\x2f\x00'  # EOT

trks.append(trk)


with open("midi-01.mid", "wb") as f1:
  f1.write(make_midi_from_tracks(trks))

