# End-to-End Vessel Reconstruction, Visualization, and Analysis on HPE Private Cloud AI (PCAI)

Author: Andrew Mendez andrew.mendez@hpe.com

This repository contains a Helm chart for deploying the Vessel Reconstruction Streamlit application on HPE's Private Cloud AI (PCAI) platform.

The application provides a complete workflow for medical imaging analysis:

-   **Input:** Takes 2D segmentation predictions from NVIDIA's VISTA-3D model (A model that is deployed in PCAI).
-   **Processing:** Performs 3D reconstruction of blood vessels (aorta, iliac arteries).
-   **Analysis:** Calculates key clinical markers such as maximum diameter and tortuosity.
-   **Visualization:** Presents the 3D models and analysis results in an interactive Streamlit web interface for review by clinicians.

By deploying on PCAI, the application is automatically deployed with turn-key infrastructure for guaranteed resource allocation, persistent storage, and scalability.

## Prerequisites

Before deploying this chart, you must have the following:

1.  Access to an HPE Private Cloud AI (PCAI) environment.
2.  An existing **PersistentVolumeClaim (PVC)** available in your target namespace (e.g., `kubeflow-shared-pvc`) for storing input and output data.

## Codebase Structure
The codebase contains the application code and Dockerfile used to containerize this application. The latest docker image is available at `mendeza/vessel-analysis-app:0.0.1`. This codebase also contains the Helm chart to deploy this application in PCAI.

## Helm Chart Structure

The application is packaged as a Helm chart with the following structure:

```
helm/
├── Chart.yaml          # Metadata about the chart (name, version, etc.).
├── values.yaml         # Default configuration values for the chart.
├── templates/
│   ├── _helpers.tpl    # Helper templates for labels and names.
│   ├── deployment.yaml # Manages the application pod and its resources.
│   ├── service.yaml    # Exposes the application internally within the cluster.
│   └── virtual-service.yaml # Exposes the service externally via the Istio gateway.
└── .helmignore         # Specifies files to ignore when packaging the chart.
```

## Deployment Instructions

To deploy this application in PCAI, follow these steps:

1.  **Clone the Repository**
    Clone this repository to your local machine.


2.  **Package the Helm Chart**
    Navigate to the `helm/` directory and use the `helm package` command. This will create a compressed `.tgz` archive of the chart.
    ```bash
    cd helm/
    helm package vessel-reconstruction/
    # This will create a file like vessel-reconstruction-0.1.0.tgz
    ```

4.  **Import into PCAI**
    -   Navigate to your PCAI dashboard.
    -   Go to **Tools & Frameworks > Data Science** tab.
    -   Click **Import Framework**.
    -   Follow the on-screen instructions, and when prompted, upload the `vessel-reconstruction-0.1.0.tgz` file you just created.
    -   During the import or deployment phase, PCAI will use the values from `values.yaml` to configure the application. 

## Accessing the Application

Once the deployment is complete, the application will be accessible at the URL https://reconstruction.${DOMAIN_NAME}, where ${DOMAIN_NAME} is the domain name PCAI is deployed with. You can find the exact link in the PCAI **Tools & Frameworks** dashboard for your deployed instance.


## Configuration

The following table lists the configurable parameters of the Vessel Reconstruction chart and their default values, as defined in `values.yaml`.

| Parameter | Description | Default |
| :--- | :--- | :--- |
| `replicaCount` | The number of application pods to run. | `1` |
| `namespace` | The Kubernetes namespace where all resources will be deployed. | `"andrew-mendez-4a1f9d06"` |
| **HPE Ezmeral (EzUA) Settings** | | |
| `ezua.enabled` | If `true`, an Istio VirtualService will be created to expose the app. | `true` |
| `ezua.virtualService.endpoint` | The external hostname for the service. `\${DOMAIN_NAME}` is a placeholder for your cluster's domain. | `"reconstruction.${DOMAIN_NAME}"` |
| `ezua.virtualService.istioGateway` | The Istio gateway to bind the VirtualService to. | `"istio-system/ezaf-gateway"` |
| **Image Settings** | | |
| `image.repository` | The Docker image to use for the application. | `"mendeza/vessel-analysis-app"` |
| `image.pullPolicy` | The image pull policy. | `"IfNotPresent"` |
| `image.tag` | The tag of the Docker image to pull. | `"0.0.1"` |
| **Resource Settings** | | |
| `resources.requests.cpu` | CPU requested for the pod. | `"4"` |
| `resources.requests.memory` | Memory requested for the pod. | `"32Gi"` |
| `resources.limits.cpu` | CPU limit for the pod. | `"4"` |
| `resources.limits.memory` | Memory limit for the pod. | `"32Gi"` |
| **Service Settings** | | |
| `service.type` | The type of Kubernetes service to create. | `"ClusterIP"` |
| `service.port` | The port the service will expose. | `8501` |
| `service.name` | The name of the service port. | `"http-streamlit"` |
| **Persistence Settings** | | |
| `persistence.enabled` | If `true`, mounts a volume for persistent data. | `true` |
| `persistence.existingClaim` | The name of the pre-existing PersistentVolumeClaim to use. | `"kubeflow-shared-pvc"` |
| `persistence.subPath` | The sub-path within the PVC to mount into the container. | `"califra/outputs"` |
| `persistence.mountPath` | The path inside the container where the volume will be mounted. | `"/app/outputs"` |