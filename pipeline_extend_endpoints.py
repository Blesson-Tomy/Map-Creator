import cv2
import numpy as np
from typing import List, Dict, Tuple

def find_line_intersection(x1, y1, x2, y2, px, py, keep_axis='x', clamp_to_segment=False) -> Tuple[int, int]:
    """
    Find where a line (x1,y1)-(x2,y2) should intersect by moving only along one axis.
    
    Args:
        x1, y1, x2, y2: The line to snap to
        px, py: The point to snap
        keep_axis: 'x' to keep x constant and find y, or 'y' to keep y constant and find x
        clamp_to_segment: If True, clamp to segment bounds. If False, use infinite line.
    
    Returns:
        Tuple of (new_x, new_y)
    """
    dx = x2 - x1
    dy = y2 - y1
    
    # Avoid division by zero
    if dx == 0 and dy == 0:
        return (px, py)
    
    if keep_axis == 'x':
        # Keep x constant, find y on the line
        if dy == 0:
            # Target line is horizontal, can't intersect by changing y
            return (px, py)
        # Line equation: (x-x1)/dx = (y-y1)/dy
        # With x = px: (px-x1)/dx = (y-y1)/dy
        # Solve for y: y = y1 + (px-x1) * dy/dx
        if dx != 0:
            t = (px - x1) / dx
        else:
            # dx is 0, line is vertical, use closest point
            t = 0
        
        if clamp_to_segment:
            t = max(0, min(1, t))
        
        new_x = x1 + t * dx
        new_y = y1 + t * dy
        return (int(round(new_x)), int(round(new_y)))
    else:  # keep_axis == 'y'
        # Keep y constant, find x on the line
        if dx == 0:
            # Target line is vertical, can't intersect by changing x
            return (px, py)
        # Line equation: (x-x1)/dx = (y-y1)/dy
        # With y = py: (x-x1)/dx = (py-y1)/dy
        # Solve for x: x = x1 + (py-y1) * dx/dy
        if dy != 0:
            t = (py - y1) / dy
        else:
            # dy is 0, line is horizontal, use closest point
            t = 0
        
        if clamp_to_segment:
            t = max(0, min(1, t))
        
        new_x = x1 + t * dx
        new_y = y1 + t * dy
        return (int(round(new_x)), int(round(new_y)))

