import json
import math

def distance_point_to_point(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def project_point_on_segment(point, seg_start, seg_end):
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

def distance_point_to_segment(point, seg_start, seg_end):
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

def straighten_stair_lines(stairs, tolerance=10):
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
            print(f"  Stair {stair_idx}: Straightened vertical (x: {x1},{x2} -> {new_x},{new_x})")
            x1 = x2 = new_x
            corrections += 1
        
        # Check if should be horizontal (same y)
        elif abs(y1 - y2) <= tolerance and abs(y1 - y2) > 0:
            new_y = int(round((y1 + y2) / 2.0))
            print(f"  Stair {stair_idx}: Straightened horizontal (y: {y1},{y2} -> {new_y},{new_y})")
            y1 = y2 = new_y
            corrections += 1
        
        # Create corrected stair segment
        corrected_stair = stair.copy()
        corrected_stair['x1'] = x1
        corrected_stair['y1'] = y1
        corrected_stair['x2'] = x2
        corrected_stair['y2'] = y2
        
        straightened.append(corrected_stair)
    
    print(f"\nStraightened {corrections} stair lines")
    return straightened

def merge_stairs_to_walls(stairs, walls, tolerance=5):
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
                print(f"  Stair {stair_idx}: Merged start vertex {v1} -> wall vertex {wv}")
                break
        
        # Check if v2 is close to any wall vertex
        for wv in wall_vertices:
            if distance_point_to_point(v2, wv) <= tolerance:
                merged_v2 = wv
                merges_applied += 1
                print(f"  Stair {stair_idx}: Merged end vertex {v2} -> wall vertex {wv}")
                break
        
        merged_stair = stair.copy()
        merged_stair['x1'] = int(merged_v1[0])
        merged_stair['y1'] = int(merged_v1[1])
        merged_stair['x2'] = int(merged_v2[0])
        merged_stair['y2'] = int(merged_v2[1])
        
        merged_stairs.append(merged_stair)
    
    if merges_applied > 0:
        print(f"\nMerged {merges_applied} stair vertices with wall vertices")
    
    return merged_stairs

def merge_duplicate_vertices(segments, tolerance=2):
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
            print(f"  Segment {seg_idx}: Merged vertices ({v1},{v2}) -> ({merged_v1},{merged_v2})")
        
        merged_seg = seg.copy()
        merged_seg['x1'] = int(merged_v1[0])
        merged_seg['y1'] = int(merged_v1[1])
        merged_seg['x2'] = int(merged_v2[0])
        merged_seg['y2'] = int(merged_v2[1])
        
        merged_segments.append(merged_seg)
    
    if merges_applied > 0:
        print(f"\nMerged {merges_applied} duplicate vertices")
    
    return merged_segments

def snap_stairs_to_walls(walls_file, stairs_file, output_file, endpoint_search_radius=100):
    """
    Snap stair points to walls using a two-priority system:
    1. Priority 1: Snap to nearest wall endpoint within search radius
    2. Priority 2: If no endpoint found, snap to nearest wall line
    """
    
    # Load walls and stairs
    with open(walls_file, 'r') as f:
        walls = json.load(f)
    
    with open(stairs_file, 'r') as f:
        stairs = json.load(f)
    
    print(f"Loaded {len(walls)} wall segments")
    print(f"Loaded {len(stairs)} stair segments")
    
    # Extract all wall endpoints
    wall_endpoints = []
    for wall in walls:
        wall_endpoints.append((wall['x1'], wall['y1']))
        wall_endpoints.append((wall['x2'], wall['y2']))
    
    # Remove duplicates
    wall_endpoints = list(set(wall_endpoints))
    print(f"Found {len(wall_endpoints)} unique wall endpoints")
    
    # Process each stair segment
    snapped_stairs = []
    
    for stair_idx, stair in enumerate(stairs):
        points = [(stair['x1'], stair['y1']), (stair['x2'], stair['y2'])]
        snapped_points = []
        
        for point_idx, point in enumerate(points):
            # Priority 1: Find nearest wall endpoint within search radius
            nearest_endpoint = None
            nearest_endpoint_dist = float('inf')
            
            for endpoint in wall_endpoints:
                dist = distance_point_to_point(point, endpoint)
                if dist < nearest_endpoint_dist:
                    nearest_endpoint_dist = dist
                    nearest_endpoint = endpoint
            
            # If found within radius, snap to it
            if nearest_endpoint_dist <= endpoint_search_radius:
                snapped_point = nearest_endpoint
                print(f"  Stair {stair_idx}, point {point_idx}: Priority 1 (endpoint) at distance {nearest_endpoint_dist:.1f}px")
            else:
                # Priority 2: Find nearest wall line and project onto it
                nearest_line_dist = float('inf')
                nearest_projection = point
                
                for wall in walls:
                    seg_start = (wall['x1'], wall['y1'])
                    seg_end = (wall['x2'], wall['y2'])
                    
                    dist = distance_point_to_segment(point, seg_start, seg_end)
                    
                    if dist < nearest_line_dist:
                        nearest_line_dist = dist
                        nearest_projection = project_point_on_segment(point, seg_start, seg_end)
                
                snapped_point = nearest_projection
                print(f"  Stair {stair_idx}, point {point_idx}: Priority 2 (line) at distance {nearest_line_dist:.1f}px")
            
            snapped_points.append(snapped_point)
        
        # Create snapped stair segment (before straightening)
        snapped_stair = {
            'x1': int(round(snapped_points[0][0])),
            'y1': int(round(snapped_points[0][1])),
            'x2': int(round(snapped_points[1][0])),
            'y2': int(round(snapped_points[1][1])),
            'original_x1': stair['x1'],
            'original_y1': stair['y1'],
            'original_x2': stair['x2'],
            'original_y2': stair['y2'],
            'type': 'stair'
        }
        snapped_stairs.append(snapped_stair)
    
    # Straighten stair lines that should be perpendicular or horizontal
    snapped_stairs = straighten_stair_lines(snapped_stairs, tolerance=10)
    
    # Merge duplicate/near-duplicate vertices within stairs
    snapped_stairs = merge_duplicate_vertices(snapped_stairs, tolerance=2)
    
    # Merge stair vertices with wall vertices
    snapped_stairs = merge_stairs_to_walls(snapped_stairs, walls, tolerance=5)
    walls_with_type = []
    for wall in walls:
        wall_copy = wall.copy()
        wall_copy['type'] = 'wall'
        walls_with_type.append(wall_copy)
    
    # Combine walls and stairs
    combined = walls_with_type + snapped_stairs
    
    # Save combined output
    with open(output_file, 'w') as f:
        json.dump(combined, f, indent=2)
    
    print(f"\nSaved combined output to {output_file}")
    print(f"Total segments: {len(combined)} ({len(walls_with_type)} walls + {len(snapped_stairs)} stairs)")

if __name__ == "__main__":
    walls_file = "json/first_floor_aligned_fixed.json"
    stairs_file = "json/first_floor_stairs_aligned.json"
    output_file = "json/first_floor_combined.json"
    
    snap_stairs_to_walls(walls_file, stairs_file, output_file, endpoint_search_radius=20)
    
    print("\nDone! Check the output file for combined walls and snapped stairs.")
