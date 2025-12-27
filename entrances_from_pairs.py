import json
import math

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def line_intersection(p1, p2, p3, p4):
    """Find intersection point of two lines."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-10:
        return None
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    
    return (x, y)

def create_entrances_from_pairs(points_mapping_file, pairs_list):
    """
    Takes a list of point ID pairs and creates entrances from their midpoints.
    
    Args:
        points_mapping_file: JSON file with point ID to coordinate mapping
        pairs_list: List of tuples like [(1, 2), (3, 4), ...] or [(1, 2, 1), (3, 4, 0), ...]
                    Third element (optional): 1 = stairs, 0 = not stairs
    """
    points_mapping = load_json(points_mapping_file)
    points = {int(pid): (coord['x'], coord['y']) for pid, coord in points_mapping['points'].items()}
    
    entrances = []
    
    for entrance_id, pair in enumerate(pairs_list, 1):
        # Handle both 2-tuple and 3-tuple formats
        if len(pair) == 3:
            p1_id, p2_id, is_stairs = pair
        else:
            p1_id, p2_id = pair
            is_stairs = 0
        
        if str(p1_id) not in points_mapping['points'] or str(p2_id) not in points_mapping['points']:
            print(f"Warning: Point {p1_id} or {p2_id} not found")
            continue
        
        p1 = points[int(p1_id)]
        p2 = points[int(p2_id)]
        
        # Calculate midpoint
        midpoint = (
            (p1[0] + p2[0]) / 2,
            (p1[1] + p2[1]) / 2
        )
        
        entrance = {
            'id': entrance_id,
            'x': round(midpoint[0], 1),
            'y': round(midpoint[1], 1)
        }
        
        if is_stairs:
            entrance['stairs'] = True
        
        entrances.append(entrance)
    
    return entrances, len(entrances)

def create_entrances_from_points(floor_file, points_mapping_file, individual_points):
    """
    Takes a list of individual point IDs, extends the line from each point,
    checks for intersection, and creates entrances from the midpoint.
    
    Args:
        floor_file: JSON file with all segments
        points_mapping_file: JSON file with point ID to coordinate mapping
        individual_points: List of point IDs or tuples like [1, 5, (10, 1), ...]
                          If tuple: (point_id, stairs_flag) where 1 = stairs, 0 = not stairs
    """
    segments = load_json(floor_file)
    points_mapping = load_json(points_mapping_file)
    points = {int(pid): (coord['x'], coord['y']) for pid, coord in points_mapping['points'].items()}
    
    entrances = []
    entrance_id = 0
    
    for item in individual_points:
        # Handle both int and tuple formats
        if isinstance(item, tuple):
            point_id, is_stairs = item
        else:
            point_id = item
            is_stairs = 0
        
        if str(point_id) not in points_mapping['points']:
            print(f"Warning: Point {point_id} not found")
            continue
        
        point = points[int(point_id)]
        
        # Find segments that have this point as endpoint
        segments_with_point = []
        for i, seg in enumerate(segments):
            p1 = (seg['x1'], seg['y1'])
            p2 = (seg['x2'], seg['y2'])
            
            if p1 == point:
                segments_with_point.append((i, p1, p2, True))  # True = p1 is our point
            elif p2 == point:
                segments_with_point.append((i, p1, p2, False))  # False = p2 is our point
        
        # For each segment containing this point, extend from the point
        for seg_idx, p1, p2, is_p1 in segments_with_point:
            seg = segments[seg_idx]
            
            # Determine direction: extend FROM the point AWAY from the other end
            if is_p1:
                # Point is p1, extend away from p2 (in direction p1->p2 extended beyond p1 = reverse)
                other_point = p2
                dx = point[0] - other_point[0]  # Direction AWAY from p2
                dy = point[1] - other_point[1]
            else:
                # Point is p2, extend away from p1 (in direction p1->p2 extended beyond p2)
                other_point = p1
                dx = point[0] - other_point[0]  # Direction AWAY from p1
                dy = point[1] - other_point[1]
            
            norm = math.sqrt(dx**2 + dy**2)
            
            if norm == 0:
                continue
            
            # Extend line from point in this direction
            extension_length = 5000
            dx_norm = dx / norm
            dy_norm = dy / norm
            
            line_end = (
                point[0] + dx_norm * extension_length,
                point[1] + dy_norm * extension_length
            )
            
            # Check intersection with all segments (walls and stairs)
            best_intersection = None
            best_distance = float('inf')
            
            for other_seg in segments:
                # Skip the segment this point belongs to
                if other_seg == seg:
                    continue
                
                other_seg_p1 = (other_seg['x1'], other_seg['y1'])
                other_seg_p2 = (other_seg['x2'], other_seg['y2'])
                
                # Find intersection
                intersection = line_intersection(point, line_end, other_seg_p1, other_seg_p2)
                
                if intersection:
                    dist = distance(point, intersection)
                    # Only accept if it's a reasonable distance and not at origin
                    if dist > 1 and dist < best_distance:
                        best_distance = dist
                        best_intersection = intersection
            
            # If found intersection with any segment, add entrance
            if best_intersection:
                midpoint = (
                    (point[0] + best_intersection[0]) / 2,
                    (point[1] + best_intersection[1]) / 2
                )
                
                entrance_id += 1
                entrance = {
                    'id': entrance_id,
                    'x': round(midpoint[0], 1),
                    'y': round(midpoint[1], 1)
                }
                
                if is_stairs:
                    entrance['stairs'] = True
                
                entrances.append(entrance)
                print(f"Point {point_id} -> intersection at {best_intersection}, midpoint: {midpoint}")
    
    return entrances, entrance_id

def save_entrances(entrances, output_file):
    """Save entrances to JSON file."""
    output = {'entrances': entrances}
    save_json(output, output_file)
    print(f"Saved {len(entrances)} entrances to {output_file}")

if __name__ == '__main__':
    # Point pairs: two endpoints that form an entrance
    pairs = [
        # (point_id_1, point_id_2),
        # Format: (1, 2), (3, 4), etc.
        (108,109),
        (30,29),
        (14,105),
        (105,13),
        (28,27),
        (11,12),
        (26,35),
        (9,10),
        (33,34),
        (19,120,1),
        (18,96,1),
        (116,115,1),
        (131,113,1),
        (111,127,1),
        (130,126,1),
        (129,128,1),
        (85,119,1),
        (118,25,1),
        (123,112,1),
        (110,121,1),
        (117,114,1),
        (88,48),
        (83,122,1),
        (44,43,1),
        (77,78),
        (79,55),
        (89,50),
        (56,90),
        (55,80),
        (60,86),
        (81,63),
        (63,74),
        (113,111),
        (45,32,1),
        (124,125,1)
    ]
    
    # Individual points: extend line from these points and find wall intersection
    individual_points = [
        # point_id,
        # Format: 1, 5, 10, etc.
        
    ]
    
    all_entrances = []
    entrance_id = 0
    
    # Process pairs
    if pairs:
        pair_entrances, next_id = create_entrances_from_pairs('json/first_floor_points_mapping.json', pairs)
        all_entrances.extend(pair_entrances)
        entrance_id = next_id
    
    # Process individual points
    if individual_points:
        point_entrances, next_id = create_entrances_from_points(
            'json/first_floor_combined_with_floors.json',
            'json/first_floor_points_mapping.json',
            individual_points
        )
        # Update IDs to continue from pairs
        for entrance in point_entrances:
            entrance['id'] = entrance_id + entrance['id']
        all_entrances.extend(point_entrances)
    
    # Save all entrances
    if all_entrances:
        save_entrances(all_entrances, 'json/first_floor_entrances.json')
    else:
        print("No entrances to save. Add pairs or individual_points to the lists.")
