# from google.oauth2.credentials import Credentials
# from typing import List, Dict, Any, Optional
# import json
# from datetime import datetime
# from .service_mapping import get_service_type_for_deployment, is_deployment_based_service

# # Try to import Google Cloud libraries, but provide fallbacks if not available
# try:
#     from google.cloud import run_v2, functions_v2, container_v1, batch_v1
#     from google.cloud import compute_v1, dataproc_v1, scheduler_v1
#     GOOGLE_CLOUD_AVAILABLE = True
#     APPENGINE_AVAILABLE = False
#     try:
#         from google.cloud import appengine_v1
#         APPENGINE_AVAILABLE = True
#     except ImportError:
#         print("Warning: App Engine library not available")
# except ImportError:
#     print("Warning: Some Google Cloud libraries not available. Deployment fetching will be limited.")
#     GOOGLE_CLOUD_AVAILABLE = False
#     APPENGINE_AVAILABLE = False

# class GCPDeploymentService:
#     def __init__(self, credentials: Credentials):
#         self.credentials = credentials
        
#         # Initialize clients for different GCP services only if libraries are available
#         if GOOGLE_CLOUD_AVAILABLE:
#             try:
#                 self.run_client = run_v2.ServicesClient(credentials=credentials)
#                 self.functions_client = functions_v2.FunctionServiceClient(credentials=credentials)
#                 self.gke_client = container_v1.ClusterManagerClient(credentials=credentials)
#                 self.batch_client = batch_v1.BatchServiceClient(credentials=credentials)
#                 self.compute_client = compute_v1.InstancesClient(credentials=credentials)
#                 self.dataproc_client = dataproc_v1.ClusterControllerClient(credentials=credentials)
#                 self.scheduler_client = scheduler_v1.CloudSchedulerClient(credentials=credentials)
                
#                 # Initialize App Engine client only if available
#                 if APPENGINE_AVAILABLE:
#                     self.appengine_client = appengine_v1.VersionsClient(credentials=credentials)
#                 else:
#                     self.appengine_client = None
                    
#             except Exception as e:
#                 print(f"Error initializing Google Cloud clients: {str(e)}")
#                 # Do not assign to GOOGLE_CLOUD_AVAILABLE here
#         else:
#             # Set clients to None if libraries aren't available
#             self.run_client = None
#             self.appengine_client = None
#             self.functions_client = None
#             self.gke_client = None
#             self.batch_client = None
#             self.compute_client = None
#             self.dataproc_client = None
#             self.scheduler_client = None

#     async def get_deployments(self, project_id: str, service_id: str) -> List[Dict[str, Any]]:
#         """Get deployments/instances for a specific GCP service"""
#         try:
#             # Map frontend service ID to backend service type
#             service_type = get_service_type_for_deployment(service_id)
#             if not service_type:
#                 raise ValueError(f"Unsupported service ID: {service_id}")
            
#             if service_type == "cloud_run":
#                 return await self._get_cloud_run_services(project_id)
#             elif service_type == "app_engine":
#                 return await self._get_app_engine_versions(project_id)
#             elif service_type == "cloud_functions":
#                 return await self._get_cloud_functions(project_id)
#             elif service_type == "gke":
#                 return await self._get_gke_clusters(project_id)
#             elif service_type == "cloud_batch":
#                 return await self._get_batch_jobs(project_id)
#             elif service_type == "compute_engine":
#                 return await self._get_compute_instances(project_id)
#             elif service_type == "dataproc":
#                 return await self._get_dataproc_clusters(project_id)
#             elif service_type == "cloud_scheduler":
#                 return await self._get_scheduler_jobs(project_id)
#             else:
#                 raise ValueError(f"Unsupported service type: {service_type}")
#         except Exception as e:
#             print(f"Error fetching deployments for {service_id}: {str(e)}")
#             return []

#     async def _get_cloud_run_services(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Cloud Run services"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.run_client:
#             print("Cloud Run client not available")
#             return []
            
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = run_v2.ListServicesRequest(parent=parent)
#             page_result = self.run_client.list_services(request=request)
            
