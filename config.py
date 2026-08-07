"""
Single source of truth for all the right paths, hyper parameters, constants and configurations for the project. 
This should be imported at the top of every notebook:

    import sys; sys.path.insert(0, '..')
    from config import *

All path variables are strings. Update REPO_ROOT if your working directory differs.

Branch: main
Purpose: the pipeline that imports analyses and creates the evidence basis for addressing the potential scenarios for the pedestrianization of Oxford Street.
"""

import os

# ROOT
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# Data directories (shared)
DATA_DIR        = os.path.join(REPO_ROOT, "data")
OUTPUTS_DIR     = os.path.join(REPO_ROOT, "data", "outputs")
RAW_DATA        = os.path.join(REPO_ROOT, "data", "downloads")

# Input files

# Area coordinates: This comes from https://boundingbox.klokantech.com/
BBOX        = [-0.306909,51.446998,-0.009249,51.578401] # Oxford Street, London

# Centrality analysis parameters
DISTANCES   = [400, 800, 1600, 2000, 5000, 10000]  # in meters