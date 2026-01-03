import math
from typing import List, Dict, Tuple

def distance_point_to_point(p1: Tuple, p2: Tuple) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def project_point_on_segment(point: Tuple, seg_start: Tuple, seg_end: Tuple) -> Tuple:
    """
    Project a point onto a line segment and return the projected point.
    """
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end
    
    # Vector from start to end
    dx = x2 - x1
    dy = y2 - y1
    
    # Length squared of segment
    length_sq = dx**2 + dy**2
    
    # If segment is a point, return that point
    if length_sq == 0:
        return seg_start
    
    # Parameter t of the closest point on the line
    t = ((px - x1) * dx + (py - y1) * dy) / length_sq
    
    # Clamp t to [0, 1] to stay on the segment
    t = max(0, min(1, t))
    
    # Projected point on segment
    projected = (x1 + t * dx, y1 + t * dy)
    
    return projected

def distance_point_to_segment(point: Tuple, seg_start: Tuple, seg_end: Tuple) -> float:
    """Calculate distance from point to line segment."""
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end
    
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx**2 + dy**2
    
    if length_sq == 0:
        return distance_point_to_point(point, seg_start)
    
    t = ((px - x1) * dx + (py - y1) * dy) / length_sq
    t = max(0, min(1, t))
    
    closest = (x1 + t * dx, y1 + t * dy)
    return distance_point_to_point(point, closest)

def straighten_stair_lines(stairs: List[Dict], tolerance: int = 10) -> List[Dict]:
    """
    Straighten stair lines that should be perpendicular or horizontal.
    If x-coordinates differ by <= tolerance, make them equal.
    If y-coordinates differ by <= tolerance, make them equal.
    
    Args:
        stairs: List of stair segment dictionaries
        tolerance: Maximum difference to consider for straightening (pixels)
    
    Returns:
        List of straightened stair segments
    """
    straightened = []
    corrections = 0
    
    for stair_idx, stair in enumerate(stairs):
        x1, y1 = stair['x1'], stair['y1']
        x2, y2 = stair['x2'], stair['y2']
        
        # Check if should be vertical (same x)
        if abs(x1 - x2) <= tolerance and abs(x1 - x2) > 0:
            new_x = int(round((x1 + x2) / 2.0))
            x1 = x2 = new_x
            corrections += 1
        
        # Check if should be horizontal (same y)
        elif abs(y1 - y2) <= tolerance and abs(y1 - y2) > 0:
            new_y = int(round((y1 + y2) / 2.0))
            y1 = y2 = new_y
            corrections += 1
        
        # Create corrected stair segment
        corrected_stair = stair.copy()
        corrected_stair['x1'] = x1
        corrected_stair['y1'] = y1
        corrected_stair['x2'] = x2
        corrected_stair['y2'] = y2
        
        straightened.append(corrected_stair)
    
    return straightened

def merge_duplicate_vertices(segments: List[Dict], tolerance: int = 2) -> List[Dict]:
    """
    Merge duplicate or near-duplicate vertices in segments.
    
    Args:
        segments: List of segment dictionaries with x1,y1,x2,y2 keys
        tolerance: Maximum distance to consider points as duplicates
    
    Returns:
        List of segments with merged vertices
    """
    # Collect all unique vertices
    vertices = {}
    vertex_map = {}  # Maps original vertex to merged vertex
    
    for seg_idx, seg in enumerate(segments):
        for pos in ['start', 'end']:
            if pos == 'start':
                v = (seg['x1'], seg['y1'])
            else:
                v = (seg['x2'], seg['y2'])
            
            if v in vertex_map:
                continue
            
            # Find if this vertex is close to any existing vertex
            found_merge = False
            for existing_v in vertices.keys():
                if distance_point_to_point(v, existing_v) <= tolerance:
                    vertex_map[v] = existing_v
                    found_merge = True
                    break
            
            if not found_merge:
                vertices[v] = True
                vertex_map[v] = v
    
    # Merge vertices and update segments
    merged_segments = []
    merges_applied = 0
    
    for seg_idx, seg in enumerate(segments):
        v1 = (seg['x1'], seg['y1'])
        v2 = (seg['x2'], seg['y2'])
        
        merged_v1 = vertex_map.get(v1, v1)
        merged_v2 = vertex_map.get(v2, v2)
        
        if (merged_v1 != v1 or merged_v2 != v2):
            merges_applied += 1
        
        merged_seg = seg.copy()
        merged_seg['x1'] = int(merged_v1[0])
        merged_seg['y1'] = int(merged_v1[1])
        merged_seg['x2'] = int(merged_v2[0])
        merged_seg['y2'] = int(merged_v2[1])
        
        merged_segments.append(merged_seg)
    
    return merged_segments

def merge_stairs_to_walls(stairs: List[Dict], walls: List[Dict], tolerance: int = 5) -> List[Dict]:
    """
    Merge stair vertices with nearby wall vertices.
    If a stair endpoint is very close to a wall endpoint, snap it to that wall endpoint.
    
    Args:
        stairs: List of stair segments
        walls: List of wall segments
        tolerance: Maximum distance to snap to wall endpoints
    
    Returns:
        List of stairs with merged endpoints
    """
    # Extract all wall vertices
    wall_vertices = set()
    for wall in walls:
        wall_vertices.add((wall['x1'], wall['y1']))
        wall_vertices.add((wall['x2'], wall['y2']))
    
    merged_stairs = []
    merges_applied = 0
    
    for stair_idx, stair in enumerate(stairs):
        v1 = (stair['x1'], stair['y1'])
        v2 = (stair['x2'], stair['y2'])
        
        merged_v1 = v1
        merged_v2 = v2
        
        # Check if v1 is close to any wall vertex
        for wv in wall_vertices:
            if distance_point_to_point(v1, wv) <= tolerance:
                merged_v1 = wv
                merges_applied += 1
                break
        
        # Check if v2 is close to any wall vertex
        for wv in wall_vertices:
            if distance_point_to_point(v2, wv) <= tolerance:
                merged_v2 = wv
                merges_applied += 1
                break
        
        merged_stair = stair.copy()
        merged_stair['x1'] = int(merged_v1[0])
        merged_stair['y1'] = int(merged_v1[1])
        merged_stair['x2'] = int(merged_v2[0])
        merged_stair['y2'] = int(merged_v2[1])
        
        merged_stairs.append(merged_stair)
    
    return merged_stairs

