import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import time
import tempfile
import os
from typing import Dict

# Import your custom modules
# Make sure these files (analysis_pipeline.py, visualization_utils.py) exist and are correct
from analysis_pipeline import enhanced_vessel_reconstruction_analysis, AnalysisResult
from visualization_utils import (
    mesh_to_plotly,
    pcd_to_plotly,
    lineset_to_plotly,
)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Vessel Geometry Analysis",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CONSTANTS ---
BASE_DATA_DIR = Path("./outputs")

# --- HELPER FUNCTIONS ---
@st.cache_data
def find_patient_scans(base_dir: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Scans the new directory structure to find patients and their associated scans.
    For each patient, it finds all available scans by matching filenames across
    nifti, segmentation, and point cloud directories.

    Returns a nested dictionary:
    {
        patient_id: {
            scan_name: {
                "nifti": path,
                "seg": path,
                "pcd": path
            },
            ...
        },
        ...
    }
    """
    patient_scan_data = {}
    
    # Updated directory names to match the new structure
    nifti_dir = base_dir / "nifti_data"
    seg_dir = base_dir / "processed_segmentations"
    pcd_dir = base_dir / "pointclouds"

    if not all([nifti_dir.is_dir(), seg_dir.is_dir(), pcd_dir.is_dir()]):
        st.sidebar.error(f"One or more required base directories not found in '{base_dir}'.")
        return {}

    # Find patients based on subdirectories in the nifti_data folder
    patient_ids = [p.name for p in nifti_dir.iterdir() if p.is_dir()]

    for pid in sorted(patient_ids):
        patient_scans = {}
        patient_nifti_dir = nifti_dir / pid
        
        # Iterate through NIfTI files as the source of truth for scans
        nifti_files = list(patient_nifti_dir.glob("*.nii*"))

        for nifti_file in nifti_files:
            # The scan name is the filename without the extension(s)
            # This handles both .nii and .nii.gz
            scan_name = nifti_file.name.replace(".nii.gz", "").replace(".nii", "")
            
            # Construct expected paths for other files based on the scan name
            seg_file = seg_dir / pid / f"{scan_name}.npz"
            pcd_file = pcd_dir / pid / f"{scan_name}.npz"

            # If all three corresponding files exist, it's a valid scan set
            if seg_file.exists() and pcd_file.exists():
                patient_scans[scan_name] = {
                    "nifti": str(nifti_file),
                    "seg": str(seg_file),
                    "pcd": str(pcd_file),
                }

        if patient_scans:
            patient_scan_data[pid] = patient_scans
        else:
            st.sidebar.warning(f"No complete scan sets found for patient `{pid}`.")
            
    return patient_scan_data

# --- CACHED ANALYSIS FUNCTION ---
@st.cache_data(show_spinner=False, max_entries=3)
def run_analysis(
    nifti_path: str, seg_path: str, pcd_path: str, patient_id: str, 
    nifti_mtime: float, seg_mtime: float, pcd_mtime: float
):
    """
    Wrapper around the main analysis function, cached based on file paths
    and their modification times to detect content changes.
    Cache will store up to 10 results and discard the least recently used.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        status_container = st.empty()
        def status_callback(message):
            status_container.status(f"`{message}`", expanded=True)

        results = enhanced_vessel_reconstruction_analysis(
            scan_nifti_file=nifti_path,
            segmentation_file=seg_path,
            pointcloud_file=pcd_path,
            destination_folder=temp_dir_path,
            patient_id=patient_id,
            status_callback=status_callback,
        )

        for vessel_name, data in results.get("vessels", {}).items():
            if plot_path_str := data.get("diameter_plot_path"):
                plot_path = Path(plot_path_str)
                if plot_path.exists():
                    with open(plot_path, "rb") as f:
                        data["diameter_plot_bytes"] = f.read()
                else:
                    data["diameter_plot_bytes"] = None
        
        status_container.empty()
        return results

# --- Plotting Helper Function ---
def create_plot(traces, title):
    """Creates a Plotly figure with a standardized layout."""
    if not traces:
        st.warning(f"No data to display for: {title}.")
        return

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis=dict(title="X (mm)"), yaxis=dict(title="Y (mm)"), zaxis=dict(title="Z (mm)"),
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True, height=700)

# --- UI RENDERING ---
st.title("🔬 Vessel Geometry Analysis & 3D Reconstruction")

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = None
if "selected_patient_id" not in st.session_state:
    st.session_state.selected_patient_id = None
if "selected_scan_name" not in st.session_state:
    st.session_state.selected_scan_name = None

