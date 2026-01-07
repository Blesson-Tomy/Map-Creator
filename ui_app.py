import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import io
import webbrowser

# Import pipeline modules
from pipeline_skeleton import get_skeleton
from pipeline_vectorize import process_skeleton
from pipeline_jsonfix import align_walls_globally
from pipeline_extend_endpoints import extend_endpoints, visualize_extended_endpoints
from pipeline_verifycoord import verify_json_coordinates
from pipeline_snap import fix_wall_endpoints, snap_stairs_to_walls

# Page configuration
st.set_page_config(
    page_title="Floor Plan Vectorizer",
    layout="wide"
)

# Initialize session state for navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'input'  # 'input', 'walls', 'stairs', 'snap'
if 'current_floor' not in st.session_state:
    st.session_state.current_floor = None
if 'walls_processed' not in st.session_state:
    st.session_state.walls_processed = False
if 'stairs_processed' not in st.session_state:
    st.session_state.stairs_processed = False
if 'walls_output_path' not in st.session_state:
    st.session_state.walls_output_path = None
if 'stairs_output_path' not in st.session_state:
    st.session_state.stairs_output_path = None
if 'walls_aligned_data' not in st.session_state:
    st.session_state.walls_aligned_data = None
if 'stairs_aligned_data' not in st.session_state:
    st.session_state.stairs_aligned_data = None
if 'snapped' not in st.session_state:
    st.session_state.snapped = False

# Define pipeline steps
STEPS = [
    ("Floor Input", "input"),
    ("Walls", "walls"),
    ("Stairs", "stairs"),
    ("Snap", "snap"),
]

def render_timeline():
    """Render the timeline navigation at the top."""
    st.markdown("---")
    
    cols = st.columns(len(STEPS))
    
    for idx, (step_name, step_key) in enumerate(STEPS):
        with cols[idx]:
            # Determine step status
            is_current = st.session_state.current_view == step_key
            is_completed = False
            is_future = False
            
            if step_key == "input":
                is_completed = st.session_state.current_floor is not None
            elif step_key == "walls":
                is_completed = st.session_state.walls_processed
            elif step_key == "stairs":
                is_completed = st.session_state.stairs_processed
            elif step_key == "snap":
                is_completed = st.session_state.snapped
            
            # Determine if step is accessible
            is_accessible = False
            if step_key == "input":
                is_accessible = True
            elif step_key == "walls":
                is_accessible = st.session_state.current_floor is not None
            elif step_key == "stairs":
                is_accessible = st.session_state.walls_processed
            elif step_key == "snap":
                is_accessible = st.session_state.walls_processed and st.session_state.stairs_processed
            
            # Style button based on status
            if is_completed:
                button_color = "🟢"
            elif is_current:
                button_color = "🔵"
            elif is_accessible:
                button_color = "⭕"
            else:
                button_color = "⚪"
            
            if is_accessible:
                if st.button(f"{button_color} {step_name}", use_container_width=True, 
                            key=f"timeline_{step_key}"):
                    st.session_state.current_view = step_key
                    st.rerun()
            else:
                st.button(f"{button_color} {step_name}", use_container_width=True, 
                         disabled=True, key=f"timeline_{step_key}_disabled")
    
    st.markdown("---")

st.title("Floor Plan Vectorizer")

# Render timeline at top
render_timeline()

# Clear any stale session state
if 'verification_img' in st.session_state:
    del st.session_state.verification_img
if 'skeleton_img' in st.session_state:
    del st.session_state.skeleton_img
if 'wall_data' in st.session_state:
    del st.session_state.wall_data
if 'aligned_data' in st.session_state:
    del st.session_state.aligned_data

# ============= FLOOR INPUT VIEW =============
if st.session_state.current_view == 'input':
    st.header("Step 1: Floor Input")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        floor_number = st.text_input(
            "Floor Number",
            value=st.session_state.current_floor or "1",
            help="e.g., 1, 1.5, 2.5"
        )
        if st.button("Set Floor", use_container_width=True, type="primary"):
            st.session_state.current_floor = floor_number
            st.session_state.current_view = 'walls'
            st.rerun()
    
    with col2:
        st.info("👈 Select a floor number and click 'Set Floor' to begin processing walls")

