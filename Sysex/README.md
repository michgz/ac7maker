## MASTERVOL.MID

A standard MIDI file to set the CT-X keyboard to 40% volume (irrespectively of the setting
of the volume knob). To try it out do the following sequence:

* Set the volume knob to minimum
* Play a note on the keyboard. You should hear nothing
* Play/send this .MID file to the keyboard USB MIDI port
* Play a note on the keyboard. You should now hear something, even though the volume knob is still at minimum

A file like this is often useful for making recordings with repeatable levels (place the file at the 00:00:00.0 time
of your DAW project).

A hex dump of the file looks like this:

>  4d 54 68 64 00 00 00 06  00 01 00 01 01 e0 4d 54

>  72 6b 00 00 00 3c 00 f0  19 44 19 01 7f 01 02 03

>  00 00 00 00 00 00 00 00  00 00 03 00 00 00 00 00

>  **33** f7 02 f0 19 44 19 01  7f 01 02 03 00 00 00 00

>  00 00 00 00 00 00 04 00  00 00 00 00 40 f7 02 ff

>  2f 00

The bolded value is the volume that will be set. 33 hex is 40% of full volume, and works
fairly well. Be careful setting larger values, it can be very loud!!
