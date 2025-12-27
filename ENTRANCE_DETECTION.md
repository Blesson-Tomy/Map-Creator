# Entrance Detection System

## Overview
The entrance detection system identifies all doors, passages, and openings in the floor plan by analyzing wall/stair endpoints and their surroundings.

## How It Works

### Algorithm
1. **Identify Edge Endpoints**: Find all segment endpoints that appear in only one segment (dead ends)
2. **Extend Perpendicular**: For each edge endpoint, extend lines perpendicular to the segment (90° and 270°)
3. **Find Intersections**: Check if the extended lines intersect with other walls/stairs within a gap distance threshold
4. **Filter Gaps**: Only accept openings between 5-200 pixels (configurable) to avoid noise
5. **Calculate Midpoint**: Store the midpoint between the endpoint and intersection point as the entrance location

### Key Parameters
- **max_gap_distance** (default 200px): Maximum distance to search for connecting walls
  - Filters out large gaps that aren't real openings
  - Larger values = find more distant connections
  - Smaller values = focus on immediate door openings

### Output Structure
Each entrance has:
- `id`: Unique identifier
- `endpoint`: The wall/stair endpoint where gap starts
- `connected_to`: The wall/stair that the gap connects to
- `gap_distance`: Distance of the opening (in pixels)
- `midpoint`: Center point of the opening (for navigation/AR)
- `segment`: Information about the segment with the endpoint
  - `id`: Segment index
  - `type`: "wall" or "stair"
  - `floors_connected`: Which floors this segment connects
- `connects_to_segment`: Information about the connected wall/stair
  - Same structure as above

## Use Cases

### Navigation
- **Path Planning**: Use entrance midpoints as waypoints for navigation algorithms
- **Room Connectivity**: Determine which rooms are accessible from each other
- **Floor Transitions**: Identify stairwells and transitions between floor levels

### Error Correction
- **Duplicate Detection**: Identify impossible openings (wall gaps that shouldn't exist)
- **Missing Walls**: Large gaps (> 200px) might indicate missing wall data
- **Misaligned Segments**: Inconsistent gap distances suggest alignment issues

### Visualization
- **Floor Plan Validation**: Visual inspection of all detected openings
- **Quality Control**: Verify no spurious openings were detected

## Files Generated

### Primary Output
- `json/first_floor_entrances.json` - Complete entrance/exit data with metadata

### Visualization
- `images/first_floor_entrances_visualization.jpg` - Visual map showing:
  - Orange lines: Walls
  - Green lines: Stairs
  - Blue dots: Entrance/exit midpoints
  - Entrance count labels on segments

## Configuration

### Running the Detection
```python
python detect_entrances.py
```

Default settings:
- Input: `json/first_floor_combined_with_floors.json`
- Output: `json/first_floor_entrances.json`
- Max gap distance: 200 pixels
- Extension length: 5000 pixels (search radius)

### Tuning for Your Floor Plan

**To find more entrances** (less strict):
- Increase `max_gap_distance` to 300-400 pixels
- Catches more distant or larger openings

**To find fewer entrances** (stricter):
- Decrease `max_gap_distance` to 50-100 pixels
- Only catches immediate, obvious openings

**Modify in `detect_entrances.py`**:
```python
find_entrances(input_file, output_file, extension_length=5000, max_gap_distance=200)
```

## Statistics for First Floor
- Total edge endpoints: 75
- Detected entrances: 84
- Average gap distance: ~50 pixels
- Entrances per stair/wall segment: 1-3

## Next Steps
1. Review `first_floor_entrances_visualization.jpg` to verify accuracy
2. Adjust `max_gap_distance` if too many/few entrances are detected
3. Use entrance midpoints in your navigation/AR system
4. Apply same logic to second and third floor files
5. Create master entrance list combining all floors with floor IDs
