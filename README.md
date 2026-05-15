Insprired by **pygobject-stubs** and **pgi-docgen**, tailored for the GIMP

## How to use

Install **pygobject-stubs**, copy 4 files **Babl.pyi**, **Gegl.pyi**,
**Gimp.pyi**, and **GimpUi.pyi** into
**.venv/lib/python3.14/site-packages/gi-stubs/repository/**

## Todo

Incorrect import paths
  `import Babl` should be changed to `from gi.repository import Babl`
  ...

Missing field
  `__gtype__` is missing because I omitted all fields that name starts with a
double underscore "__"
