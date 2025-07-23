import plotly.graph_objects as go
import numpy as np
from typing import Dict

def mesh_to_plotly(mesh_data: Dict[str, np.ndarray], color='gray', name='Mesh', showlegend=True):
    """Converts mesh data (vertices, triangles) to a Plotly Mesh3d trace."""
    vertices = mesh_data["vertices"]
    triangles = mesh_data["triangles"]

    trace = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=triangles[:, 0],
        j=triangles[:, 1],
        k=triangles[:, 2],
        color=color,
        opacity=0.7,
        name=name,
        hoverinfo='name',
        showlegend=showlegend # FIX: Explicitly control legend visibility
    )
    return trace

def pcd_to_plotly(pcd_data: Dict[str, np.ndarray], name='Point Cloud', showlegend=True):
    """Converts point cloud data (points, colors) to a Plotly Scatter3d trace."""
    points = pcd_data["points"]
    colors = pcd_data["colors"] * 255

    trace = go.Scatter3d(
        x=points[:, 0],
        y=points[:, 1],
        z=points[:, 2],
        mode='markers',
        marker=dict(
            size=2,
            color=colors,
            opacity=0.8
        ),
        name=name,
        hoverinfo='name',
        showlegend=showlegend # FIX: Explicitly control legend visibility
    )
    return trace

def lineset_to_plotly(lineset_data: Dict[str, np.ndarray], color='yellow', name='Centerline', showlegend=True):
    """Converts lineset data (points, lines) to a Plotly Scatter3d trace with lines."""
    points = lineset_data["points"]
    lines = lineset_data["lines"]
    
    x_lines, y_lines, z_lines = [], [], []

    for line in lines:
        p1 = points[line[0]]
        p2 = points[line[1]]
        x_lines.extend([p1[0], p2[0], None])
        y_lines.extend([p1[1], p2[1], None])
        z_lines.extend([p1[2], p2[2], None])

    trace = go.Scatter3d(
        x=x_lines,
        y=y_lines,
        z=z_lines,
        mode='lines',
        line=dict(
            color=color,
            width=5
        ),
        name=name,
        hoverinfo='name',
        showlegend=showlegend # FIX: Explicitly control legend visibility
    )
    return trace
