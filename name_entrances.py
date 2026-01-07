import json

def name_entrances(entrances_file, output_file=None):
    """
    Add names and room numbers to entrances in the JSON file.
    Only entrances with data in the dictionary will have attributes added.
    """
    
    # Define entrance details - add name, room_no, and/or available for each entrance
    entrance_details = {
        # Format: entrance_id: {"name": "...", "room_no": "...", "available": True/False/None}
        # You can include any combination, or use None for null values
        1: {"name": "Lift", "room_no": None, "available": True},
        2: {"name": "Programming Lab", "room_no": "209", "available": True},
        3: {"name": "Staff Room", "room_no": "210", "available": True},
        4: {"name": "Staff Room", "room_no": "211", "available": True},
        5: {"name": "Programming Lab", "room_no": "209", "available": True},
        6: {"name": "Lecture Hall", "room_no": "208", "available": True},
        7: {"name": "IEDC", "room_no": "212", "available": True},
        8: {"name": "Lecture Hall", "room_no": "213", "available": True},
        9: {"name": "Lecture Hall", "room_no": "213", "available": True},
        10: {"name": "Lecture Hall", "room_no": "208", "available": True},
        11: {"name": None, "room_no": None, "available": True},
        12: {"name": None, "room_no": None, "available": True},
        13: {"name": None, "room_no": None, "available": True},
        14: {"name": None, "room_no": None, "available": True},
        15: {"name": None, "room_no": None, "available": True},
        16: {"name": "Lecture Hall", "room_no": "207", "available": True},
        17: {"name": "Lecture Hall", "room_no": "202", "available": True},
        18: {"name": "Lecture Hall", "room_no": "202", "available": True},
        19: {"name": "Staff Room", "room_no": "203", "available": True},
        20: {"name": "Lecture Hall", "room_no": "207", "available": True},
        21: {"name": "Lecture Hall", "room_no": "206", "available": True},
        22: {"name": "HOD Office", "room_no": "204", "available": True},
        23: {"name": "Staff Room", "room_no": "205", "available": True},
        24: {"name": "Lecture Hall", "room_no": "206", "available": True},
        25: {"name": None, "room_no": None, "available": True},
    }
    
    if output_file is None:
        output_file = entrances_file
    
    # Load current entrances
    with open(entrances_file, 'r') as f:
        data = json.load(f)
    
    # Add details to entrances that have them defined
    for entrance in data['entrances']:
        entrance_id = entrance['id']
        if entrance_id in entrance_details:
            details = entrance_details[entrance_id]
            if 'name' in details:
                entrance['name'] = details['name']
            if 'room_no' in details:
                entrance['room_no'] = details['room_no']
            if 'available' in details:
                entrance['available'] = details['available']
    
    # Save updated data
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Print summary
    named_count = sum(1 for e in data['entrances'] if 'name' in e)
    room_count = sum(1 for e in data['entrances'] if 'room_no' in e)
    available_count = sum(1 for e in data['entrances'] if 'available' in e)
    print(f"Updated entrances: {named_count} have names, {room_count} have room numbers, {available_count} have availability")
    print(f"Saved to {output_file}")

if __name__ == '__main__':
    name_entrances('json/floor_2_entrances.json')
