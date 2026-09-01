"""Angular-continuity utilities for topological street tracing.

Used to define Oxford Street and its connecting arteries via axial
continuity (bearing-based hop-to-hop and cumulative deflection), rather
than proximity buffering.

`trace_core`, `find_direct_junctions`, `trace_artery`, and the
`trace_oxford_street_and_arteries` orchestration function were promoted
here from notebook 02's cells so notebook 05 (and any future notebook)
can regenerate the same traced corridor+artery set without duplicating
the logic. Notebook 02 should be updated to call these instead of its
inline versions, so there's a single definition of "what counts as
Oxford Street."
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


def find_seed_segment(street_gdf, reference_geom):
    """Index of the street_gdf segment nearest the reference geometry's centroid,
    plus the distance, so the caller can sanity-check the match."""
    centroid = reference_geom.centroid
    dists = street_gdf.geometry.distance(centroid)
    return dists.idxmin(), dists.min()


def trace_core(street_gdf, node_index, seed_idx, direction_end, corridor_geom,
                deflection_threshold, node_decimals, max_hops=200):
    """Walk from seed_idx in direction_end, staying within corridor_geom and
    under the per-hop deflection_threshold. Returns a list of segment indices."""
    chain = [seed_idx]
    visited = {seed_idx}
    current_idx, current_exit_end = seed_idx, direction_end

    for _ in range(max_hops):
        geom = street_gdf.loc[current_idx, 'geometry']
        coords = list(geom.coords)
        exit_key = tuple(np.round(coords[-1] if current_exit_end == 'end' else coords[0], node_decimals))
        incoming_bearing = bearing_at_endpoint(geom, which=current_exit_end)

        candidates = [(oi, w) for oi, w in node_index[exit_key] if oi != current_idx]
        if not candidates:
            break
        candidates = [(oi, w) for oi, w in candidates
                      if street_gdf.loc[oi, 'geometry'].intersects(corridor_geom)]
        if not candidates:
            break

        scored = sorted(
            ((deflection_deg(incoming_bearing + np.pi, bearing_at_endpoint(street_gdf.loc[oi, 'geometry'], w)), oi, w)
             for oi, w in candidates),
            key=lambda t: t[0]
        )
        best_defl, best_idx, best_which = scored[0]
        if best_defl > deflection_threshold or best_idx in visited:
            break

        chain.append(best_idx)
        visited.add(best_idx)
        current_idx, current_exit_end = best_idx, opposite_end(best_which)

    return chain


def find_direct_junctions(street_gdf, node_index, core_idx, node_decimals):
    """Segments that touch the core segment set at an endpoint but aren't
    themselves part of it -- the seed points for artery tracing."""
    direct_junctions = set()
    for idx in core_idx:
        coords = list(street_gdf.loc[idx, 'geometry'].coords)
        for key in (tuple(np.round(coords[0], node_decimals)),
                    tuple(np.round(coords[-1], node_decimals))):
            for other_idx, _ in node_index[key]:
                if other_idx not in core_idx:
                    direct_junctions.add(other_idx)
    return direct_junctions


def trace_artery(street_gdf, node_index, seed_idx, seed_entry_end,
                  deflection_threshold, cumulative_cap, node_decimals, max_hops=50):
    """Walk outward from a junction segment, capping both per-hop deflection
    and cumulative drift from the entry bearing (guards against small
    hop-to-hop bends compounding into a large net turn onto a parallel street)."""
    artery = [seed_idx]
    visited = {seed_idx}
    current_idx, current_exit_end = seed_idx, opposite_end(seed_entry_end)
    entry_bearing = bearing_at_endpoint(street_gdf.loc[seed_idx, 'geometry'], which=current_exit_end)

    for _ in range(max_hops):
        geom = street_gdf.loc[current_idx, 'geometry']
        coords = list(geom.coords)
        exit_key = tuple(np.round(coords[-1] if current_exit_end == 'end' else coords[0], node_decimals))
        incoming_bearing = bearing_at_endpoint(geom, which=current_exit_end)

        candidates = [(oi, w) for oi, w in node_index[exit_key] if oi != current_idx]
        if not candidates:
            break

        scored = sorted(
            ((deflection_deg(incoming_bearing + np.pi, bearing_at_endpoint(street_gdf.loc[oi, 'geometry'], w)), oi, w)
             for oi, w in candidates),
            key=lambda t: t[0]
        )
        best_defl, best_idx, best_which = scored[0]
        if best_defl > deflection_threshold or best_idx in visited:
            break

        candidate_bearing = bearing_at_endpoint(street_gdf.loc[best_idx, 'geometry'], which=opposite_end(best_which))
        if deflection_deg(entry_bearing, candidate_bearing) > cumulative_cap:
            break

        artery.append(best_idx)
        visited.add(best_idx)
        current_idx, current_exit_end = best_idx, opposite_end(best_which)

    return artery


def trace_oxford_street_and_arteries(
    street_gdf, oxford_ref_coords, corridor_width, node_decimals,
    core_deflection_threshold, artery_deflection_threshold, cumulative_deflection_cap,
    geographic_crs="EPSG:4326",
):
    """
    Full corridor-tracing pipeline. Defines Oxford Street's core segments by
    topological angular tracing outward from a seed segment near
    oxford_ref_coords, then traces connecting arteries from every segment
    that directly touches the core.

    Parameters
    ----------
    street_gdf : GeoDataFrame
        Full street network to trace over (e.g. loaded from
        NETWORK_CENTRALITY_GPKG), already in a projected CRS.
    oxford_ref_coords : list of (lon, lat)
        Two-point reference line spanning Oxford Street end to end
        (Marble Arch / Tottenham Court Rd by convention), in geographic_crs.
    corridor_width : float
        Buffer width (metres) around the reference line used as a sanity
        bound during core tracing.
    node_decimals, core_deflection_threshold, artery_deflection_threshold,
    cumulative_deflection_cap : as in config.py.

    Returns
    -------
    streets_gdf : GeoDataFrame
        street_gdf filtered to core + artery segments, with a
        'segment_type' column ('core' / 'artery').
    oxford_idx, all_artery_idx : set
        Index sets into street_gdf, for diagnostics.
    """
    from shapely.geometry import LineString
    import geopandas as gpd

    node_index = build_node_index(street_gdf, node_decimals)

    oxford_ref = LineString(oxford_ref_coords)
    oxford_ref_gdf = gpd.GeoSeries([oxford_ref], crs=geographic_crs).to_crs(street_gdf.crs)
    corridor = oxford_ref_gdf.buffer(corridor_width).iloc[0]

    seed_idx, seed_dist = find_seed_segment(street_gdf, oxford_ref_gdf.iloc[0])
    print(f"Seed segment: {seed_idx}, distance to reference centroid: {seed_dist:.1f}m")
    if seed_dist > corridor_width:
        print(f"WARNING: seed segment is {seed_dist:.1f}m from the reference line, "
              f"outside corridor_width ({corridor_width}m). oxford_ref_coords may not "
              "line up with street_gdf's actual geometry/CRS -- check before trusting the trace.")

    oxford_idx = (
        set(trace_core(street_gdf, node_index, seed_idx, 'end', corridor,
                        core_deflection_threshold, node_decimals))
        | set(trace_core(street_gdf, node_index, seed_idx, 'start', corridor,
                          core_deflection_threshold, node_decimals))
    )
    print(f"Oxford Street core segments (topologically traced): {len(oxford_idx)}")

    direct_junctions = find_direct_junctions(street_gdf, node_index, oxford_idx, node_decimals)
    print(f"Directly-touching junction segments: {len(direct_junctions)}")

    arteries = {}
    for idx in direct_junctions:
        coords = list(street_gdf.loc[idx, 'geometry'].coords)
        for which, key in (('start', tuple(np.round(coords[0], node_decimals))),
                            ('end', tuple(np.round(coords[-1], node_decimals)))):
            if any(oi in oxford_idx for oi, _ in node_index[key]):
                arteries[idx] = trace_artery(
                    street_gdf, node_index, idx, which,
                    artery_deflection_threshold, cumulative_deflection_cap, node_decimals,
                )
                break

    all_artery_idx = set(i for chain in arteries.values() for i in chain)
    print(f"Artery seed junctions: {len(arteries)}, total artery segments: {len(all_artery_idx)}")

    overlap = oxford_idx & all_artery_idx
    if overlap:
        print(f"NOTE: {len(overlap)} segments appear in both core and artery sets; "
              "core takes precedence for segment_type.")

    combined_idx = list(oxford_idx | all_artery_idx)
    streets_gdf = street_gdf.loc[combined_idx].copy()
    streets_gdf['segment_type'] = [
        'core' if i in oxford_idx else 'artery' for i in streets_gdf.index
    ]

    return streets_gdf, oxford_idx, all_artery_idx
