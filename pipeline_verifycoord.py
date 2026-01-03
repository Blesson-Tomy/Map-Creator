import cv2
import numpy as np

def verify_json_coordinates(walls_data, stairs_data=None):
    """
    Verify coordinates and return visualization image without saving.
    Displays walls in green and stairs in magenta.
    
    Args:
        walls_data: List of wall line segments
        stairs_data: Optional list of stair line segments
    
    Returns:
        The verification image as numpy array
    """
    if not walls_data:
        return None

    all_x = []
    all_y = []
    
    for l in walls_data:
        all_x.extend([l['x1'], l['x2']])
        all_y.extend([l['y1'], l['y2']])
    
    if stairs_data:
        for l in stairs_data:
            all_x.extend([l['x1'], l['x2']])
            all_y.extend([l['y1'], l['y2']])

    if not all_x or not all_y:
        return None

    max_x, max_y = max(all_x), max(all_y)
    h, w = max_y + 150, max_x + 150
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background

    # Draw walls in green
    for l in walls_data:
        pt1 = (l['x1'], l['y1'])
        pt2 = (l['x2'], l['y2'])
        cv2.line(img, pt1, pt2, (0, 180, 0), 2)  # Green for walls

    # Draw stairs in magenta if provided
    if stairs_data:
        for l in stairs_data:
            pt1 = (l['x1'], l['y1'])
            pt2 = (l['x2'], l['y2'])
            cv2.line(img, pt1, pt2, (255, 0, 255), 2)  # Magenta for stairs

    # Collect all vertices
    unique_points = set()
    for l in walls_data:
        unique_points.add((l['x1'], l['y1']))
        unique_points.add((l['x2'], l['y2']))
    
    if stairs_data:
        for l in stairs_data:
            unique_points.add((l['x1'], l['y1']))
            unique_points.add((l['x2'], l['y2']))
        
    sorted_points = sorted(list(unique_points), key=lambda p: (p[1], p[0]))
    font = cv2.FONT_HERSHEY_SIMPLEX

    for pt in sorted_points:
        x, y = pt
        
        # Draw Vertex (Red Dot)
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        
        # Draw Coordinate Label (Black, slightly offset)
        coord_text = f"({x},{y})"
        cv2.putText(img, coord_text, (x + 8, y - 8), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # Legend
    cv2.putText(img, "Walls (Green)", (20, h - 40), font, 0.5, (0, 180, 0), 1, cv2.LINE_AA)
    if stairs_data:
        cv2.putText(img, "Stairs (Magenta)", (20, h - 20), font, 0.5, (255, 0, 255), 1, cv2.LINE_AA)

    return img
