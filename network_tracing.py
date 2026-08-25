"""Angular-continuity utilities for topological street tracing.

Used to define Oxford Street and its connecting arteries via axial
continuity (bearing-based hop-to-hop and cumulative deflection), rather
than proximity buffering.
"""
import numpy as np
from collections import defaultdict


def bearing_at_endpoint(geom, which='start', n_vertices=2):
    """Bearing (radians) of the line's direction leaving the given endpoint,
    using the terminal n_vertices to handle curved LineStrings robustly."""
    coords = list(geom.coords)
    if which == 'start':
        p0, p1 = coords[0], coords[min(n_vertices - 1, len(coords) - 1)]
    else:
        p0, p1 = coords[-1], coords[max(0, len(coords) - n_vertices)]
    return np.arctan2(p1[1] - p0[1], p1[0] - p0[0])


def deflection_deg(b1, b2):
    """Absolute angular difference between two bearings (radians in, degrees out)."""
    d = np.degrees(abs(b1 - b2)) % 360
    return 360 - d if d > 180 else d


def opposite_end(which):
    return 'end' if which == 'start' else 'start'


def build_node_index(gdf, node_decimals):
    """Map rounded endpoint coordinates -> list of (segment index, which end)."""
    node_index = defaultdict(list)
    for idx, geom in gdf.geometry.items():
        coords = list(geom.coords)
        node_index[tuple(np.round(coords[0], node_decimals))].append((idx, 'start'))
        node_index[tuple(np.round(coords[-1], node_decimals))].append((idx, 'end'))
    return node_index