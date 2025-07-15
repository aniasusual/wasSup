# from typing import Dict, Optional

# # Mapping from frontend service IDs to backend service types
# SERVICE_TYPE_MAPPING: Dict[str, str] = {
#     # Cloud Run - support multiple possible service_ids
#     "cloud_run": "cloud_run",
#     "cloud_run_revision": "cloud_run",
#     "cloud_run_service": "cloud_run",
    
#     # App Engine
#     "app_engine": "app_engine",
#     "gae_app": "app_engine",
    
#     # Cloud Functions
#     "cloud_functions": "cloud_functions",
#     "cloud_function": "cloud_functions",
    
#     # GKE
#     "gke": "gke",
#     "kubernetes": "gke",
#     "k8s_container": "gke",
    
#     # Compute Engine
#     "compute_engine": "compute_engine",
#     "gce_instance": "compute_engine",
    
#     # Cloud Batch (if available)
#     "cloud_batch": "cloud_batch",
#     "batch_job": "cloud_batch",
    
#     # Dataproc
#     "dataproc": "dataproc",
#     "dataproc_cluster": "dataproc",
    
#     # Cloud Scheduler
#     "cloud_scheduler": "cloud_scheduler",
#     "cloud_scheduler_job": "cloud_scheduler",
# }

# def get_service_type_for_deployment(service_id: str) -> Optional[str]:
#     """Get the backend service type for deployment fetching based on frontend service ID"""
#     service_type = SERVICE_TYPE_MAPPING.get(service_id)
#     if not service_type:
#         print(f"Warning: Unknown service_id '{service_id}'. Available service_ids: {list(SERVICE_TYPE_MAPPING.keys())}")
#     return service_type

# def is_deployment_based_service(service_id: str) -> bool:
#     """Check if a service is deployment-based (has deployments/instances to fetch)"""
#     return service_id in SERVICE_TYPE_MAPPING

# def get_supported_deployment_services() -> list:
#     """Get list of service IDs that support deployment fetching"""
#     return list(SERVICE_TYPE_MAPPING.keys())

from typing import Dict, Optional

# Mapping from frontend service IDs to backend service types
SERVICE_TYPE_MAPPING: Dict[str, str] = {
    # Cloud Run - support multiple possible service_ids
    "cloud_run": "cloud_run",
    "cloud_run_revision": "cloud_run",
    "cloud_run_service": "cloud_run",
    
    # App Engine
    "app_engine": "app_engine",
    "gae_app": "app_engine",
    
    # Cloud Functions
    "cloud_functions": "cloud_functions",
    "cloud_function": "cloud_functions",
    
    # GKE
    "gke": "gke",
    "kubernetes": "gke",
    "k8s_container": "gke",
    
    # Compute Engine
    "compute_engine": "compute_engine",
    "gce_instance": "compute_engine",
    
    # Cloud Batch (if available)
    "cloud_batch": "cloud_batch",
    "batch_job": "cloud_batch",
    
    # Dataproc
    "dataproc": "dataproc",
    "dataproc_cluster": "dataproc",
    
    # Cloud Scheduler
    "cloud_scheduler": "cloud_scheduler",
    "cloud_scheduler_job": "cloud_scheduler",
}

def get_service_type_for_deployment(service_id: str) -> Optional[str]:
    """Get the backend service type for deployment fetching based on frontend service ID"""
    service_type = SERVICE_TYPE_MAPPING.get(service_id)
    if not service_type:
        print(f"Warning: Unknown service_id '{service_id}'. Available service_ids: {list(SERVICE_TYPE_MAPPING.keys())}")
    return service_type

def is_deployment_based_service(service_id: str) -> bool:
    """Check if a service is deployment-based (has deployments/instances to fetch)"""
    return service_id in SERVICE_TYPE_MAPPING

def get_supported_deployment_services() -> list:
    """Get list of service IDs that support deployment fetching"""
    return list(SERVICE_TYPE_MAPPING.keys())