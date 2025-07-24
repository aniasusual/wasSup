
# Complete GCP API endpoints configuration matching your resource mappings
from typing import Dict, List, Any, Optional, Callable, Union

def extract_names_from_items(data: Dict[str, Any], name_field: str = "name") -> List[str]:
    """Helper function to extract names from API response items"""
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not isinstance(items, list):
        return []
    return [item.get(name_field) for item in items if isinstance(item, dict) and item.get(name_field)]

def extract_ids_from_items(data: Dict[str, Any], id_field: str = "id") -> List[str]:
    """Helper function to extract IDs from API response items"""
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not isinstance(items, list):
        return []
    return [item.get(id_field) for item in items if isinstance(item, dict) and item.get(id_field)]

def extract_from_aggregated(data: Dict[str, Any], resource_key: str, name_field: str = "name") -> List[str]:
    """Helper function to extract resources from aggregated API responses"""
    if not isinstance(data, dict):
        return []
    resources = []
    items = data.get("items", {})
    if isinstance(items, dict):
        for region_data in items.values():
            if isinstance(region_data, dict) and resource_key in region_data:
                resource_list = region_data[resource_key]
                if isinstance(resource_list, list):
                    resources.extend([
                        resource.get(name_field) 
                        for resource in resource_list 
                        if isinstance(resource, dict) and resource.get(name_field)
                    ])
    return resources

def extract_split_names(data: Dict[str, Any], items_key: str, split_char: str = "/") -> List[str]:
    """Helper function to extract names that need to be split from full paths"""
    if not isinstance(data, dict):
        return []
    items = data.get(items_key, [])
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if isinstance(item, dict) and item.get("name"):
            name = item.get("name", "")
            if split_char in name:
                result.append(name.split(split_char)[-1])
            else:
                result.append(name)
    return result

def extract_cloud_run_services(data: Dict[str, Any]) -> List[str]:
    """Extract Cloud Run service names from API response"""
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not isinstance(items, list):
        return []
    services = []
    for item in items:
        if isinstance(item, dict):
            metadata = item.get("metadata", {})
            if isinstance(metadata, dict):
                name = metadata.get("name")
                if name:
                    services.append(name)
    return services

def extract_cloud_run_revisions(data: Dict[str, Any]) -> List[str]:
    """Extract Cloud Run revision names from API response"""
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    if not isinstance(items, list):
        return []
    revisions = []
    for item in items:
        if isinstance(item, dict):
            metadata = item.get("metadata", {})
            if isinstance(metadata, dict):
                name = metadata.get("name")
                if name:
                    revisions.append(name)
    return revisions