#             services = []
#             for service in page_result:
#                 services.append({
#                     "id": service.name.split("/")[-1],
#                     "name": service.metadata.name,
#                     "display_name": service.metadata.name,
#                     "status": service.status.conditions[-1].type if service.status.conditions else "UNKNOWN",
#                     "url": service.status.url,
#                     "region": service.metadata.labels.get("cloud.googleapis.com/location", "unknown"),
#                     "created_at": service.metadata.create_time.isoformat() if service.metadata.create_time else None,
#                     "updated_at": service.metadata.update_time.isoformat() if service.metadata.update_time else None,
#                     "type": "cloud_run"
#                 })
#             return services
#         except Exception as e:
#             print(f"Error fetching Cloud Run services: {str(e)}")
#             return []

#     async def _get_app_engine_versions(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get App Engine versions"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.appengine_client:
#             print("App Engine client not available")
#             return []
            
#         try:
#             parent = f"apps/{project_id}/services/-"
#             request = appengine_v1.ListVersionsRequest(parent=parent)
#             page_result = self.appengine_client.list_versions(request=request)
            
#             versions = []
#             for version in page_result:
#                 versions.append({
#                     "id": version.name.split("/")[-1],
#                     "name": version.id,
#                     "display_name": f"{version.id} ({version.service_id})",
#                     "status": version.status,
#                     "service_id": version.service_id,
#                     "created_at": version.create_time.isoformat() if version.create_time else None,
#                     "type": "app_engine"
#                 })
#             return versions
#         except Exception as e:
#             print(f"Error fetching App Engine versions: {str(e)}")
#             return []

#     async def _get_cloud_functions(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Cloud Functions"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.functions_client:
#             print("Cloud Functions client not available")
#             return []
            
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = functions_v2.ListFunctionsRequest(parent=parent)
#             page_result = self.functions_client.list_functions(request=request)
            
#             functions = []
#             for function in page_result:
#                 functions.append({
#                     "id": function.name.split("/")[-1],
#                     "name": function.name.split("/")[-1],
#                     "display_name": function.name.split("/")[-1],
#                     "status": function.state.name,
#                     "region": function.name.split("/")[3] if len(function.name.split("/")) > 3 else "unknown",
#                     "runtime": function.build_config.runtime if function.build_config else "unknown",
#                     "created_at": function.create_time.isoformat() if function.create_time else None,
#                     "updated_at": function.update_time.isoformat() if function.update_time else None,
#                     "type": "cloud_functions"
#                 })
#             return functions
#         except Exception as e:
#             print(f"Error fetching Cloud Functions: {str(e)}")
#             return []

#     async def _get_gke_clusters(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get GKE clusters"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.gke_client:
#             print("GKE client not available")
#             return []
            
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = container_v1.ListClustersRequest(parent=parent)
#             page_result = self.gke_client.list_clusters(request=request)
            
#             clusters = []
#             for cluster in page_result:
#                 clusters.append({
#                     "id": cluster.name.split("/")[-1],
#                     "name": cluster.name.split("/")[-1],
#                     "display_name": cluster.name.split("/")[-1],
#                     "status": cluster.status.name,
#                     "location": cluster.location,
#                     "node_count": cluster.current_node_count,
#                     "version": cluster.current_master_version,
#                     "created_at": cluster.create_time.isoformat() if cluster.create_time else None,
#                     "type": "gke"
#                 })
#             return clusters
#         except Exception as e:
#             print(f"Error fetching GKE clusters: {str(e)}")
#             return []

#     async def _get_batch_jobs(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Cloud Batch jobs"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.batch_client:
#             print("Cloud Batch client not available")
#             return []
            
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = batch_v1.ListJobsRequest(parent=parent)
#             page_result = self.batch_client.list_jobs(request=request)
            
#             jobs = []
#             for job in page_result:
#                 jobs.append({
#                     "id": job.name.split("/")[-1],
#                     "name": job.name.split("/")[-1],
#                     "display_name": job.name.split("/")[-1],
#                     "status": job.status.state.name,
#                     "location": job.name.split("/")[3] if len(job.name.split("/")) > 3 else "unknown",
#                     "created_at": job.create_time.isoformat() if job.create_time else None,
#                     "type": "cloud_batch"
#                 })
#             return jobs
#         except Exception as e:
#             print(f"Error fetching Cloud Batch jobs: {str(e)}")
#             return []

