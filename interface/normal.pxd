# For typing definitions
from vy.editor cimport _Editor

# For module namespace
from vy.keys cimport _escape
from vy.interface.helpers cimport one_inside_dict_starts_with

# Module content definition
cpdef loop(_Editor editor)