# --- Sidebar ---
with st.sidebar:
    st.header("1. Select Data")
    
    if not BASE_DATA_DIR.exists():
        st.error(f"Base data directory not found: '{BASE_DATA_DIR}'. Please ensure it exists.")
        st.stop()
    
    patient_scan_data = find_patient_scans(BASE_DATA_DIR)
    
    if not patient_scan_data:
        st.error(f"No valid patient data found in '{BASE_DATA_DIR}'. Please check the directory structure.")
        st.stop()
        
    patient_ids = list(patient_scan_data.keys())
    selected_patient_id = st.selectbox("Select Patient", patient_ids, key="sb_patient")

    selected_scan_name = None
    if selected_patient_id:
        available_scans = list(patient_scan_data[selected_patient_id].keys())
        if available_scans:
            selected_scan_name = st.selectbox("Select Scan", available_scans, key="sb_scan")
        else:
            st.warning("This patient has no complete scans available.")

    run_button = st.button(
        "Run Analysis",
        type="primary",
        disabled=not (selected_patient_id and selected_scan_name),
    )

    st.markdown("---")
    st.header("Cache Options")
    if st.button("Clear Analysis Cache & Reset"):
        st.cache_data.clear()
        st.session_state.clear()
        st.success("Cache cleared! App has been reset.")
        time.sleep(2) 
        st.rerun()

# --- Main App Logic ---
if run_button and selected_patient_id and selected_scan_name:
    # Store selections in session state to persist them across reruns
    st.session_state.selected_patient_id = selected_patient_id
    st.session_state.selected_scan_name = selected_scan_name
    
    patient_files = patient_scan_data[selected_patient_id][selected_scan_name]
    
    nifti_path = patient_files['nifti']
    seg_path = patient_files['seg']
    pcd_path = patient_files['pcd']
    
    with st.spinner("Starting analysis... This may take a few moments."):
        nifti_mtime = os.path.getmtime(nifti_path)
        seg_mtime = os.path.getmtime(seg_path)
        pcd_mtime = os.path.getmtime(pcd_path)
        
        analysis_id = f"{selected_patient_id}_{selected_scan_name}"
        
        st.session_state.results = run_analysis(
            nifti_path, seg_path, pcd_path, analysis_id,
            nifti_mtime, seg_mtime, pcd_mtime
        )
    st.rerun()

if st.session_state.results:
    results: AnalysisResult = st.session_state.results
    colors = {"Aorta": "red", "Left Iliac Artery": "green", "Right Iliac Artery": "blue"}
    
    display_patient_id = st.session_state.get("selected_patient_id", "N/A")
    display_scan_name = st.session_state.get("selected_scan_name", "N/A")
    
    st.header(f"3D Interactive Viewer: {display_patient_id} ({display_scan_name})")
    
    tab_list = ["Point Cloud View", "Centerline View", "Mesh View"]
    tab_pcd, tab_centerline, tab_mesh = st.tabs(tab_list)

    # Prepare traces for each view
    mesh_traces, centerline_traces, pcd_traces = [], [], []
    
    if "point_cloud" in results:
        pcd_data = results["point_cloud"]
        if pcd_data and pcd_data.get("geometry"):
            pcd_traces.append(pcd_to_plotly(pcd_data["geometry"], "Point Cloud", showlegend=True))

    for vessel_name, data in results.get("vessels", {}).items():
        color = colors.get(vessel_name, "gray")
        if data.get("mesh"):
            mesh_traces.append(mesh_to_plotly(data["mesh"], color=color, name=f"{vessel_name} Mesh", showlegend=True))
        if data.get("centerline"):
            centerline_traces.append(lineset_to_plotly(data["centerline"], color="yellow", name=f"{vessel_name} Centerline", showlegend=True))
        if data.get("max_diameter_disc"):
            centerline_traces.append(mesh_to_plotly(data["max_diameter_disc"], color="magenta", name=f"{vessel_name} Max Diameter", showlegend=True))

    with tab_pcd:
        create_plot(pcd_traces, "Point Cloud View")
    with tab_centerline:
        create_plot(centerline_traces, "Centerline View")
    with tab_mesh:
        create_plot(mesh_traces, "Mesh View")

    st.markdown("---")
    st.header(f"Analysis Results: {display_patient_id} ({display_scan_name})")
    for vessel_name, data in results.get("vessels", {}).items():
        with st.expander(f"**{vessel_name}** Metrics", expanded=True):
            metrics = data.get("metrics", {})
            if not metrics:
                st.warning("No metrics computed for this vessel.")
                continue

            cols = st.columns(3); cols[0].metric("Surface Area (mm²)", f"{metrics.get('surface_area', 0):.2f}"); cols[1].metric("Volume (mm³)", f"{metrics.get('volume', 0):.2f}"); cols[2].metric("Watertight", "✅ Yes" if metrics.get('is_watertight') else "❌ No")

            if "centerline" in metrics:
                cl_metrics = metrics["centerline"]
                cols = st.columns(3); cols[0].metric("Vessel Length (mm)", f"{cl_metrics.get('length', 0):.2f}"); cols[1].metric("Max Diameter (mm)", f"{cl_metrics.get('diameters', {}).get('max', 0):.2f}"); cols[2].metric("Tortuosity", f"{cl_metrics.get('tortuosity', 0):.3f}")
            
            if data.get("diameter_plot_bytes"):
                st.image(data["diameter_plot_bytes"], caption=f"{vessel_name} Diameter Profile")
else:
    st.info("Select a patient and scan from the sidebar, then click 'Run Analysis' to begin.")