# ============= WALLS VIEW =============
elif st.session_state.current_view == 'walls':
    st.header("Step 2: Process Walls")
    
    st.subheader("Image Source")
    image_source = st.radio(
        "Select source:",
        ["Upload Image", "Use Existing File"],
        key="walls_source"
    )
    
    selected_image_path = None
    
    if image_source == "Upload Image":
        uploaded_file = st.file_uploader(
            "Upload floor plan image",
            type=["jpg", "jpeg", "png", "bmp", "tiff"],
            key="walls_upload"
        )
        if uploaded_file:
            temp_path = f"/tmp/floor_plan_temp.{uploaded_file.name.split('.')[-1]}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_image_path = temp_path
    else:
        image_folder = "images"
        if os.path.exists(image_folder):
            image_files = [f for f in os.listdir(image_folder) 
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))]
            if image_files:
                selected_file = st.selectbox(
                    "Select existing image:",
                    image_files,
                    key="walls_select"
                )
                selected_image_path = os.path.join(image_folder, selected_file)
            else:
                st.warning("No image files found in 'images' folder")
        else:
            st.warning("'images' folder not found")
    
    run_walls_button = st.button("Process Walls", use_container_width=True, type="primary", key="walls_btn")

# ============= STAIRS VIEW =============
elif st.session_state.current_view == 'stairs':
    if not st.session_state.walls_processed:
        st.error("Please complete walls processing first")
    else:
        st.header("Step 3: Process Stairs")
        
        st.subheader("Image Source")
        stairs_source = st.radio(
            "Select source:",
            ["Upload Image", "Use Existing File"],
            key="stairs_source"
        )
        
        stairs_image_path = None
        
        if stairs_source == "Upload Image":
            stairs_uploaded = st.file_uploader(
                "Upload stairs image",
                type=["jpg", "jpeg", "png", "bmp", "tiff"],
                key="stairs_upload"
            )
            if stairs_uploaded:
                temp_path = f"/tmp/stairs_temp.{stairs_uploaded.name.split('.')[-1]}"
                with open(temp_path, "wb") as f:
                    f.write(stairs_uploaded.getbuffer())
                stairs_image_path = temp_path
        else:
            image_folder = "images"
            if os.path.exists(image_folder):
                image_files = [f for f in os.listdir(image_folder) 
                               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))]
                if image_files:
                    stairs_file = st.selectbox(
                        "Select existing image:",
                        image_files,
                        key="stairs_select"
                    )
                    stairs_image_path = os.path.join(image_folder, stairs_file)
                else:
                    st.warning("No image files found in 'images' folder")
            else:
                st.warning("'images' folder not found")
        
        run_stairs_button = st.button("Process Stairs", use_container_width=True, type="primary", key="stairs_btn")

# ============= SNAP VIEW =============
elif st.session_state.current_view == 'snap':
    if not st.session_state.walls_processed or not st.session_state.stairs_processed:
        st.error("Please complete walls and stairs processing first")
    else:
        st.header("Step 4: Snap Stairs to Walls")
        
        col1, col2 = st.columns(2)
        with col1:
            endpoint_threshold = st.slider(
                "Endpoint Snap Threshold (px)",
                min_value=10.0,
                max_value=100.0,
                value=50.0,
                step=5.0,
                help="Distance threshold for snapping to wall endpoints"
            )
        
        with col2:
            line_threshold = st.slider(
                "Line Snap Threshold (px)",
                min_value=5.0,
                max_value=50.0,
                value=30.0,
                step=2.5,
                help="Distance threshold for snapping to wall lines"
            )
        
        snap_button = st.button("Snap Stairs to Walls", use_container_width=True, type="primary", key="snap_btn")
        
        # Store thresholds in session state for access in snapping block
        if snap_button:
            st.session_state.snap_endpoint_threshold = endpoint_threshold
            st.session_state.snap_line_threshold = line_threshold


# ============= PROCESSING LOGIC =============

