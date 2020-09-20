#! /bin/usr/python3

##
#
# A library of functions for communicating with a CT-X3000 keyboard over
# the MIDI interface. Linux only. Assumes that there is only one MIDI
# connection, i.e. the device will be located at "/dev/midi1".
#
# Casio keyboards other than CT-X3000 may also work with some of the
# functions, but none have been tested.
#
#
## Dependencies:
#
# Needs crcmod. Install using:
#
#     pip3 install crcmod
#
#
## Functions:
#
#   upload_ac7(dest_num, data)
#   ==========================
#
# Uploads an AC7 rhythm to the keyboard. Parameters:
#
#   dest_num:  Number of the destination. Must lie in the user area, i.e.
#               values 294-343 inclusive.
#   data:      Byte array to write to the destination. It is in "HBR"
#               format, which is identical to the format of an .AC7 file
#               as saved by the keyboard. It should be possible to just
#               read an .AC7 file and upload it with no modification.
#
# Example:
#
#    with open("MyRhythm.AC7", "rb") as f:
#      x = f.read()
#    upload_ac7(294, x)
#
#
#   download_ac7(src_num)
#   =====================
#
# Downloads an AC7 rhythm from the keyboard. Parameter:
#
#   src_num:   Number of the source. Must lie in the user area, i.e.
#               values 294-343 inclusive.
#
#       Returns:
#
#   Byte array in "HBR" format. That is, it is identical to the format
#     of an .AC7 file as saved by the keyboard. It should be possible to
#     write to an .AC7 file which can be loaded into a keyboard by USB.
#
# Example:
#
#    with open("MyRhythm.AC7", "wb") as f:
#      f.write(download_ac7(294))
#

import sys

from internal.sysex_comms_internal import download_ac7_internal
from internal.sysex_comms_internal import upload_ac7_internal


def upload_ac7(dest_num, data):

  if dest_num >= 294 and dest_num <= 343:
    # Uploading to user memory area
    upload_ac7_internal(dest_num - 294, data)
  else:
    # Cannot do bulk uploads to preset locations
    print("Wrong destination number: cannot do bulk uploads to preset location")
    raise Exception


def download_ac7(src_num):

  if src_num >= 294 and src_num <= 343:
    # Download from user memory
    return download_ac7_internal(src_num - 294)
  else:
    # Cannot do bulk download from preset locations
    print("Wrong source number: Cannot do bulk download from preset location")
    return -1


if __name__=="__main__":
  pass

