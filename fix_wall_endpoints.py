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
    
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx**2 + dy**2
    
    if length_sq == 0:
        return seg_start
    
    t = ((px - x1) * dx + (py - y1) * dy) / length_sq
    t = max(0, min(1, t))
    
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

def fix_wall_endpoints(input_file, output_file, endpoint_snap_radius=30, line_snap_radius=15):
    """
    Fix wall endpoints by:
    1. Snapping endpoints to other nearby endpoints
    2. Snapping endpoints to nearby wall lines
    
    Args:
        input_file: Path to original walls JSON
        output_file: Path to corrected walls JSON
        endpoint_snap_radius: Radius to search for nearby endpoints
        line_snap_radius: Radius to search for nearby wall lines
    """
    
    with open(input_file, 'r') as f:
        walls = json.load(f)
    
    print(f"Loaded {len(walls)} wall segments")
    print(f"Processing wall endpoints...")
    
    # Extract all endpoints
    endpoints = []
    endpoint_to_walls = {}  # Map endpoint to list of (wall_idx, position)
    
    for wall_idx, wall in enumerate(walls):
        start = (wall['x1'], wall['y1'])
        end = (wall['x2'], wall['y2'])
        
        endpoints.append(start)
        endpoints.append(end)
        
        if start not in endpoint_to_walls:
            endpoint_to_walls[start] = []
        endpoint_to_walls[start].append((wall_idx, 'start'))
        
        if end not in endpoint_to_walls:
            endpoint_to_walls[end] = []
        endpoint_to_walls[end].append((wall_idx, 'end'))
    
    print(f"Found {len(set(endpoints))} unique endpoints")
    
    # Build mapping of original endpoint to corrected endpoint
    correction_map = {}
    
    # Phase 1: Snap nearby endpoints together
    unique_endpoints = list(set(endpoints))
    endpoint_merged_to = {}  # Maps endpoint to merged endpoint
    
    for i, ep1 in enumerate(unique_endpoints):
        if ep1 in endpoint_merged_to:
            continue  # Already merged
        
        # Find all nearby endpoints
        nearby = [ep1]
        for ep2 in unique_endpoints[i+1:]:
            if ep2 in endpoint_merged_to:
                continue
            if distance_point_to_point(ep1, ep2) <= endpoint_snap_radius:
                nearby.append(ep2)
        
        if len(nearby) > 1:
            # Snap all nearby endpoints to their average
            avg_x = sum(ep[0] for ep in nearby) / len(nearby)
            avg_y = sum(ep[1] for ep in nearby) / len(nearby)
            merged_point = (int(round(avg_x)), int(round(avg_y)))
            
            for ep in nearby:
                endpoint_merged_to[ep] = merged_point
            print(f"  Merged {len(nearby)} endpoints at {nearby[0]} -> {merged_point}")
    
    # Phase 2: Snap endpoints to nearby wall lines (but not to the wall they belong to)
    for endpoint in unique_endpoints:
        merged = endpoint_merged_to.get(endpoint, endpoint)
        
        # Find walls that this endpoint does NOT belong to
        my_walls = set(wall_idx for wall_idx, _ in endpoint_to_walls.get(endpoint, []))
        
        best_projection = merged
        best_distance = line_snap_radius
        best_wall_idx = -1
        
        for wall_idx, wall in enumerate(walls):
            # Skip if this endpoint belongs to this wall
            if wall_idx in my_walls:
                continue
            
            seg_start = (wall['x1'], wall['y1'])
            seg_end = (wall['x2'], wall['y2'])
            
            dist = distance_point_to_segment(merged, seg_start, seg_end)
            
            if dist < best_distance:
                best_distance = dist
                best_projection = project_point_on_segment(merged, seg_start, seg_end)
                best_wall_idx = wall_idx
        
        if best_wall_idx != -1:
            print(f"  Endpoint {merged} snapped to wall {best_wall_idx} line at distance {best_distance:.1f}px")
            correction_map[endpoint] = best_projection
        else:
            correction_map[endpoint] = merged
    
    # Apply corrections to all walls
    fixed_walls = []
    fixes_applied = 0
    
    for wall_idx, wall in enumerate(walls):
        start = (wall['x1'], wall['y1'])
        end = (wall['x2'], wall['y2'])
        
        new_start = correction_map.get(start, start)
        new_end = correction_map.get(end, end)
        
        if new_start != start or new_end != end:
            fixes_applied += 1
            print(f"  Wall {wall_idx}: ({wall['x1']},{wall['y1']}) -> ({new_start[0]},{new_start[1]}), "
                  f"({wall['x2']},{wall['y2']}) -> ({new_end[0]},{new_end[1]})")
        
        fixed_wall = wall.copy()
        fixed_wall['x1'] = int(new_start[0])
        fixed_wall['y1'] = int(new_start[1])
        fixed_wall['x2'] = int(new_end[0])
        fixed_wall['y2'] = int(new_end[1])
        
        fixed_walls.append(fixed_wall)
    
    # Save corrected walls
    with open(output_file, 'w') as f:
        json.dump(fixed_walls, f, indent=2)
    
    print(f"\nApplied {fixes_applied} fixes to {len(fixed_walls)} walls")
    print(f"Saved corrected walls to {output_file}")

if __name__ == "__main__":
    fix_wall_endpoints("json/floor_1_aligned.json", "json/floor_1_aligned_fixed.json", 
                       endpoint_snap_radius=30, line_snap_radius=15)
    print("\nDone!")