# Complete GCP API endpoints configuration
GCP_API_ENDPOINTS = {
    # Compute Services
    "cloud_run_revision": {
        "service_name": {
            "endpoint": lambda project_id: f"https://run.googleapis.com/v1/projects/{project_id}/locations/-/services",
            "transform": extract_cloud_run_services,
        },
        "revision_name": {
            "endpoint": lambda project_id, service_name: f"https://run.googleapis.com/v1/projects/{project_id}/locations/-/services/{service_name}/revisions",
            "transform": extract_cloud_run_revisions,
            "depends_on": "service_name",
        },
        "location": {
            "endpoint": lambda project_id: f"https://run.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "k8s_container": {
        "cluster_name": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations/-/clusters",
            "transform": lambda data: [cluster.get("name") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("name")],
        },
        "namespace_name": {
            "endpoint": "#kubernetes-api-required",
            "transform": lambda data: ["default", "kube-system", "kube-public", "gke-system"],  # Common namespaces
        },
        "pod_name": {
            "endpoint": "#kubernetes-api-required", 
            "transform": lambda data: [],
        },
        "container_name": {
            "endpoint": "#kubernetes-api-required",
            "transform": lambda data: [],
        },
    },

    "k8s_cluster": {
        "cluster_name": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations/-/clusters",
            "transform": lambda data: [cluster.get("name") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "k8s_node": {
        "cluster_name": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations/-/clusters",
            "transform": lambda data: [cluster.get("name") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("name")],
        },
        "node_name": {
            "endpoint": "#kubernetes-api-required",
            "transform": lambda data: [],
        },
        "location": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "k8s_pod": {
        "cluster_name": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations/-/clusters",
            "transform": lambda data: [cluster.get("name") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("name")],
        },
        "namespace_name": {
            "endpoint": "#kubernetes-api-required",
            "transform": lambda data: ["default", "kube-system", "kube-public", "gke-system"],
        },
        "pod_name": {
            "endpoint": "#kubernetes-api-required",
            "transform": lambda data: [],
        },
        "location": {
            "endpoint": lambda project_id: f"https://container.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "gce_instance": {
        "instance_id": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/instances",
            "transform": lambda data: extract_from_aggregated(data, "instances", "id"),
        },
        "zone": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones",
            "transform": extract_names_from_items,
        },
    },

    "cloud_function": {
        "function_name": {
            "endpoint": lambda project_id: f"https://cloudfunctions.googleapis.com/v1/projects/{project_id}/locations/-/functions",
            "transform": lambda data: [func.get("name", "").split("/")[-1] for func in data.get("functions", []) if isinstance(func, dict) and func.get("name")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://cloudfunctions.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "gae_app": {
        "service": {
            "endpoint": lambda project_id: f"https://appengine.googleapis.com/v1/apps/{project_id}/services",
            "transform": lambda data: [svc.get("id") for svc in data.get("services", []) if isinstance(svc, dict) and svc.get("id")],
        },
        "version": {
            "endpoint": lambda project_id, service_name: f"https://appengine.googleapis.com/v1/apps/{project_id}/services/{service_name}/versions",
            "transform": lambda data: [ver.get("id") for ver in data.get("versions", []) if isinstance(ver, dict) and ver.get("id")],
            "depends_on": "service",
        },
        "instance_id": {
            "endpoint": lambda project_id, service_name, version_id: f"https://appengine.googleapis.com/v1/apps/{project_id}/services/{service_name}/versions/{version_id}/instances",
            "transform": lambda data: [inst.get("id") for inst in data.get("instances", []) if isinstance(inst, dict) and inst.get("id")],
            "depends_on": ["service", "version"],
        },
    },

    # Storage Services
    "cloudsql_database": {
        "database_id": {
            "endpoint": lambda project_id: f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project_id}/instances",
            "transform": lambda data: [inst.get("name") for inst in data.get("items", []) if isinstance(inst, dict) and inst.get("name")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions", 
            "transform": extract_names_from_items,
        },
    },

    "gcs_bucket": {
        "bucket_name": {
            "endpoint": lambda project_id: f"https://storage.googleapis.com/storage/v1/b?project={project_id}",
            "transform": lambda data: [bucket.get("name") for bucket in data.get("items", []) if isinstance(bucket, dict) and bucket.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://storage.googleapis.com/storage/v1/b?project={project_id}",
            "transform": lambda data: list(set(bucket.get("location") for bucket in data.get("items", []) if isinstance(bucket, dict) and bucket.get("location"))),
        },
    },

    "bigtable_instance": {
        "instance_id": {
            "endpoint": lambda project_id: f"https://bigtableadmin.googleapis.com/v2/projects/{project_id}/instances",
            "transform": lambda data: [inst.get("name", "").split("/")[-1] for inst in data.get("instances", []) if isinstance(inst, dict) and inst.get("name")],
        },
        "cluster": {
            "endpoint": lambda project_id, instance_id: f"https://bigtableadmin.googleapis.com/v2/projects/{project_id}/instances/{instance_id}/clusters",
            "transform": lambda data: [cluster.get("name", "").split("/")[-1] for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("name")],
            "depends_on": "instance_id",
        },
        "zone": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones",
            "transform": extract_names_from_items,
        },
    },

    "datastore_database": {
        "database_id": {
            "endpoint": lambda project_id: f"https://datastore.googleapis.com/v1/projects/{project_id}/databases",
            "transform": lambda data: [db.get("name", "").split("/")[-1] for db in data.get("databases", [])] or ["(default)"],
        },
    },

    "spanner_instance": {
        "instance_id": {
            "endpoint": lambda project_id: f"https://spanner.googleapis.com/v1/projects/{project_id}/instances",
            "transform": lambda data: [inst.get("name", "").split("/")[-1] for inst in data.get("instances", []) if isinstance(inst, dict) and inst.get("name")],
        },
        "database": {
            "endpoint": lambda project_id, instance_id: f"https://spanner.googleapis.com/v1/projects/{project_id}/instances/{instance_id}/databases",
            "transform": lambda data: [db.get("name", "").split("/")[-1] for db in data.get("databases", []) if isinstance(db, dict) and db.get("name")],
            "depends_on": "instance_id",
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "firestore_database": {
        "database_id": {
            "endpoint": lambda project_id: f"https://firestore.googleapis.com/v1/projects/{project_id}/databases",
            "transform": lambda data: [db.get("name", "").split("/")[-1] for db in data.get("databases", [])] or ["(default)"],
        },
    },

    # Networking Services
    "vpc_flow_log": {
        "subnetwork_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/subnetworks",
            "transform": lambda data: extract_from_aggregated(data, "subnetworks"),
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
        "vpc_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks",
            "transform": extract_names_from_items,
        },
    },

    "gce_network": {
        "network_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks",
            "transform": extract_names_from_items,
        },
    },

    "gce_subnetwork": {
        "subnetwork_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/subnetworks",
            "transform": lambda data: extract_from_aggregated(data, "subnetworks"),
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "vpn_gateway": {
        "gateway_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/vpnGateways",
            "transform": lambda data: extract_from_aggregated(data, "vpnGateways"),
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    # Load Balancers
    "http_load_balancer": {
        "forwarding_rule_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/forwardingRules",
            "transform": extract_names_from_items,
        },
        "target_proxy_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/targetHttpProxies",
            "transform": extract_names_from_items,
        },
        "url_map_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/urlMaps",
            "transform": extract_names_from_items,
        },
    },

    "tcp_ssl_proxy_load_balancer": {
        "forwarding_rule_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/forwardingRules",
            "transform": extract_names_from_items,
        },
        "target_proxy_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/targetTcpProxies",
            "transform": extract_names_from_items,
        },
    },

    "internal_http_load_balancer": {
        "forwarding_rule_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/forwardingRules",
            "transform": lambda data: extract_from_aggregated(data, "forwardingRules"),
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "network_load_balancer": {
        "forwarding_rule_name": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/forwardingRules",
            "transform": lambda data: extract_from_aggregated(data, "forwardingRules"),
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    # Data & Analytics Services
    "bigquery_dataset": {
        "dataset_id": {
            "endpoint": lambda project_id: f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets",
            "transform": lambda data: [ds.get("datasetReference", {}).get("datasetId") for ds in data.get("datasets", []) if isinstance(ds, dict) and isinstance(ds.get("datasetReference"), dict) and ds.get("datasetReference", {}).get("datasetId")],
        },
    },

    "bigquery_project": {
        "project_id": {
            "endpoint": lambda project_id: "https://cloudresourcemanager.googleapis.com/v1/projects",
            "transform": lambda data: [proj.get("projectId") for proj in data.get("projects", []) if isinstance(proj, dict) and proj.get("projectId")],
        },
    },

    "dataflow_job": {
        "job_name": {
            "endpoint": lambda project_id: f"https://dataflow.googleapis.com/v1b3/projects/{project_id}/jobs",
            "transform": lambda data: [job.get("name") for job in data.get("jobs", []) if isinstance(job, dict) and job.get("name")],
        },
        "job_id": {
            "endpoint": lambda project_id: f"https://dataflow.googleapis.com/v1b3/projects/{project_id}/jobs",
            "transform": lambda data: [job.get("id") for job in data.get("jobs", []) if isinstance(job, dict) and job.get("id")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "dataproc_cluster": {
        "cluster_name": {
            "endpoint": lambda project_id: f"https://dataproc.googleapis.com/v1/projects/{project_id}/regions/-/clusters",
            "transform": lambda data: [cluster.get("clusterName") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("clusterName")],
        },
        "cluster_uuid": {
            "endpoint": lambda project_id: f"https://dataproc.googleapis.com/v1/projects/{project_id}/regions/-/clusters",
            "transform": lambda data: [cluster.get("clusterUuid") for cluster in data.get("clusters", []) if isinstance(cluster, dict) and cluster.get("clusterUuid")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "pubsub_topic": {
        "topic_id": {
            "endpoint": lambda project_id: f"https://pubsub.googleapis.com/v1/projects/{project_id}/topics",
            "transform": lambda data: [topic.get("name", "").split("/")[-1] for topic in data.get("topics", []) if isinstance(topic, dict) and topic.get("name")],
        },
    },

    "pubsub_subscription": {
        "subscription_id": {
            "endpoint": lambda project_id: f"https://pubsub.googleapis.com/v1/projects/{project_id}/subscriptions",
            "transform": lambda data: [sub.get("name", "").split("/")[-1] for sub in data.get("subscriptions", []) if isinstance(sub, dict) and sub.get("name")],
        },
    },

    # AI/ML Services
    "ml_job": {
        "job_id": {
            "endpoint": lambda project_id: f"https://ml.googleapis.com/v1/projects/{project_id}/jobs",
            "transform": lambda data: [job.get("jobId") for job in data.get("jobs", []) if isinstance(job, dict) and job.get("jobId")],
        },
        "task_name": {
            "endpoint": "#dynamic-task-names",
            "transform": lambda data: [],
        },
    },

    "aiplatform_training_job": {
        "job_id": {
            "endpoint": lambda project_id: f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/-/trainingPipelines",
            "transform": lambda data: [pipeline.get("name", "").split("/")[-1] for pipeline in data.get("trainingPipelines", []) if isinstance(pipeline, dict) and pipeline.get("name")],
        },
    },

    "aiplatform_endpoint": {
        "endpoint_id": {
            "endpoint": lambda project_id: f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/-/endpoints",
            "transform": lambda data: [ep.get("name", "").split("/")[-1] for ep in data.get("endpoints", []) if isinstance(ep, dict) and ep.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    # API & Developer Services
    "api_gateway": {
        "gateway_id": {
            "endpoint": lambda project_id: f"https://apigateway.googleapis.com/v1/projects/{project_id}/locations/-/gateways",
            "transform": lambda data: [gw.get("name", "").split("/")[-1] for gw in data.get("gateways", []) if isinstance(gw, dict) and gw.get("name")],
        },
        "api_id": {
            "endpoint": lambda project_id: f"https://apigateway.googleapis.com/v1/projects/{project_id}/locations/global/apis",
            "transform": lambda data: [api.get("name", "").split("/")[-1] for api in data.get("apis", []) if isinstance(api, dict) and api.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://apigateway.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "cloud_endpoints_service": {
        "service_name": {
            "endpoint": lambda project_id: f"https://servicemanagement.googleapis.com/v1/services?producerProjectId={project_id}",
            "transform": lambda data: [svc.get("serviceName") for svc in data.get("services", []) if isinstance(svc, dict) and svc.get("serviceName")],
        },
    },

    "cloud_build": {
        "build_id": {
            "endpoint": lambda project_id: f"https://cloudbuild.googleapis.com/v1/projects/{project_id}/builds",
            "transform": lambda data: [build.get("id") for build in data.get("builds", []) if isinstance(build, dict) and build.get("id")],
        },
        "build_trigger_id": {
            "endpoint": lambda project_id: f"https://cloudbuild.googleapis.com/v1/projects/{project_id}/triggers",
            "transform": lambda data: [trigger.get("id") for trigger in data.get("triggers", []) if isinstance(trigger, dict) and trigger.get("id")],
        },
    },

    "cloud_source_repo": {
        "repo_name": {
            "endpoint": lambda project_id: f"https://sourcerepo.googleapis.com/v1/projects/{project_id}/repos",
            "transform": lambda data: [repo.get("name", "").split("/")[-1] for repo in data.get("repos", []) if isinstance(repo, dict) and repo.get("name")],
        },
    },

    # Monitoring & Operations
    "uptime_url": {
        "check_id": {
            "endpoint": lambda project_id: f"https://monitoring.googleapis.com/v3/projects/{project_id}/uptimeCheckConfigs",
            "transform": lambda data: [check.get("name", "").split("/")[-1] for check in data.get("uptimeCheckConfigs", []) if isinstance(check, dict) and check.get("name")],
        },
        "checker_location": {
            "endpoint": None,  # Static data
            "transform": lambda data: [
                "us-central1", "us-east1", "us-west1", "us-east4", "us-west2", "us-west3", "us-west4",
                "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6", "europe-north1",
                "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
                "asia-south1", "asia-southeast1", "asia-southeast2", "australia-southeast1", "southamerica-east1",
            ],
        },
    },

    "logging_sink": {
        "sink_name": {
            "endpoint": lambda project_id: f"https://logging.googleapis.com/v2/projects/{project_id}/sinks",
            "transform": lambda data: [sink.get("name") for sink in data.get("sinks", []) if isinstance(sink, dict) and sink.get("name")],
        },
    },

    # Security & Identity
    "service_account": {
        "email_id": {
            "endpoint": lambda project_id: f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts",
            "transform": lambda data: [acc.get("email") for acc in data.get("accounts", []) if isinstance(acc, dict) and acc.get("email")],
        },
        "unique_id": {
            "endpoint": lambda project_id: f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts",
            "transform": lambda data: [acc.get("uniqueId") for acc in data.get("accounts", []) if isinstance(acc, dict) and acc.get("uniqueId")],
        },
    },

    # Scheduler & Tasks
    "cloud_scheduler_job": {
        "job_id": {
            "endpoint": lambda project_id, location: f"https://cloudscheduler.googleapis.com/v1/projects/{project_id}/locations/{location}/jobs",
            "transform": lambda data: [job.get("name", "").split("/")[-1] for job in data.get("jobs", []) if isinstance(job, dict) and job.get("name")],
            "depends_on": "location",
        },
        "location": {
            "endpoint": lambda project_id: f"https://cloudscheduler.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "cloud_tasks_queue": {
        "queue_id": {
            "endpoint": lambda project_id, location: f"https://cloudtasks.googleapis.com/v2/projects/{project_id}/locations/{location}/queues",
            "transform": lambda data: [queue.get("name", "").split("/")[-1] for queue in data.get("queues", []) if isinstance(queue, dict) and queue.get("name")],
            "depends_on": "location",
        },
        "location": {
            "endpoint": lambda project_id: f"https://cloudtasks.googleapis.com/v2/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    # Cache Services
    "redis_instance": {
        "instance_id": {
            "endpoint": lambda project_id: f"https://redis.googleapis.com/v1/projects/{project_id}/locations/-/instances",
            "transform": lambda data: [inst.get("name", "").split("/")[-1] for inst in data.get("instances", []) if isinstance(inst, dict) and inst.get("name")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    "memcache_instance": {
        "instance_id": {
            "endpoint": lambda project_id: f"https://memcache.googleapis.com/v1/projects/{project_id}/locations/-/instances",
            "transform": lambda data: [inst.get("name", "").split("/")[-1] for inst in data.get("instances", []) if isinstance(inst, dict) and inst.get("name")],
        },
        "region": {
            "endpoint": lambda project_id: f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions",
            "transform": extract_names_from_items,
        },
    },

    # Other Services
    "cloud_composer_environment": {
        "environment_name": {
            "endpoint": lambda project_id: f"https://composer.googleapis.com/v1/projects/{project_id}/locations/-/environments",
            "transform": lambda data: [env.get("name", "").split("/")[-1] for env in data.get("environments", []) if isinstance(env, dict) and env.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://composer.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "datastream_stream": {
        "stream_id": {
            "endpoint": lambda project_id: f"https://datastream.googleapis.com/v1/projects/{project_id}/locations/-/streams",
            "transform": lambda data: [stream.get("name", "").split("/")[-1] for stream in data.get("streams", []) if isinstance(stream, dict) and stream.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://datastream.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    "cloud_dns_zone": {
        "zone_name": {
            "endpoint": lambda project_id: f"https://dns.googleapis.com/dns/v1/projects/{project_id}/managedZones",
            "transform": lambda data: [zone.get("name") for zone in data.get("managedZones", []) if isinstance(zone, dict) and zone.get("name")],
        },
    },

    "certificate_manager": {
        "certificate_name": {
            "endpoint": lambda project_id: f"https://certificatemanager.googleapis.com/v1/projects/{project_id}/locations/-/certificates",
            "transform": lambda data: [cert.get("name", "").split("/")[-1] for cert in data.get("certificates", []) if isinstance(cert, dict) and cert.get("name")],
        },
        "location": {
            "endpoint": lambda project_id: f"https://certificatemanager.googleapis.com/v1/projects/{project_id}/locations",
            "transform": lambda data: [loc.get("locationId") for loc in data.get("locations", []) if isinstance(loc, dict) and loc.get("locationId")],
        },
    },

    # Global/Generic Resources
    "global": {
        # Global resources don't have specific endpoints
        # They should be handled at the application level
    },

    "project": {
        "project_id": {
            "endpoint": lambda project_id: "https://cloudresourcemanager.googleapis.com/v1/projects",
            "transform": lambda data: [proj.get("projectId") for proj in data.get("projects", []) if isinstance(proj, dict) and proj.get("projectId")],
        },
    },
}