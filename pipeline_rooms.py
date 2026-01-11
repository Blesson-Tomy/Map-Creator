"""Room creation utilities for floor plan processing."""

import json
import math


def parse_room_name(full_name):
    """
    Parse room name to extract number and name separately.
    
    Examples:
        "114: Gents Toilet" -> {"number": 114, "name": "Gents Toilet"}
        "Lift" -> {"number": None, "name": "Lift"}
    
    Args:
        full_name: String with optional "number: name" format
    
    Returns:
        Dict with 'number' and 'name' keys
    """
    if not full_name or not full_name.strip():
        return {"number": None, "name": None}
    
    full_name = full_name.strip()
    
    # Check if format is "number: name"
    if ':' in full_name:
        parts = full_name.split(':', 1)
        try:
            number = int(parts[0].strip())
            name = parts[1].strip() if len(parts) > 1 else None
            return {"number": number, "name": name}
        except ValueError:
            # If conversion fails, treat whole thing as name
            return {"number": None, "name": full_name}
    else:
        return {"number": None, "name": full_name}


def calculate_quadrilateral_centroid(p1, p2, p3, p4):
    """
    Calculate the centroid (center) of a quadrilateral from 4 points.
    Uses the average of the 4 points as centroid.
    
    Args:
        p1, p2, p3, p4: Tuples (x, y) for each point
    
    Returns:
        Tuple (centroid_x, centroid_y)
    """
    centroid_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
    centroid_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
    return (centroid_x, centroid_y)


def create_room_from_points(p1_id, p2_id, p3_id, p4_id, points, room_name, room_id):
    """
    Create a room dict from 4 point IDs and room name.
    
    Args:
        p1_id, p2_id, p3_id, p4_id: Point IDs (as integers)
        points: Dict mapping point_id to (x, y) coordinates
        room_name: Full room name (e.g., "114: Gents Toilet")
        room_id: Sequential room ID
    
    Returns:
        Dict with room data including centroid and parsed name/number
    """
    # Get coordinates for each point
    p1 = points[str(p1_id)]
    p2 = points[str(p2_id)]
    p3 = points[str(p3_id)]
    p4 = points[str(p4_id)]
    
    # Calculate centroid
    centroid = calculate_quadrilateral_centroid(p1, p2, p3, p4)
    
    # Parse room name
    parsed = parse_room_name(room_name)
    
    # Create room entry
    room_entry = {
        "id": room_id,
        "x": centroid[0],
        "y": centroid[1],
        "number": parsed["number"],
        "name": parsed["name"],
        "point_ids": [p1_id, p2_id, p3_id, p4_id]
    }
    
    return room_entry


def save_rooms_json(rooms, output_file):
    """
    Save rooms data to JSON file.
    
    Args:
        rooms: List of room dicts
        output_file: Output file path
    """
    rooms_data = {
        "total_rooms": len(rooms),
        "rooms": rooms
    }
    
    with open(output_file, 'w') as f:
        json.dump(rooms_data, f, indent=2)