#     async def _get_compute_instances(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Compute Engine instances"""
#         if not GOOGLE_CLOUD_AVAILABLE or not self.compute_client:
#             print("Compute Engine client not available")
#             return []
            
#         try:
#             request = compute_v1.AggregatedListInstancesRequest(project=project_id)
#             page_result = self.compute_client.aggregated_list(request=request)
            
#             instances = []
#             for zone, zone_instances in page_result.items():
#                 if zone_instances.instances:
#                     for instance in zone_instances.instances:
#                         instances.append({
#                             "id": instance.name,
#                             "name": instance.name,
#                             "display_name": instance.name,
#                             "status": instance.status,
#                             "zone": instance.zone.split("/")[-1],
#                             "machine_type": instance.machine_type.split("/")[-1],
#                             "created_at": instance.creation_timestamp,
#                             "type": "compute_engine"
#                         })
#             return instances
#         except Exception as e:
#             print(f"Error fetching Compute Engine instances: {str(e)}")
#             return []

#     async def _get_dataproc_clusters(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Dataproc clusters"""
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = dataproc_v1.ListClustersRequest(parent=parent)
#             page_result = self.dataproc_client.list_clusters(request=request)
            
#             clusters = []
#             for cluster in page_result:
#                 clusters.append({
#                     "id": cluster.cluster_name,
#                     "name": cluster.cluster_name,
#                     "display_name": cluster.cluster_name,
#                     "status": cluster.status.state.name,
#                     "location": cluster.cluster_name.split("/")[3] if len(cluster.cluster_name.split("/")) > 3 else "unknown",
#                     "created_at": cluster.status.state_start_time.isoformat() if cluster.status.state_start_time else None,
#                     "type": "dataproc"
#                 })
#             return clusters
#         except Exception as e:
#             print(f"Error fetching Dataproc clusters: {str(e)}")
#             return []

#     async def _get_scheduler_jobs(self, project_id: str) -> List[Dict[str, Any]]:
#         """Get Cloud Scheduler jobs"""
#         try:
#             parent = f"projects/{project_id}/locations/-"
#             request = scheduler_v1.ListJobsRequest(parent=parent)
#             page_result = self.scheduler_client.list_jobs(request=request)
            
#             jobs = []
#             for job in page_result:
#                 jobs.append({
#                     "id": job.name.split("/")[-1],
#                     "name": job.name.split("/")[-1],
#                     "display_name": job.name.split("/")[-1],
#                     "status": "ACTIVE" if job.state == scheduler_v1.Job.State.ENABLED else "PAUSED",
#                     "location": job.name.split("/")[3] if len(job.name.split("/")) > 3 else "unknown",
#                     "schedule": job.schedule,
#                     "created_at": job.create_time.isoformat() if job.create_time else None,
#                     "type": "cloud_scheduler"
#                 })
#             return jobs
#         except Exception as e:
#             print(f"Error fetching Cloud Scheduler jobs: {str(e)}")
#             return [] 

from google.oauth2.credentials import Credentials
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from .service_mapping import get_service_type_for_deployment, is_deployment_based_service

# Try to import Google Cloud libraries, but provide fallbacks if not available
try:
    from google.cloud import run_v2, functions_v2, container_v1, batch_v1
    from google.cloud import compute_v1, dataproc_v1, scheduler_v1
    GOOGLE_CLOUD_AVAILABLE = True
    APPENGINE_AVAILABLE = False
    try:
        from google.cloud import appengine_v1
        APPENGINE_AVAILABLE = True
    except ImportError:
        print("Warning: App Engine library not available")
except ImportError:
    print("Warning: Some Google Cloud libraries not available. Deployment fetching will be limited.")
    GOOGLE_CLOUD_AVAILABLE = False
    APPENGINE_AVAILABLE = False

