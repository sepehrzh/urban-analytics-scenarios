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
POI_BBOX    = [-0.220678,51.498466,-0.074337,51.528699] # Oxford Street, London

# Centrality analysis parameters
DISTANCES   = [400, 800, 1600, 2000, 5000, 10000]  # in meters

# Angular-continuity tracing (network_tracing.py) — see HANDOFF-02.md for
# rationale and open sensitivity-analysis item
NODE_DECIMALS = 3               # coordinate rounding tolerance (mm-scale at EPSG:32630)
CORRIDOR_WIDTH = 40              # generous sanity-check width for Oxford St core trace
CORE_DEFLECTION_THRESHOLD = 20   # per-hop, defining Oxford Street itself
ARTERY_DEFLECTION_THRESHOLD = 40 # per-hop, general artery tracing (was 30 — confirm intentional)
CUMULATIVE_DEFLECTION_CAP = 45   # total drift from entry bearing, artery tracing