# examples directory
Example inputs for the ac7maker script

## Example 1
Drums and acoustic guitar in the style of Nick & Roy Lowe. It is an examples of how to use the
"chord_sync" field with versatile instruments to turn off transposition. Strum and
body sounds are not transposed, while normal note sounds are transposed according
to the played chord.

## Example 2
Drums and guitar in the style of King Missile. It shows how arbitrary DSP chains
can be applied to preset sounds within the rhythm definition itself. In this example,
a Delay effect is followed by Drive to create a guitar echo that fades from heavy distortion
to clean -- an effect that can't be achieved with any of the preset DSP chains

## Example 3
A non-musical example for unit-testing a few features. Var1 tests pitch bend with
a french horn bending down a 4th followed by up a 5th. Var2 is pitch bend being
applied to a drum kit creating a melodic "roto-tom" sound. Var3 is for proving the
handling of 12/8 time
