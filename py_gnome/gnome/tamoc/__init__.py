"""
code for interfacing with TAMOC:

https://github.com/socolofs/tamoc

For now, this imports everythign from tamoc.py in this package

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import *
from .tamoc_spill import *
