import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import open3d as o3d
import os

def plot_diameter(diameters, output_dir, name, slice_ids=None):
    """
    Plot diameter over vessel's centerline and save it to a file.

    Args:
        diameters: np.array, diameter across the centerline
        output_dir: str folder where to save the plot
        name: str, name of the vessel
        slice_ids: np.array, id for each diameter measure
    """
    plt.figure(figsize=(10, 4))
    if slice_ids is None:
        plt.plot(np.arange(len(diameters)), diameters, "-o")
    else:
        plt.plot(slice_ids, diameters, "-o")

    if slice_ids is None:
        plt.xlabel("Centerline point index")
    else:
        plt.xlabel("Slice coordinate")
    plt.ylabel("Diameter (mm)")
    plt.title(f"{name} Diameter Along Centerline")
    plt.grid(True)
    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    entire_file_path = Path(output_dir) / f"{'_'.join(name.split(' '))}.png"
    plt.savefig(
        entire_file_path, dpi=200
    )
    # The plot is closed to free up memory and prevent it from being displayed
    # in non-interactive environments.
    plt.close()
    return entire_file_path


def create_flat_disc(center, radius, normal, resolution=60):
    """
    Create a flat disc mesh centered at `center`, perpendicular to `normal`,
    with the specified `radius` and triangle resolution.

    Args:
        center: coordinates where to center the disk
        radius: disc radius
        normal: vector to which the disc should be normal to (i.e. tangent to centerline)
        resolution: the number of segments (or triangles) used to approximate the circular disc.
            
    Return:
        Open3D disc mesh
    """
    normal = np.asarray(normal, dtype=np.float64)
    if np.linalg.norm(normal) == 0:
        # If the normal is a zero vector, default to Z-axis to avoid errors
        normal = np.array([0, 0, 1], dtype=np.float64)
    else:
        normal /= np.linalg.norm(normal)
        
    # Step 1: Create disc in XY plane
    angles = np.linspace(0, 2 * np.pi, resolution, endpoint=False)
    circle_points = np.c_[np.cos(angles), np.sin(angles), np.zeros_like(angles)] * radius
    vertices = np.vstack([[0, 0, 0], circle_points])
    triangles = [[0, i, i + 1] for i in range(1, resolution)]
    triangles.append([0, resolution, 1])  

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(vertices)
    mesh.triangles = o3d.utility.Vector3iVector(triangles)
    mesh.compute_vertex_normals()

    # Step 2: Rotate to align normal with Z-axis
    z_axis = np.array([0, 0, 1], dtype=np.float64)

    if not np.allclose(normal, z_axis):
        axis = np.cross(z_axis, normal)
        # Handle case where normal is parallel to z_axis but opposite
        if np.linalg.norm(axis) == 0:
            if np.allclose(normal, -z_axis):
                axis = np.array([1,0,0]) # Rotate 180 degrees around x-axis
            else:
                axis = np.array([0,1,0]) # Default axis if already aligned
        else:
             axis /= np.linalg.norm(axis)

        angle = np.arccos(np.clip(np.dot(z_axis, normal), -1.0, 1.0))
        R = o3d.geometry.get_rotation_matrix_from_axis_angle(axis * angle)
        mesh.rotate(R, center=(0, 0, 0))

    # Step 3: Translate to center position
    mesh.translate(center)

    return mesh