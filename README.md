# Corelle

No-nonsense plate rotation models

## Plate rotation models

http://www.serg.unicam.it/Models.html

Finite rotation of an angle about an axis

# General notes

Each model should include:

- Spin axis plate ID
- Mantle reference frame plate ID

Sometimes these are the same, and 0 is commonly used as the spin axis.
This is the best-approximation fixed frame.

The Eglington model uses 0 as the mantle reference frame and 800 as spin axis.
Other models, e.g. Scotese, use 0 as the spin axis.

## Rotation file

http://www.earthbyte.org/Resources/GPlates_tutorials/All_Tutorials/GPlates_Rotations1_Tutorial.html

### Columns

`plate id`, `time`, rotation pole `lat`, `lon`, `angle`, `fixed plate id`,
`data` (plate name, conjugate plate name, reference information).

### Process

Implement rotation tree to get an array of quaternions to be applied

Convert *Euler pole* representation to unit rotation quaternions.


