import json
import cv2
import numpy as np

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def number_points(input_file, output_image, output_json):
    """
    Extract all unique points from segments, number them sequentially, 
    and create a visualization with labels.
    """
    segments = load_json(input_file)
    
    # Extract unique points
    unique_points = {}
    point_id = 0
    
    for seg in segments:
        p1 = (seg['x1'], seg['y1'])
        p2 = (seg['x2'], seg['y2'])
        
        if p1 not in unique_points:
            unique_points[p1] = point_id
            point_id += 1
        
        if p2 not in unique_points:
            unique_points[p2] = point_id
            point_id += 1
    
    # Find bounds
    points = list(unique_points.keys())
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # Create image
    padding = 100
    width = int(max_x - min_x + padding * 2)
    height = int(max_y - min_y + padding * 2)
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Draw segments
    for seg in segments:
        x1 = int(seg['x1'] - min_x + padding)
        y1 = int(seg['y1'] - min_y + padding)
        x2 = int(seg['x2'] - min_x + padding)
        y2 = int(seg['y2'] - min_y + padding)
        
        color = (0, 165, 255) if seg['type'] == 'wall' else (0, 255, 0)
        cv2.line(img, (x1, y1), (x2, y2), color, 2)
    
    # Draw points with numbers
    for point, point_id in sorted(unique_points.items(), key=lambda x: x[1]):
        x = int(point[0] - min_x + padding)
        y = int(point[1] - min_y + padding)
        
        cv2.circle(img, (x, y), 8, (0, 0, 255), -1)
        cv2.putText(img, str(point_id), (x + 12, y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    cv2.imwrite(output_image, img)
    print(f"Saved numbered points image to {output_image}")
    print(f"Total unique points: {len(unique_points)}")
    
    # Save mapping
    points_mapping = {
        'total_points': len(unique_points),
        'points': {str(pid): {'x': p[0], 'y': p[1]} for p, pid in unique_points.items()}
    }
    save_json(points_mapping, output_json)
    print(f"Saved points mapping to {output_json}")

if __name__ == '__main__':
    number_points(
        'json/floor_2_with_floor_conn_data.json',
        'images/floor_2_numbered_points.jpg',
        'json/floor_2_points_mapping.json'
    )
