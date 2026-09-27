"""Closed aisle geometry certificates; vehicle swept paths remain separate."""
import math
from shapely.geometry import Polygon, LineString


def closed_aisle_loop(drive, width):
    """Find a closed centreline with a full-width corridor inside drawn aisles.

    A connected C/comb or a pinched return leg is not a loop. This conservative
    polygon-offset certificate does not certify steering radius or every bay's
    route to the loop; those require separate path and frontage checks.
    """
    if not isinstance(width,(float,int)) or isinstance(width,bool) or not math.isfinite(width) or width<=0:
        return None
    if drive.is_empty or not drive.is_valid:
        return None
    candidates=[]
    for part in ([drive] if drive.geom_type=='Polygon' else getattr(drive,'geoms',[])):
        if part.geom_type!='Polygon':
            continue
        for interior in part.interiors:
            island=Polygon(interior)
            offset=island.buffer(width/2,join_style=2)
            if offset.geom_type!='Polygon':
                continue
            path=LineString(offset.exterior.coords)
            if path.is_ring and part.buffer(1e-6).covers(path.buffer(width/2,join_style=2)):
                candidates.append(path)
    return max(candidates,key=lambda g:g.length) if candidates else None
