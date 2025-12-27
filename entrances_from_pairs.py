import json

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def create_entrances_from_pairs(points_mapping_file, pairs_list):
    """
    Takes a list of point ID pairs and creates entrances from their midpoints.
    
    Args:
        points_mapping_file: JSON file with point ID to coordinate mapping
        pairs_list: List of tuples like [(1, 2), (3, 4), ...]
    """
    points_mapping = load_json(points_mapping_file)
    points = {int(pid): (coord['x'], coord['y']) for pid, coord in points_mapping['points'].items()}
    
    entrances = []
    
    for entrance_id, (p1_id, p2_id) in enumerate(pairs_list, 1):
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
        
        entrances.append({
            'id': entrance_id,
            'x': round(midpoint[0], 1),
            'y': round(midpoint[1], 1)
        })
    
    return entrances

def save_entrances(entrances, output_file):
    """Save entrances to JSON file."""
    output = {'entrances': entrances}
    save_json(output, output_file)
    print(f"Saved {len(entrances)} entrances to {output_file}")

if __name__ == '__main__':
    # Example: Create entrances from point pairs
    # Edit this list with the pairs you want from the image
    pairs = [
        # (point_id_1, point_id_2),
        # Format: (1, 2), (3, 4), etc.
    ]
    
    entrances = create_entrances_from_pairs('json/first_floor_points_mapping.json', pairs)
    save_entrances(entrances, 'json/first_floor_entrances.json')
