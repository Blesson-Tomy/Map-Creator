import json
import math

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_point_from_id(points_mapping, point_id):
    """Get coordinates for a point ID from the mapping."""
    point_str = str(point_id)
    if point_str in points_mapping['points']:
        p = points_mapping['points'][point_str]
        return (p['x'], p['y'])
    else:
        raise ValueError(f"Point ID {point_id} not found in mapping")

def calculate_quadrilateral_centroid(p1, p2, p3, p4):
    """
    Calculate the centroid (center) of a quadrilateral from 4 points.
    Uses the average of the 4 points as a simple centroid.
    """
    centroid_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
    centroid_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
    return (centroid_x, centroid_y)

def label_rooms(points_mapping_file, output_file=None):
    """
    Create rooms from 4-point quadrilaterals and store their centroids.
    """
    
    # Define rooms - each room is identified by 4 point IDs forming a quadrilateral
    rooms = {
        # Format 1 (without name): room_id: [point_id_1, point_id_2, point_id_3, point_id_4]
        # Format 2 (with name): room_id: {"point_ids": [...], "name": "Room Name"}
        1: {"point_ids": [20, 21, 25, 24], "name": "Lift"},
        2: {"point_ids": [1, 19, 17, 94], "name": "210: Staff Room"},
        3: {"point_ids": [33, 37, 89, 90], "name": "209: Programming Lab"},
        4: {"point_ids": [94, 17, 15, 91], "name": "211: Staff Room"},
        5: {"point_ids": [84, 86, 88, 85], "name": "212: IEDC"},
        6: {"point_ids": [0, 10, 84, 85], "name": "213: Lecture Hall"},
        7: {"point_ids": [28, 36, 89, 90], "name": "208: Lecture Hall"},
        8: {"point_ids": [34, 35, 41, 40], "name": "202: Lecture Hall"},
        9: {"point_ids": [40, 44, 41, 47], "name": "203: Staff Room"},
        10: {"point_ids": [48, 52, 51, 53], "name": "204: HOD Office"},
        11: {"point_ids": [52, 58, 72, 53], "name": "205: Staff Room"},
        12: {"point_ids": [42, 81, 43, 59], "name": "206: Lecture Hall"},
        13: {"point_ids": [42, 43, 82, 76], "name": "207: Lecture Hall"},
    }
    
    if output_file is None:
        output_file = 'json/floor_2_rooms.json'
    
    # Load points mapping
    points_mapping = load_json(points_mapping_file)
    
    # Create rooms data structure
    rooms_data = {
        'total_rooms': len(rooms),
        'rooms': []
    }
    
    # Process each room
    for room_id, room_data in rooms.items():
        # Handle both formats: list of points or dict with point_ids and name
        if isinstance(room_data, list):
            point_ids = room_data
            room_name = None
        elif isinstance(room_data, dict):
            point_ids = room_data.get('point_ids', [])
            room_name = room_data.get('name', None)
        else:
            print(f"Warning: Room {room_id} has invalid format, skipping")
            continue
        
        if len(point_ids) != 4:
            print(f"Warning: Room {room_id} does not have exactly 4 points, skipping")
            continue
        
        try:
            # Get coordinates for each point
            p1 = get_point_from_id(points_mapping, point_ids[0])
            p2 = get_point_from_id(points_mapping, point_ids[1])
            p3 = get_point_from_id(points_mapping, point_ids[2])
            p4 = get_point_from_id(points_mapping, point_ids[3])
            
            # Calculate centroid
            centroid = calculate_quadrilateral_centroid(p1, p2, p3, p4)
            
            # Create room entry
            room_entry = {
                'id': room_id,
                'x': centroid[0],
                'y': centroid[1],
                'name': room_name,
                'point_ids': point_ids
            }
            rooms_data['rooms'].append(room_entry)
            
            print(f"Room {room_id}: Points {point_ids} -> Centroid: ({centroid[0]:.2f}, {centroid[1]:.2f}) - Name: {room_name}")
        
        except ValueError as e:
            print(f"Error processing room {room_id}: {e}")
    
    # Save rooms data
    save_json(rooms_data, output_file)
    print(f"\nSaved {len(rooms_data['rooms'])} rooms to {output_file}")

if __name__ == '__main__':
    label_rooms('json/floor_2_points_mapping.json')
