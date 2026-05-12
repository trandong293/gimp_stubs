#!/usr/bin/env sh

# callbacks missing
#Gegl TileSourceCommand
#Gegl LookupFunction
#Gimp ProgressVtableStartFunc
#Gimp ProgressVtableEndFunc
#Gimp ProgressVtableSetTextFunc
#Gimp ProgressVtableSetValueFunc
#Gimp ProgressVtablePulseFunc
#Gimp ProgressVtableGetWindowFunc

# wrong name, from property handler, using its name because pytype is None (get_str_pytype)
#GimpUi GtkIconSize
#GimpUi PangoEllipsizeMode
#GimpUi PangoEllipsizeMode

gi_mods="Gtk Pango" # todo: more?
ruff check --output-format concise *.pyi | while IFS= read -r line; do
  # F821
  read -r module child row <<< $(echo $line | sed -n 's/^\(.*\)\.pyi:\([0-9]*\):[0-9]*: F821.*`\(.*\)`$/\1 \3 \2/p')
  if [ -z $module ]; then
    continue
  fi
  # fix 1
  fix1=0
  for gi_mod in $gi_mods; do
    if [[ $child == $gi_mod* ]];then
      fix1=1
      sed -i "${row}s/$gi_mod/$gi_mod\./" $module.pyi
    fi
  done
  if [[ $fix1 == 1 ]]; then
    continue 
  fi
  # fix 2
  python callbacks_missing.py $module $child >> $module.pyi
done
