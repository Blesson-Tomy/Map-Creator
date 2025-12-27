import cv2
import numpy as np
import json

def visualize_combined_floor_plan(json_path, output_img_path):
    """
    Visualize combined floor plan with walls and stairs in different colors.
    
    Args:
        json_path: Path to combined JSON file
        output_img_path: Path to save the output image
    """
    
    # 1. Load Data
    try:
        with open(json_path, 'r') as f:
            segments = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return

    if not segments:
        print("Error: No segments found in JSON.")
        return

    # 2. Setup Canvas
    all_x = []
    all_y = []
    
    for seg in segments:
        all_x.extend([seg['x1'], seg['x2']])
        all_y.extend([seg['y1'], seg['y2']])

    max_x, max_y = max(all_x), max(all_y)
    h, w = max_y + 150, max_x + 150
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background

    # 3. Draw Lines with Type-based Color Coding
    print(f"Drawing {len(segments)} segments...")
    
    walls_count = 0
    stairs_count = 0
    
    for seg in segments:
        pt1 = (seg['x1'], seg['y1'])
        pt2 = (seg['x2'], seg['y2'])
        
        # Determine color based on segment type
        seg_type = seg.get('type', 'unknown')
        
        if seg_type == 'wall':
            color = (0, 150, 255)  # Orange (Walls) - BGR
            walls_count += 1
        elif seg_type == 'stair':
            color = (0, 255, 0)    # Green (Stairs) - BGR
            stairs_count += 1
        else:
            color = (128, 128, 128)  # Gray (Unknown)
            
        cv2.line(img, pt1, pt2, color, 2)

    print(f"  Walls: {walls_count}")
    print(f"  Stairs: {stairs_count}")

    # 4. Draw Vertices and Coordinate Labels
    unique_points = set()
    for seg in segments:
        unique_points.add((seg['x1'], seg['y1']))
        unique_points.add((seg['x2'], seg['y2']))
        
    sorted_points = sorted(list(unique_points), key=lambda p: (p[1], p[0]))
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    print(f"Found {len(sorted_points)} unique vertices.")

    for pt in sorted_points:
        x, y = pt
        
        # Draw Vertex (Red Dot)
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
        
        # Draw Coordinate Label (Black, slightly offset)
        coord_text = f"({x},{y})"
        cv2.putText(img, coord_text, (x + 8, y - 8), font, 0.35, (0, 0, 0), 1, cv2.LINE_AA)

    # 5. Legend
    legend_y = h - 100
    cv2.putText(img, "Legend:", (20, legend_y), font, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    
    cv2.line(img, (20, legend_y + 25), (80, legend_y + 25), (0, 150, 255), 3)
    cv2.putText(img, "Walls (Orange)", (90, legend_y + 30), font, 0.5, (0, 150, 255), 1, cv2.LINE_AA)
    
    cv2.line(img, (20, legend_y + 50), (80, legend_y + 50), (0, 255, 0), 3)
    cv2.putText(img, "Stairs (Green)", (90, legend_y + 55), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    
    cv2.circle(img, (50, legend_y + 75), 4, (0, 0, 255), -1)
    cv2.putText(img, "Vertices (Red dots), Coordinates in Black", (90, legend_y + 80), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # 6. Save
    cv2.imwrite(output_img_path, img)
    print(f"\nVisualization saved to: {output_img_path}")
    print(f"Image size: {w}x{h} pixels")

# Run
visualize_combined_floor_plan('json/first_floor_combined.json', 'images/floor_plan_combined_visualization.jpg')