# Process walls
if st.session_state.current_view == 'walls' and 'run_walls_button' in locals() and run_walls_button:
    if not selected_image_path or not os.path.exists(selected_image_path):
        st.error("Please select or upload an image first")
    else:
        try:
            progress_bar = st.progress(0, text="Step 1: Extracting skeleton...")
            
            # Step 1: Skeleton
            original_img, skeleton_img = get_skeleton(selected_image_path)
            if skeleton_img is None:
                st.error("Failed to extract skeleton")
                st.stop()
            
            progress_bar.progress(25, text="Step 2: Vectorizing lines...")
            
            # Step 2: Vectorize
            wall_data = process_skeleton(skeleton_img)
            if wall_data is None or len(wall_data['walls']) == 0:
                st.error("Failed to vectorize")
                st.stop()
            
            progress_bar.progress(50, text="Step 3: Aligning walls...")
            
            # Step 3: Align
            json_lines = [
                {"x1": int(line[0]), "y1": int(line[1]), 
                 "x2": int(line[2]), "y2": int(line[3])}
                for line in wall_data['walls']
            ]
            aligned_data = align_walls_globally(json_lines)
            if not aligned_data:
                st.error("Failed to align walls")
                st.stop()
            
            progress_bar.progress(60, text="Step 4: Extending endpoints...")
            
            # Step 4: Extend free endpoints to nearby walls
            original_aligned = [dict(d) for d in aligned_data]  # Keep original for visualization
            extended_data = extend_endpoints(aligned_data, snap_distance=50.0)
            if not extended_data:
                st.error("Failed to extend endpoints")
                st.stop()
            
            progress_bar.progress(75, text="Step 5: Generating verification...")
            
            # Step 5: Verify
            verification_img = verify_json_coordinates(extended_data)
            if verification_img is None:
                st.error("Failed to generate verification image")
                st.stop()
            
            progress_bar.progress(100, text="Complete")
            st.success("Walls processed successfully")
            
            # Save extended data for later snapping
            st.session_state.walls_aligned_data = extended_data
            
            # Save and open image
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/floor_{st.session_state.current_floor}_walls_verification.png"
            cv2.imwrite(output_path, verification_img)
            
            st.session_state.walls_processed = True
            st.session_state.walls_output_path = output_path
            
            # Save JSON output
            import json
            os.makedirs("json", exist_ok=True)
            json_output_path = f"json/floor_{st.session_state.current_floor}_walls.json"
            with open(json_output_path, "w") as f:
                json.dump(extended_data, f, indent=2)
            
            # Display output files section
            st.divider()
            st.subheader("📁 Output Files")
            
            col1, col2 = st.columns(2)
            
            # Image output
            with col1:
                st.write("**Image (PNG)**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.code(os.path.abspath(output_path), language="text")
                with col_b:
                    if st.button("📋 Copy", key="copy_walls_img"):
                        st.toast("Path copied!")
            
            # JSON output
            with col2:
                st.write("**Data (JSON)**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.code(os.path.abspath(json_output_path), language="text")
                with col_b:
                    if st.button("📋 Copy", key="copy_walls_json"):
                        st.toast("Path copied!")
            
            # Display image and JSON preview
            st.divider()
            st.subheader("📊 Verification Image")
            st.image(verification_img, channels="BGR", caption="Walls with Extended Endpoints")
            
            st.divider()
            st.subheader("📋 JSON Preview")
            with st.expander("Show first 10 lines of JSON data"):
                lines = json.dumps(extended_data[:min(3, len(extended_data))], indent=2).split('\n')
                st.code('\n'.join(lines[:15]) + "...", language="json")
            
            file_url = os.path.abspath(output_path)
            webbrowser.open(f"file:///{file_url}")
            st.success("✅ Walls processed successfully!")
            st.info("📌 Both image and JSON files have been saved. Click the Stairs button in the timeline above to continue.")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Process stairs
if st.session_state.current_view == 'stairs' and st.session_state.walls_processed and 'run_stairs_button' in locals() and run_stairs_button:
    if not stairs_image_path or not os.path.exists(stairs_image_path):
        st.error("Please select or upload a stairs image first")
    else:
        try:
            progress_bar = st.progress(0, text="Step 1: Extracting skeleton...")
            
            # Step 1: Skeleton
            original_img, skeleton_img = get_skeleton(stairs_image_path)
            if skeleton_img is None:
                st.error("Failed to extract skeleton")
                st.stop()
            
            progress_bar.progress(25, text="Step 2: Vectorizing lines...")
            
            # Step 2: Vectorize
            stair_data = process_skeleton(skeleton_img)
            if stair_data is None or len(stair_data['walls']) == 0:
                st.error("Failed to vectorize")
                st.stop()
            
            progress_bar.progress(50, text="Step 3: Aligning stairs...")
            
            # Step 3: Align
            json_lines = [
                {"x1": int(line[0]), "y1": int(line[1]), 
                 "x2": int(line[2]), "y2": int(line[3])}
                for line in stair_data['walls']
            ]
            aligned_data = align_walls_globally(json_lines)
            if not aligned_data:
                st.error("Failed to align stairs")
                st.stop()
            
            progress_bar.progress(60, text="Step 4: Extending endpoints...")
            
            # Step 4: Extend free endpoints to nearby walls
            extended_data = extend_endpoints(aligned_data, snap_distance=50.0)
            if not extended_data:
                st.error("Failed to extend endpoints")
                st.stop()
            
            progress_bar.progress(75, text="Step 5: Generating verification...")
            
            # Step 5: Verify
            verification_img = verify_json_coordinates(extended_data)
            if verification_img is None:
                st.error("Failed to generate verification image")
                st.stop()
            
            progress_bar.progress(100, text="Complete")
            st.success("Stairs processed successfully")
            
            # Save extended data for later snapping
            st.session_state.stairs_aligned_data = extended_data
            
            # Save and open image
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/floor_{st.session_state.current_floor}_stairs_verification.png"
            cv2.imwrite(output_path, verification_img)
            
            st.session_state.stairs_processed = True
            st.session_state.stairs_output_path = output_path
            
            # Save JSON output
            os.makedirs("json", exist_ok=True)
            json_output_path = f"json/floor_{st.session_state.current_floor}_stairs.json"
            with open(json_output_path, "w") as f:
                json.dump(extended_data, f, indent=2)
            
            # Display output files section
            st.divider()
            st.subheader("📁 Output Files")
            
            col1, col2 = st.columns(2)
            
            # Image output
            with col1:
                st.write("**Image (PNG)**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.code(os.path.abspath(output_path), language="text")
                with col_b:
                    if st.button("📋 Copy", key="copy_stairs_img"):
                        st.toast("Path copied!")
            
            # JSON output
            with col2:
                st.write("**Data (JSON)**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.code(os.path.abspath(json_output_path), language="text")
                with col_b:
                    if st.button("📋 Copy", key="copy_stairs_json"):
                        st.toast("Path copied!")
            
            # Display image and JSON preview
            st.divider()
            st.subheader("📊 Verification Image")
            st.image(verification_img, channels="BGR", caption="Stairs with Extended Endpoints")
            
            st.divider()
            st.subheader("📋 JSON Preview")
            with st.expander("Show first 10 lines of JSON data"):
                lines = json.dumps(extended_data[:min(3, len(extended_data))], indent=2).split('\n')
                st.code('\n'.join(lines[:15]) + "...", language="json")
            
            file_url = os.path.abspath(output_path)
            webbrowser.open(f"file:///{file_url}")
            st.success("✅ Stairs processed successfully!")
            st.info("📌 Both image and JSON files have been saved. Click the Snap button in the timeline above to continue.")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Snap stairs to walls
if st.session_state.current_view == 'snap' and 'snap_button' in locals() and snap_button and not st.session_state.snapped:
    try:
        progress_bar = st.progress(0, text="Snapping stairs to walls...")
        
        # Get thresholds from session state
        endpoint_threshold = st.session_state.get('snap_endpoint_threshold', 50.0)
        line_threshold = st.session_state.get('snap_line_threshold', 30.0)
        
        # Snap stairs to original walls without modifying wall structure
        snapped_stairs = snap_stairs_to_walls(
            st.session_state.stairs_aligned_data,
            st.session_state.walls_aligned_data,
            endpoint_threshold=endpoint_threshold,
            line_threshold=line_threshold
        )
        
        progress_bar.progress(75, text="Generating verification...")
        
        # Step 3: Verify - Show walls and stairs together
        verification_img = verify_json_coordinates(st.session_state.walls_aligned_data, snapped_stairs)
        if verification_img is None:
            st.error("Failed to generate verification image")
            st.stop()
        
        progress_bar.progress(100, text="Complete")
        st.success("Stairs snapped to walls successfully")
        
        # Save snapped image
        os.makedirs("outputs", exist_ok=True)
        output_path = f"outputs/floor_{st.session_state.current_floor}_stairs_snapped_verification.png"
        cv2.imwrite(output_path, verification_img)
        
        st.session_state.snapped = True
        
        # Save ONLY the snapped stairs JSON (walls don't change during snapping)
        os.makedirs("json", exist_ok=True)
        stairs_json_path = f"json/floor_{st.session_state.current_floor}_stairs_snapped.json"
        
        with open(stairs_json_path, "w") as f:
            json.dump(snapped_stairs, f, indent=2)
        
        # Display output files section
        st.divider()
        st.subheader("📁 Output Files")
        
        col1, col2 = st.columns(2)
        
        # Image output
        with col1:
            st.write("**Image (PNG)**")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.code(os.path.abspath(output_path), language="text")
            with col_b:
                if st.button("📋 Copy", key="copy_snap_img"):
                    st.toast("Path copied!")
        
        # JSON output (only stairs, walls are unchanged)
        with col2:
            st.write("**Data (JSON)**")
            st.caption("Snapped Stairs Only")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.code(os.path.abspath(stairs_json_path), language="text")
            with col_b:
                if st.button("📋 Copy", key="copy_snap_stairs_json"):
                    st.toast("Path copied!")
        
        # Display image and JSON preview
        st.divider()
        st.subheader("📊 Verification Image")
        st.image(verification_img, channels="BGR", caption="Final Verification: Walls (Green) + Snapped Stairs (Magenta)")
        
        st.divider()
        st.subheader("📋 JSON Preview")
        with st.expander("Show snapped stairs data (first 3 segments)"):
            lines = json.dumps(snapped_stairs[:min(3, len(snapped_stairs))], indent=2).split('\n')
            st.code('\n'.join(lines[:20]) + "...", language="json")
        
        # Open in browser
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        st.success("✅ Snapping completed successfully!")
        st.info("📌 Snapped stairs JSON has been saved. Walls JSON remains unchanged from walls processing step.")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
