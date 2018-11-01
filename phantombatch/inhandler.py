import os
import logging as log
from phantombatch import setuphandler


def write_to_in(new_in, ref_in, in_strings, pconf):
    """ Write to the .in files """
    setuphandler.write_to_setup(new_in, ref_in, in_strings, pconf)


