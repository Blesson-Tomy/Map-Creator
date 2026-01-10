"""Pipeline for creating entrances from point pairs."""

import json
import math

def load_points_mapping(points_mapping_file):
    """Load points mapping from JSON file."""
    with open(points_mapping_file, 'r') as f:
        points_mapping = json.load(f)
    return {int(pid): (coord['x'], coord['y']) for pid, coord in points_mapping['points'].items()}

def create_entrance_from_pair(p1_id, p2_id, points, name=None, room_no=None, stairs=False, entrance_id=1):
    """
    Create an entrance from two point IDs.
    
    Args:
        p1_id: First point ID
        p2_id: Second point ID
        points: Dictionary of point_id -> (x, y)
        name: Optional entrance name
        room_no: Optional room number
        stairs: Whether this is a staircase entrance
        entrance_id: ID for this entrance
    
    Returns:
        Entrance dict
    """
    if p1_id not in points or p2_id not in points:
        return None
    
    p1 = points[p1_id]
    p2 = points[p2_id]
    
    # Calculate midpoint
    midpoint = (
        (p1[0] + p2[0]) / 2,
        (p1[1] + p2[1]) / 2
    )
    
    entrance = {
        'id': entrance_id,
        'x': round(midpoint[0], 1),
        'y': round(midpoint[1], 1),
        'available': True
    }
    
    if name:
        entrance['name'] = name
    else:
        entrance['name'] = None
    
    if room_no:
        entrance['room_no'] = room_no
    else:
        entrance['room_no'] = None
    
    if stairs:
        entrance['stairs'] = True
    
    return entrance

def save_entrances_json(entrances, output_file):
    """Save entrances to JSON file in the standard format."""
    output = {'entrances': entrances}
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