class GCPDeploymentService:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        
        # Initialize clients for different GCP services only if libraries are available
        if GOOGLE_CLOUD_AVAILABLE:
            try:
                self.run_client = run_v2.ServicesClient(credentials=credentials)
                self.functions_client = functions_v2.FunctionServiceClient(credentials=credentials)
                self.gke_client = container_v1.ClusterManagerClient(credentials=credentials)
                self.batch_client = batch_v1.BatchServiceClient(credentials=credentials)
                self.compute_client = compute_v1.InstancesClient(credentials=credentials)
                self.dataproc_client = dataproc_v1.ClusterControllerClient(credentials=credentials)
                self.scheduler_client = scheduler_v1.CloudSchedulerClient(credentials=credentials)
                
                # Initialize App Engine client only if available
                if APPENGINE_AVAILABLE:
                    self.appengine_client = appengine_v1.VersionsClient(credentials=credentials)
                else:
                    self.appengine_client = None
                    
            except Exception as e:
                print(f"Error initializing Google Cloud clients: {str(e)}")
                # Do not assign to GOOGLE_CLOUD_AVAILABLE here
        else:
            # Set clients to None if libraries aren't available
            self.run_client = None
            self.appengine_client = None
            self.functions_client = None
            self.gke_client = None
            self.batch_client = None
            self.compute_client = None
            self.dataproc_client = None
            self.scheduler_client = None

    async def get_deployments(self, project_id: str, service_id: str) -> List[Dict[str, Any]]:
        """Get deployments/instances for a specific GCP service"""
        try:
            # Map frontend service ID to backend service type
            service_type = get_service_type_for_deployment(service_id)
            if not service_type:
                print(f"Unsupported service ID: {service_id}")
                return []
            
            print(f"Fetching deployments for service_id: {service_id}, service_type: {service_type}")
            
            if service_type == "cloud_run":
                return await self._get_cloud_run_services(project_id)
            elif service_type == "app_engine":
                return await self._get_app_engine_versions(project_id)
            elif service_type == "cloud_functions":
                return await self._get_cloud_functions(project_id)
            elif service_type == "gke":
                return await self._get_gke_clusters(project_id)
            elif service_type == "cloud_batch":
                return await self._get_batch_jobs(project_id)
            elif service_type == "compute_engine":
                return await self._get_compute_instances(project_id)
            elif service_type == "dataproc":
                return await self._get_dataproc_clusters(project_id)
            elif service_type == "cloud_scheduler":
                return await self._get_scheduler_jobs(project_id)
            else:
                print(f"Unsupported service type: {service_type}")
                return []
        except Exception as e:
            print(f"Error fetching deployments for {service_id}: {str(e)}")
            return []

    async def _get_cloud_run_services(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Cloud Run services (both Container and Function types)"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.run_client:
            print("Cloud Run client not available")
            return []
            
        try:
            # Get all regions to search in
            regions = ['us-central1', 'us-east1', 'us-west1', 'europe-west1', 'asia-east1']  # Add more regions as needed
            all_services = []
            
            for region in regions:
                try:
                    parent = f"projects/{project_id}/locations/{region}"
                    request = run_v2.ListServicesRequest(parent=parent)
                    page_result = self.run_client.list_services(request=request)
                    
                    for service in page_result:
                        service_data = {
                            "id": service.name.split("/")[-1],
                            "name": service.name.split("/")[-1],
                            "display_name": service.name.split("/")[-1],
                            "status": "ACTIVE" if service.status.conditions else "UNKNOWN",
                            "url": service.status.url if service.status.url else None,
                            "region": region,
                            "created_at": service.metadata.create_time.isoformat() if service.metadata.create_time else None,
                            "updated_at": service.metadata.update_time.isoformat() if service.metadata.update_time else None,
                            "type": "cloud_run"
                        }
                        
                        # Check if this is a function (Cloud Run functions show up as services)
                        if service.metadata.labels and 'run.googleapis.com/execution-environment' in service.metadata.labels:
                            if service.metadata.labels.get('run.googleapis.com/execution-environment') == 'gen2':
                                service_data['deployment_type'] = 'Function'
                            else:
                                service_data['deployment_type'] = 'Container'
                        else:
                            service_data['deployment_type'] = 'Container'
                        
                        # Extract authentication info from metadata
                        if service.metadata.annotations:
                            auth_policy = service.metadata.annotations.get('run.googleapis.com/ingress', 'all')
                            service_data['authentication'] = 'Allow unauthenticated' if auth_policy != 'internal' else 'Require authentication'
                            service_data['ingress'] = auth_policy
                        
                        all_services.append(service_data)
                        
                except Exception as region_error:
                    print(f"Error fetching Cloud Run services in region {region}: {str(region_error)}")
                    continue
            
            print(f"Found {len(all_services)} Cloud Run services")
            return all_services
            
        except Exception as e:
            print(f"Error fetching Cloud Run services: {str(e)}")
            return []

    async def _get_app_engine_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """Get App Engine versions"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.appengine_client:
            print("App Engine client not available")
            return []
            
        try:
            parent = f"apps/{project_id}/services/-"
            request = appengine_v1.ListVersionsRequest(parent=parent)
            page_result = self.appengine_client.list_versions(request=request)
            
            versions = []
            for version in page_result:
                versions.append({
                    "id": version.name.split("/")[-1],
                    "name": version.id,
                    "display_name": f"{version.id} ({version.service})",
                    "status": version.serving_status.name if version.serving_status else "UNKNOWN",
                    "service_id": version.service,
                    "created_at": version.create_time.isoformat() if version.create_time else None,
                    "type": "app_engine"
                })
            return versions
        except Exception as e:
            print(f"Error fetching App Engine versions: {str(e)}")
            return []

    async def _get_cloud_functions(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Cloud Functions (1st gen functions)"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.functions_client:
            print("Cloud Functions client not available")
            return []
            
        try:
            # Get all regions to search in
            regions = ['us-central1', 'us-east1', 'us-west1', 'europe-west1', 'asia-east1']  # Add more regions as needed
            all_functions = []
            
            for region in regions:
                try:
                    parent = f"projects/{project_id}/locations/{region}"
                    request = functions_v2.ListFunctionsRequest(parent=parent)
                    page_result = self.functions_client.list_functions(request=request)
                    
                    for function in page_result:
                        all_functions.append({
                            "id": function.name.split("/")[-1],
                            "name": function.name.split("/")[-1],
                            "display_name": function.name.split("/")[-1],
                            "status": function.state.name if function.state else "UNKNOWN",
                            "region": region,
                            "runtime": function.build_config.runtime if function.build_config else "unknown",
                            "created_at": function.create_time.isoformat() if function.create_time else None,
                            "updated_at": function.update_time.isoformat() if function.update_time else None,
                            "type": "cloud_functions",
                            "deployment_type": "Function"
                        })
                except Exception as region_error:
                    print(f"Error fetching Cloud Functions in region {region}: {str(region_error)}")
                    continue
            
            print(f"Found {len(all_functions)} Cloud Functions")
            return all_functions
            
        except Exception as e:
            print(f"Error fetching Cloud Functions: {str(e)}")
            return []

    async def _get_gke_clusters(self, project_id: str) -> List[Dict[str, Any]]:
        """Get GKE clusters"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.gke_client:
            print("GKE client not available")
            return []
            
        try:
            parent = f"projects/{project_id}/locations/-"
            request = container_v1.ListClustersRequest(parent=parent)
            page_result = self.gke_client.list_clusters(request=request)
            
            clusters = []
            for cluster in page_result:
                clusters.append({
                    "id": cluster.name.split("/")[-1],
                    "name": cluster.name.split("/")[-1],
                    "display_name": cluster.name.split("/")[-1],
                    "status": cluster.status.name if cluster.status else "UNKNOWN",
                    "location": cluster.location,
                    "node_count": cluster.current_node_count,
                    "version": cluster.current_master_version,
                    "created_at": cluster.create_time.isoformat() if cluster.create_time else None,
                    "type": "gke"
                })
            return clusters
        except Exception as e:
            print(f"Error fetching GKE clusters: {str(e)}")
            return []

    async def _get_batch_jobs(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Cloud Batch jobs"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.batch_client:
            print("Cloud Batch client not available")
            return []
            
        try:
            parent = f"projects/{project_id}/locations/-"
            request = batch_v1.ListJobsRequest(parent=parent)
            page_result = self.batch_client.list_jobs(request=request)
            
            jobs = []
            for job in page_result:
                jobs.append({
                    "id": job.name.split("/")[-1],
                    "name": job.name.split("/")[-1],
                    "display_name": job.name.split("/")[-1],
                    "status": job.status.state.name if job.status else "UNKNOWN",
                    "location": job.name.split("/")[3] if len(job.name.split("/")) > 3 else "unknown",
                    "created_at": job.create_time.isoformat() if job.create_time else None,
                    "type": "cloud_batch"
                })
            return jobs
        except Exception as e:
            print(f"Error fetching Cloud Batch jobs: {str(e)}")
            return []

    async def _get_compute_instances(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Compute Engine instances"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.compute_client:
            print("Compute Engine client not available")
            return []
            
        try:
            request = compute_v1.AggregatedListInstancesRequest(project=project_id)
            page_result = self.compute_client.aggregated_list(request=request)
            
            instances = []
            for zone_name, zone_instances in page_result.items():
                if zone_instances.instances:
                    for instance in zone_instances.instances:
                        instances.append({
                            "id": instance.name,
                            "name": instance.name,
                            "display_name": instance.name,
                            "status": instance.status,
                            "zone": instance.zone.split("/")[-1] if instance.zone else "unknown",
                            "machine_type": instance.machine_type.split("/")[-1] if instance.machine_type else "unknown",
                            "created_at": instance.creation_timestamp,
                            "type": "compute_engine"
                        })
            return instances
        except Exception as e:
            print(f"Error fetching Compute Engine instances: {str(e)}")
            return []

    async def _get_dataproc_clusters(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Dataproc clusters"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.dataproc_client:
            print("Dataproc client not available")
            return []
            
        try:
            parent = f"projects/{project_id}/regions/-"
            request = dataproc_v1.ListClustersRequest(project_id=project_id, region="-")
            page_result = self.dataproc_client.list_clusters(request=request)
            
            clusters = []
            for cluster in page_result:
                clusters.append({
                    "id": cluster.cluster_name,
                    "name": cluster.cluster_name,
                    "display_name": cluster.cluster_name,
                    "status": cluster.status.state.name if cluster.status else "UNKNOWN",
                    "location": cluster.config.gce_cluster_config.zone_uri.split("/")[-1] if cluster.config.gce_cluster_config.zone_uri else "unknown",
                    "created_at": cluster.status.state_start_time.isoformat() if cluster.status.state_start_time else None,
                    "type": "dataproc"
                })
            return clusters
        except Exception as e:
            print(f"Error fetching Dataproc clusters: {str(e)}")
            return []

    async def _get_scheduler_jobs(self, project_id: str) -> List[Dict[str, Any]]:
        """Get Cloud Scheduler jobs"""
        if not GOOGLE_CLOUD_AVAILABLE or not self.scheduler_client:
            print("Cloud Scheduler client not available")
            return []
            
        try:
            parent = f"projects/{project_id}/locations/-"
            request = scheduler_v1.ListJobsRequest(parent=parent)
            page_result = self.scheduler_client.list_jobs(request=request)
            
            jobs = []
            for job in page_result:
                jobs.append({
                    "id": job.name.split("/")[-1],
                    "name": job.name.split("/")[-1],
                    "display_name": job.name.split("/")[-1],
                    "status": "ACTIVE" if job.state == scheduler_v1.Job.State.ENABLED else "PAUSED",
                    "location": job.name.split("/")[3] if len(job.name.split("/")) > 3 else "unknown",
                    "schedule": job.schedule,
                    "created_at": job.create_time.isoformat() if job.create_time else None,
                    "type": "cloud_scheduler"
                })
            return jobs
        except Exception as e:
            print(f"Error fetching Cloud Scheduler jobs: {str(e)}")
            return []