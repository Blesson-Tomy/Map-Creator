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
from pipeline_verifycoord import verify_json_coordinates
from pipeline_snap import fix_wall_endpoints, snap_stairs_to_walls

# Page configuration
st.set_page_config(
    page_title="Floor Plan Vectorizer",
    layout="wide"
)

st.title("Floor Plan Vectorizer")

# Initialize session state
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

# Clear any stale session state
if 'verification_img' in st.session_state:
    del st.session_state.verification_img
if 'skeleton_img' in st.session_state:
    del st.session_state.skeleton_img
if 'wall_data' in st.session_state:
    del st.session_state.wall_data
if 'aligned_data' in st.session_state:
    del st.session_state.aligned_data

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    
    floor_number = st.text_input(
        "Floor Number",
        value="1",
        help="e.g., 1, 1.5, 2.5"
    )
    
    st.divider()
    
    # Floor plan / Walls processing
    if not st.session_state.walls_processed:
        st.header("Step 1: Walls")
        st.header("Image Source")
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
        
        st.divider()
        run_walls_button = st.button("Process Walls", use_container_width=True, type="primary", key="walls_btn")
    else:
        st.success("Walls processed ✓")
        st.divider()
        st.header("Step 2: Stairs")
        
        st.header("Image Source")
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
        
        st.divider()
        run_stairs_button = st.button("Process Stairs", use_container_width=True, type="primary", key="stairs_btn")
        process_stairs = True
    
    if st.session_state.stairs_processed:
        st.success("Stairs processed ✓")
        st.divider()
        st.header("Step 3: Snap Stairs to Walls")
        
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
        
        # Store thresholds in session state for access in snapping block (without key params)
        if snap_button:
            st.session_state.snap_endpoint_threshold = endpoint_threshold
            st.session_state.snap_line_threshold = line_threshold



# Process walls
if not st.session_state.walls_processed and 'run_walls_button' in locals() and run_walls_button:
    if not selected_image_path or not os.path.exists(selected_image_path):
        st.error("Please select or upload an image first")
    else:
        try:
            st.session_state.current_floor = floor_number
            
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
            
            progress_bar.progress(75, text="Step 4: Generating verification...")
            
            # Step 4: Verify
            verification_img = verify_json_coordinates(aligned_data)
            if verification_img is None:
                st.error("Failed to generate verification image")
                st.stop()
            
            progress_bar.progress(100, text="Complete")
            st.success("Walls processed successfully")
            
            # Save aligned data for later snapping
            st.session_state.walls_aligned_data = aligned_data
            
            # Save and open image
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/floor_{floor_number}_walls_verification.png"
            cv2.imwrite(output_path, verification_img)
            
            st.session_state.walls_processed = True
            st.session_state.walls_output_path = output_path
            
            # Open in browser
            file_url = os.path.abspath(output_path)
            webbrowser.open(f"file:///{file_url}")
            st.info(f"Walls image opened in browser: {output_path}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Process stairs
if st.session_state.walls_processed and 'run_stairs_button' in locals() and run_stairs_button and 'process_stairs' in locals():
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
            
            progress_bar.progress(75, text="Step 4: Generating verification...")
            
            # Step 4: Verify
            verification_img = verify_json_coordinates(aligned_data)
            if verification_img is None:
                st.error("Failed to generate verification image")
                st.stop()
            
            progress_bar.progress(100, text="Complete")
            st.success("Stairs processed successfully")
            
            # Save aligned data for later snapping
            st.session_state.stairs_aligned_data = aligned_data
            
            # Save and open image
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/floor_{floor_number}_stairs_verification.png"
            cv2.imwrite(output_path, verification_img)
            
            st.session_state.stairs_processed = True
            st.session_state.stairs_output_path = output_path
            
            # Open in browser
            file_url = os.path.abspath(output_path)
            webbrowser.open(f"file:///{file_url}")
            st.info(f"Stairs image opened in browser: {output_path}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Snap stairs to walls
if (st.session_state.walls_processed and st.session_state.stairs_processed and 
    'snap_button' in locals() and snap_button and not st.session_state.snapped):
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
        
        # Display the combined verification image
        st.image(verification_img, channels="BGR", caption="Final Verification: Walls (Green) + Snapped Stairs (Magenta)")
        
        # Open in browser
        file_url = os.path.abspath(output_path)
        webbrowser.open(f"file:///{file_url}")
        st.info(f"Snapped stairs image opened in browser: {output_path}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
