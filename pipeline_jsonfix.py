import json

# --- TUNING ---
GLOBAL_ALIGN_THRESHOLD = 20 
SKEW_TOLERANCE = 15 

def align_walls_globally(lines_data):
    """
    Align walls globally without saving to disk.
    Returns aligned lines list.
    """
    if not lines_data:
        return []
    
    lines = [dict(l) for l in lines_data]  # Deep copy

    # --- STEP 1: GENERATE MASTER GRID ---
    v_x_coords = []
    h_y_coords = []

    skewed_lines_detected = 0

    for line in lines:
        x1, y1, x2, y2 = line['x1'], line['y1'], line['x2'], line['y2']
        
        # Check Vertical (Relaxed Tolerance)
        if abs(x1 - x2) < SKEW_TOLERANCE: 
            v_x_coords.extend([x1, x2])
            h_y_coords.extend([y1, y2])
            
            if abs(x1 - x2) > 0: skewed_lines_detected += 1
            
        # Check Horizontal (Relaxed Tolerance)
        elif abs(y1 - y2) < SKEW_TOLERANCE: 
            h_y_coords.extend([y1, y2])
            v_x_coords.extend([x1, x2])
            
            if abs(y1 - y2) > 0: skewed_lines_detected += 1

    # --- STEP 2: CLUSTER COORDINATES INTO GRID LINES ---
    def get_snap_rules(coords, threshold):
        if not coords: return []
        unique_coords = sorted(list(set(coords)))
        
        clusters = []
        if not unique_coords: return []
        
        current_cluster = [unique_coords[0]]
        
        for i in range(1, len(unique_coords)):
            val = unique_coords[i]
            if val - current_cluster[-1] <= threshold:
                current_cluster.append(val)
            else:
                clusters.append(current_cluster)
                current_cluster = [val]
        clusters.append(current_cluster)
        
        rules = []
        for clust in clusters:
            avg_val = int(round(sum(clust) / len(clust)))
            
            rules.append({
                'min': min(clust) - 2, 
                'max': max(clust) + 2,
                'target': avg_val
            })
        return rules

    x_rules = get_snap_rules(v_x_coords, GLOBAL_ALIGN_THRESHOLD)
    y_rules = get_snap_rules(h_y_coords, GLOBAL_ALIGN_THRESHOLD)

    # --- STEP 3: APPLY GRID SNAPS TO ALL LINES ---
    corrected_count = 0
    
    for line in lines:
        orig_x1, orig_y1 = line['x1'], line['y1']
        orig_x2, orig_y2 = line['x2'], line['y2']
        
        new_x1, new_y1 = orig_x1, orig_y1
        new_x2, new_y2 = orig_x2, orig_y2
        
        # Apply X Snaps
        for r in x_rules:
            if r['min'] <= orig_x1 <= r['max']: new_x1 = r['target']
            if r['min'] <= orig_x2 <= r['max']: new_x2 = r['target']
            
        # Apply Y Snaps
        for r in y_rules:
            if r['min'] <= orig_y1 <= r['max']: new_y1 = r['target']
            if r['min'] <= orig_y2 <= r['max']: new_y2 = r['target']
            
        # Update line if changed
        if (new_x1 != orig_x1) or (new_y1 != orig_y1) or \
           (new_x2 != orig_x2) or (new_y2 != orig_y2):
            line['x1'], line['y1'] = new_x1, new_y1
            line['x2'], line['y2'] = new_x2, new_y2
            corrected_count += 1

    return lines
