# examples directory
Example inputs for the ac7maker script

## Example 1
Drums and acoustic guitar in the style of Roy & Nick Lowe. It is an examples of how to use the
"chord_sync" field. In this example, strum and fret-noise sounds from the guitar have
chord syncing turned off so the same sounds are used for any chord. The string notes
are still, as usual, transposed to match the played chord

Parts defined:
  - part 2: BRUSH SET
  - part 5: VERSATILE STEEL GUITAR
Elements defined:
  - intro, variation 1, variation 2, fill 1 & fill 2.

## Example 2
Drums and heavy guitar in the style of King Missile. It shows how arbitrary DSP chains
can be applied using the "dsp" field. In this example,
a Delay effect is followed by Drive to create a guitar echo that fades from heavy distortion
to clean - an effect that can't be achieved with any of the preset DSP chains

Parts defined:
  - part 2: ROOM SET
  - part 5: STEEL STR. GUITAR 4 with custom DSP chain
Elements defined:
  - variation 1, variation 2, fill 1 & fill 2.

## Example 3
A non-musical example for unit-testing a few features. Var1 tests pitch bend with
a french horn bending down a 4th followed by up a 5th. Var2 is pitch bend being
applied to a drum kit creating a melodic "roto-tom" sound. Var3 is for proving the
handling of 12/8 time
