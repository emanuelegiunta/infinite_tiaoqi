import sys

# Add the root of the directory in the path (all errors modules need to import
#  tiaoqi submodules
sys.path.insert(0, "../.")

# Submodules Import
from test.test_pieces import *