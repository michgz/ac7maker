# Key follow
Relates to tone parameters 47 & 48 (see ..\Tone definition format.txt). They allow
a gain to be applied tone that varies with the pitch of the note being
played. It achieves a similar result to the "Key Follow" function of some earlier
Casio keyboards.

The plots show the profile for each possible value of the parameters, from 0 to 126.
A value of 127 causes a software crash on the keyboard.

Parameters 47 & 48 are identical to each other and independent, such that the effects of them are stacked
(or, added when measured in dB terms). y-axis values on the plots are in dB relative to the default
setting which is 2. The measurement was done starting with tone in Bank MSB 63 Patch 82
("CALIBRATION 1KHZ") and changing parameter 48, and plotting was done using matplotlib.