def extend_endpoints(lines_data: List[Dict], snap_distance: float = 50.0) -> List[Dict]:
    """
    Extend free line endpoints to nearby walls/lines while preserving verticality/horizontality.
    
    A free endpoint is one that's not shared with another line.
    
    Args:
        lines_data: List of line segments with x1, y1, x2, y2
        snap_distance: Maximum distance to consider a line as "nearby" (pixels)
    
    Returns:
        Modified lines_data with extended endpoints
    """
    if not lines_data:
        return lines_data
    
    # Deep copy
    lines = [dict(line) for line in lines_data]
    
    # Count endpoint usage
    endpoint_count = {}
    for line_idx, line in enumerate(lines):
        p1 = (line['x1'], line['y1'])
        p2 = (line['x2'], line['y2'])
        
        if p1 not in endpoint_count:
            endpoint_count[p1] = []
        if p2 not in endpoint_count:
            endpoint_count[p2] = []
        
        endpoint_count[p1].append((line_idx, 'start'))
        endpoint_count[p2].append((line_idx, 'end'))
    
    # Find free endpoints (used by only 1 line)
    free_endpoints = {pt: uses for pt, uses in endpoint_count.items() if len(uses) == 1}
    
    print(f"Found {len(free_endpoints)} free endpoints out of {len(endpoint_count)} total")
    
    # Process each free endpoint
    modifications = 0
    for endpoint, uses in free_endpoints.items():
        line_idx, pos = uses[0]
        line = lines[line_idx]
        
        if pos == 'start':
            px, py = line['x1'], line['y1']
            other_x, other_y = line['x2'], line['y2']
        else:
            px, py = line['x2'], line['y2']
            other_x, other_y = line['x1'], line['y1']
        
        # Determine if this line is mostly vertical or horizontal
        dx = other_x - px
        dy = other_y - py
        is_vertical = abs(dx) < abs(dy)
        is_horizontal = abs(dy) < abs(dx)
        
        # Search for nearby lines to snap to
        best_snap = None
        best_dist = snap_distance
        best_line_idx = None
        keep_axis = None
        
        for other_idx, other_line in enumerate(lines):
            if other_idx == line_idx:
                continue
            
            # Check distance from endpoint to the other line
            x1, y1 = other_line['x1'], other_line['y1']
            x2, y2 = other_line['x2'], other_line['y2']
            
            # Distance from point to line segment
            dx_seg = x2 - x1
            dy_seg = y2 - y1
            
            if dx_seg == 0 and dy_seg == 0:
                continue
            
            length_sq = dx_seg**2 + dy_seg**2
            t = max(0, min(1, ((px - x1) * dx_seg + (py - y1) * dy_seg) / length_sq))
            closest_x = x1 + t * dx_seg
            closest_y = y1 + t * dy_seg
            
            dist = ((px - closest_x)**2 + (py - closest_y)**2) ** 0.5
            
            if dist < best_dist:
                best_dist = dist
                best_snap = (closest_x, closest_y)
                best_line_idx = other_idx
                
                # Determine which axis to keep
                if is_vertical:
                    keep_axis = 'x'  # Keep x, find y on nearby line
                elif is_horizontal:
                    keep_axis = 'y'  # Keep y, find x on nearby line
                else:
                    # Diagonal line, snap to nearest point
                    keep_axis = None
        
        # Apply snap if found
        if best_snap is not None and best_line_idx is not None:
            other_line = lines[best_line_idx]
            
            if keep_axis is not None:
                # For vertical/horizontal lines, constrain movement to infinite line
                # Use clamp_to_segment=False to allow snapping beyond segment bounds
                new_pos = find_line_intersection(
                    other_line['x1'], other_line['y1'],
                    other_line['x2'], other_line['y2'],
                    px, py,
                    keep_axis=keep_axis,
                    clamp_to_segment=False  # Allow snapping to infinite line, not just segment
                )
            else:
                # For diagonal lines, snap to nearest point on target segment
                # Clamp to segment for diagonal lines
                new_pos = best_snap
            
            if pos == 'start':
                old_pos = (line['x1'], line['y1'])
                line['x1'] = int(new_pos[0])
                line['y1'] = int(new_pos[1])
            else:
                old_pos = (line['x2'], line['y2'])
                line['x2'] = int(new_pos[0])
                line['y2'] = int(new_pos[1])
            
            modifications += 1
            line_type = "vertical" if is_vertical else ("horizontal" if is_horizontal else "diagonal")
            print(f"  Line {line_idx} ({line_type}): Extended endpoint {old_pos} -> {new_pos} (dist: {best_dist:.1f}px)")
    
    print(f"\nExtended {modifications} free endpoints")
    return lines

def visualize_extended_endpoints(lines_data: List[Dict], original_lines_data: List[Dict] = None) -> np.ndarray:
    """
    Visualize the extended endpoints with before/after comparison if original provided.
    
    Args:
        lines_data: Modified line segments
        original_lines_data: Original line segments before extension (optional)
    
    Returns:
        Visualization image as numpy array
    """
    if not lines_data:
        return None
    
    # Get canvas size
    all_x = []
    all_y = []
    
    for line in lines_data:
        all_x.extend([line['x1'], line['x2']])
        all_y.extend([line['y1'], line['y2']])
    
    if not all_x or not all_y:
        return None
    
    max_x = max(all_x)
    max_y = max(all_y)
    h, w = max_y + 150, max_x + 150
    
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background
    
    # Draw original lines in light gray if provided
    if original_lines_data:
        for line in original_lines_data:
            pt1 = (line['x1'], line['y1'])
            pt2 = (line['x2'], line['y2'])
            cv2.line(img, pt1, pt2, (200, 200, 200), 1)  # Light gray for original
    
    # Draw modified lines in blue
    for line in lines_data:
        pt1 = (line['x1'], line['y1'])
        pt2 = (line['x2'], line['y2'])
        cv2.line(img, pt1, pt2, (0, 150, 200), 2)  # Blue for extended
    
    # Draw all endpoints as circles
    all_points = set()
    for line in lines_data:
        all_points.add((line['x1'], line['y1']))
        all_points.add((line['x2'], line['y2']))
    
    for pt in all_points:
        cv2.circle(img, pt, 3, (0, 0, 255), -1)  # Red circles for endpoints
    
    # Add legend
    font = cv2.FONT_HERSHEY_SIMPLEX
    if original_lines_data:
        cv2.putText(img, "Original (Gray)", (20, h - 40), font, 0.5, (200, 200, 200), 1)
        cv2.putText(img, "Extended (Blue)", (20, h - 20), font, 0.5, (0, 150, 200), 1)
    else:
        cv2.putText(img, "Extended Endpoints (Blue)", (20, h - 20), font, 0.5, (0, 150, 200), 1)
    
    return img