def fix_wall_endpoints(walls_data: List[Dict]) -> List[Dict]:
    """
    Fix wall endpoints by snapping them to their own wall lines.
    Ensures endpoints are exactly on their own wall lines.
    """
    if not walls_data:
        return walls_data
    
    walls = [dict(w) for w in walls_data]  # Deep copy
    
    # For each wall, check if endpoints are on the line
    for wall in walls:
        x1, y1, x2, y2 = wall['x1'], wall['y1'], wall['x2'], wall['y2']
        
        # Check if this is mostly vertical
        if abs(x1 - x2) < abs(y1 - y2):  # Vertical line
            # Snap x coordinates to average x
            avg_x = (x1 + x2) // 2
            wall['x1'] = avg_x
            wall['x2'] = avg_x
        else:  # Horizontal line
            # Snap y coordinates to average y
            avg_y = (y1 + y2) // 2
            wall['y1'] = avg_y
            wall['y2'] = avg_y
    
    return walls

def snap_stairs_to_walls(stairs_data: List[Dict], walls_data: List[Dict], 
                        endpoint_threshold: float = 50.0, 
                        line_threshold: float = 30.0) -> List[Dict]:
    """
    Snap stair points to nearby wall endpoints or lines with post-processing.
    
    Two-priority snapping system:
    1. Priority 1: Snap to nearest wall endpoint within endpoint_threshold
    2. Priority 2: If no endpoint found, snap to nearest wall line within line_threshold
    
    Post-processing:
    - Straighten near-vertical/horizontal stair lines
    - Merge duplicate/near-duplicate vertices
    - Merge stair vertices with wall vertices
    
    Args:
        stairs_data: List of stair line segments with x1, y1, x2, y2
        walls_data: List of wall line segments with x1, y1, x2, y2
        endpoint_threshold: Distance threshold for snapping to wall endpoints (pixels)
        line_threshold: Distance threshold for snapping to wall lines (pixels)
    
    Returns:
        Modified stairs_data with snapped coordinates
    """
    if not stairs_data or not walls_data:
        return stairs_data
    
    stairs = [dict(s) for s in stairs_data]  # Deep copy
    
    # Collect all wall endpoints
    wall_endpoints = set()
    for wall in walls_data:
        wall_endpoints.add((wall['x1'], wall['y1']))
        wall_endpoints.add((wall['x2'], wall['y2']))
    
    # Process each stair line's endpoints
    for stair in stairs:
        # Process start point (x1, y1)
        px, py = stair['x1'], stair['y1']
        
        best_snap = None
        best_dist = endpoint_threshold
        snap_type = None
        
        # Try to snap to wall endpoints
        for ex, ey in wall_endpoints:
            dist = distance_point_to_point((px, py), (ex, ey))
            if dist < best_dist:
                best_dist = dist
                best_snap = (ex, ey)
                snap_type = "endpoint"
        
        # If no endpoint found, try to snap to wall lines
        if snap_type != "endpoint":
            best_dist = line_threshold
            for wall in walls_data:
                dist = distance_point_to_segment((px, py), (wall['x1'], wall['y1']), (wall['x2'], wall['y2']))
                
                if dist < best_dist:
                    # Get closest point on the line
                    closest = project_point_on_segment((px, py), (wall['x1'], wall['y1']), (wall['x2'], wall['y2']))
                    best_snap = closest
                    best_dist = dist
                    snap_type = "line"
        
        # Apply snap to start point
        if best_snap is not None:
            stair['x1'] = int(best_snap[0])
            stair['y1'] = int(best_snap[1])
        
        # Process end point (x2, y2)
        px, py = stair['x2'], stair['y2']
        
        best_snap = None
        best_dist = endpoint_threshold
        snap_type = None
        
        # Try to snap to wall endpoints
        for ex, ey in wall_endpoints:
            dist = distance_point_to_point((px, py), (ex, ey))
            if dist < best_dist:
                best_dist = dist
                best_snap = (ex, ey)
                snap_type = "endpoint"
        
        # If no endpoint found, try to snap to wall lines
        if snap_type != "endpoint":
            best_dist = line_threshold
            for wall in walls_data:
                dist = distance_point_to_segment((px, py), (wall['x1'], wall['y1']), (wall['x2'], wall['y2']))
                
                if dist < best_dist:
                    # Get closest point on the line
                    closest = project_point_on_segment((px, py), (wall['x1'], wall['y1']), (wall['x2'], wall['y2']))
                    best_snap = closest
                    best_dist = dist
                    snap_type = "line"
        
        # Apply snap to end point
        if best_snap is not None:
            stair['x2'] = int(best_snap[0])
            stair['y2'] = int(best_snap[1])
    
    # Post-processing: Straighten stair lines that should be perpendicular or horizontal
    stairs = straighten_stair_lines(stairs, tolerance=10)
    
    # Merge duplicate/near-duplicate vertices within stairs
    stairs = merge_duplicate_vertices(stairs, tolerance=2)
    
    # Merge stair vertices with wall vertices
    stairs = merge_stairs_to_walls(stairs, walls_data, tolerance=5)
    
    return stairs
