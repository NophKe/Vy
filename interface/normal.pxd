#from vy.interface.helpers cimport one_inside_dict_starts_with, resolver
from vy.console cimport stdin_no_echo
from vy.keys cimport _escape
from vy.editor cimport Editor

cdef loop(Editor self)
