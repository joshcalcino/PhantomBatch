import os
import logging as log
import subprocess
from phantombatch import jobscripthandler, dirhandler

try:
    splash_dir = os.environ('SPLASH_DIR')
except KeyError:
    log.warning('SPLASH_DIR environment variable not set!')


def make_splash_jobscript(sbconf):
    return NotImplementedError


def make_movie_directories(pconf, sbconf, run_dir):
    dirhandler.create_dirs(pconf, sbconf, run_dir, movies=True)
    return NotImplementedError
