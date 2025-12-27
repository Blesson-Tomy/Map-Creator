import json
import cv2
import numpy as np

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def visualize_entrances(floor_file, entrances_file, output_image):
    """
    Create visualization showing entrances overlaid on floor plan.
    """
    floor_data = load_json(floor_file)
    entrances_data = load_json(entrances_file)
    
    # Find bounds
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    for seg in floor_data:
        min_x = min(min_x, seg['x1'], seg['x2'])
        max_x = max(max_x, seg['x1'], seg['x2'])
        min_y = min(min_y, seg['y1'], seg['y2'])
        max_y = max(max_y, seg['y1'], seg['y2'])
    
    # Add padding
    padding = 100
    width = int(max_x - min_x + padding * 2)
    height = int(max_y - min_y + padding * 2)
    
    # Create image
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Draw walls and stairs
    for seg in floor_data:
        x1 = int(seg['x1'] - min_x + padding)
        y1 = int(seg['y1'] - min_y + padding)
        x2 = int(seg['x2'] - min_x + padding)
        y2 = int(seg['y2'] - min_y + padding)
        
        if seg['type'] == 'wall':
            # Orange for walls
            cv2.line(img, (x1, y1), (x2, y2), (0, 165, 255), 3)
        else:
            # Green for stairs
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
    
    # Draw entrances
    for entrance in entrances_data['entrances']:
        ex = int(entrance['x'] - min_x + padding)
        ey = int(entrance['y'] - min_y + padding)
        
        # Check if this entrance is part of stairs
        is_stairs = entrance.get('stairs', False)
        
        if is_stairs:
            # Green circle for stair entrances
            cv2.circle(img, (ex, ey), 12, (0, 255, 0), -1)
            text_color = (255, 255, 255)
        else:
            # Blue circle for regular entrances
            cv2.circle(img, (ex, ey), 12, (255, 0, 0), -1)
            text_color = (255, 255, 255)
        
        # Draw ID label
        cv2.putText(img, str(entrance['id']), (ex - 8, ey + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
    
    # Add legend
    cv2.putText(img, f"Entrances: {len(entrances_data['entrances'])}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.line(img, (10, 50), (40, 50), (0, 165, 255), 3)
    cv2.putText(img, "Wall", (45, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    cv2.line(img, (140, 50), (170, 50), (0, 255, 0), 3)
    cv2.putText(img, "Stair", (175, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    cv2.circle(img, (310, 50), 6, (255, 0, 0), -1)
    cv2.putText(img, "Entrance", (320, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    cv2.circle(img, (480, 50), 6, (0, 255, 0), -1)
    cv2.putText(img, "Stair Entrance", (490, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    cv2.imwrite(output_image, img)
    print(f"Saved visualization to {output_image}")
    print(f"Image dimensions: {width}x{height}")
    print(f"Total entrances visualized: {len(entrances_data['entrances'])}")

if __name__ == '__main__':
    visualize_entrances(
        'json/first_floor_combined_with_floors.json',
        'json/first_floor_entrances.json',
        'images/first_floor_entrances_final.jpg'
    )
