// export const GCP_RESOURCE_MAPPINGS = {
//     // Compute Services
//     cloud_run_revision: {
//         id: "Cloud Run Revision",
//         labels: ["service_name", "revision_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     k8s_container: {
//         id: "Kubernetes Container",
//         labels: ["cluster_name", "namespace_name", "pod_name", "container_name"],
//         additionalQueries: ["severity", "timestamp", "textPayload", "jsonPayload"],
//     },
//     k8s_cluster: {
//         id: "Kubernetes Cluster",
//         labels: ["cluster_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     k8s_node: {
//         id: "Kubernetes Node",
//         labels: ["cluster_name", "node_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     k8s_pod: {
//         id: "Kubernetes Pod",
//         labels: ["cluster_name", "namespace_name", "pod_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     gce_instance: {
//         id: "GCE Instance",
//         labels: ["instance_id", "zone"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "labels"],
//     },
//     cloud_function: {
//         id: "Cloud Function",
//         labels: ["function_name", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     gae_app: {
//         id: "App Engine App",
//         labels: ["service", "version", "instance_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },

//     // Storage Services
//     cloudsql_database: {
//         id: "Cloud SQL Database",
//         labels: ["database_id", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     gcs_bucket: {
//         id: "GCS Bucket",
//         labels: ["bucket_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     bigtable_instance: {
//         id: "Bigtable Instance",
//         labels: ["instance_id", "cluster", "zone"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     datastore_database: {
//         id: "Datastore Database",
//         labels: ["database_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     spanner_instance: {
//         id: "Spanner Instance",
//         labels: ["instance_id", "database", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     firestore_database: {
//         id: "Firestore Database",
//         labels: ["database_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Networking Services
//     vpc_flow_log: {
//         id: "VPC Flow Log",
//         labels: ["subnetwork_name", "region", "vpc_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     gce_network: {
//         id: "GCE Network",
//         labels: ["network_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     gce_subnetwork: {
//         id: "GCE Subnetwork",
//         labels: ["subnetwork_name", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     vpn_gateway: {
//         id: "VPN Gateway",
//         labels: ["gateway_name", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     http_load_balancer: {
//         id: "HTTP Load Balancer",
//         labels: ["forwarding_rule_name", "target_proxy_name", "url_map_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     tcp_ssl_proxy_load_balancer: {
//         id: "TCP/SSL Proxy Load Balancer",
//         labels: ["forwarding_rule_name", "target_proxy_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     internal_http_load_balancer: {
//         id: "Internal HTTP Load Balancer",
//         labels: ["forwarding_rule_name", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     network_load_balancer: {
//         id: "Network Load Balancer",
//         labels: ["forwarding_rule_name", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Data & Analytics Services
//     bigquery_dataset: {
//         id: "BigQuery Dataset",
//         labels: ["dataset_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     bigquery_project: {
//         id: "BigQuery Project",
//         labels: ["project_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     dataflow_job: {
//         id: "Dataflow Job",
//         labels: ["job_name", "job_id", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     dataproc_cluster: {
//         id: "Dataproc Cluster",
//         labels: ["cluster_name", "cluster_uuid", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     pubsub_topic: {
//         id: "Pub/Sub Topic",
//         labels: ["topic_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     pubsub_subscription: {
//         id: "Pub/Sub Subscription",
//         labels: ["subscription_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // AI/ML Services
//     ml_job: {
//         id: "ML Job",
//         labels: ["job_id", "task_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     aiplatform_training_job: {
//         id: "AI Platform Training Job",
//         labels: ["job_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     aiplatform_endpoint: {
//         id: "AI Platform Endpoint",
//         labels: ["endpoint_id", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // API & Developer Services
//     api_gateway: {
//         id: "API Gateway",
//         labels: ["gateway_id", "api_id", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     cloud_endpoints_service: {
//         id: "Cloud Endpoints Service",
//         labels: ["service_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     cloud_build: {
//         id: "Cloud Build",
//         labels: ["build_id", "build_trigger_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     cloud_source_repo: {
//         id: "Cloud Source Repository",
//         labels: ["repo_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Monitoring & Operations
//     uptime_url: {
//         id: "Uptime URL",
//         labels: ["check_id", "checker_location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     logging_sink: {
//         id: "Logging Sink",
//         labels: ["sink_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Security & Identity
//     service_account: {
//         id: "Service Account",
//         labels: ["email_id", "unique_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Scheduler & Tasks
//     cloud_scheduler_job: {
//         id: "Cloud Scheduler Job",
//         labels: ["job_id", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     cloud_tasks_queue: {
//         id: "Cloud Tasks Queue",
//         labels: ["queue_id", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Cache Services
//     redis_instance: {
//         id: "Redis Instance",
//         labels: ["instance_id", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     memcache_instance: {
//         id: "Memcache Instance",
//         labels: ["instance_id", "region"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Other Services
//     cloud_composer_environment: {
//         id: "Cloud Composer Environment",
//         labels: ["environment_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
//     datastream_stream: {
//         id: "Datastream Stream",
//         labels: ["stream_id", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     cloud_dns_zone: {
//         id: "Cloud DNS Zone",
//         labels: ["zone_name"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },
//     certificate_manager: {
//         id: "Certificate Manager",
//         labels: ["certificate_name", "location"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload"],
//     },

//     // Global/Generic Resources
//     global: {
//         id: "Global",
//         labels: [],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload", "labels"],
//     },
//     project: {
//         id: "Project",
//         labels: ["project_id"],
//         additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
//     },
// };

// // Additional query value mappings for common fields
// export const QUERY_VALUE_MAPPINGS = {
//     severity: ["DEFAULT", "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY"],
//     timestamp: ["last_hour", "last_24_hours", "last_7_days", "custom_range"],
//     location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1", "global"],
//     region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
//     zone: ["us-central1-a", "us-central1-b", "us-east1-a", "us-west1-a", "europe-west1-a"],
// };

// export function getServiceById(id: string) {
//     return GCP_RESOURCE_MAPPINGS[id as keyof typeof GCP_RESOURCE_MAPPINGS];
// }


// data/gcpResourceMappings.ts - Complete GCP Resource Mappings Configuration

export const GCP_RESOURCE_MAPPINGS = {
    // Compute Services
    cloud_run_revision: {
        id: "Cloud Run Revision",
        labels: ["service_name", "revision_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    k8s_container: {
        id: "Kubernetes Container",
        labels: ["cluster_name", "namespace_name", "pod_name", "container_name"],
        additionalQueries: ["severity", "timestamp", "textPayload", "jsonPayload"],
    },
    k8s_cluster: {
        id: "Kubernetes Cluster",
        labels: ["cluster_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    k8s_node: {
        id: "Kubernetes Node",
        labels: ["cluster_name", "node_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    k8s_pod: {
        id: "Kubernetes Pod",
        labels: ["cluster_name", "namespace_name", "pod_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    gce_instance: {
        id: "GCE Instance",
        labels: ["instance_id", "zone"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "labels"],
    },
    cloud_function: {
        id: "Cloud Function",
        labels: ["function_name", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    gae_app: {
        id: "App Engine App",
        labels: ["service", "version", "instance_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },

    // Storage Services
    cloudsql_database: {
        id: "Cloud SQL Database",
        labels: ["database_id", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    gcs_bucket: {
        id: "GCS Bucket",
        labels: ["bucket_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    bigtable_instance: {
        id: "Bigtable Instance",
        labels: ["instance_id", "cluster", "zone"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    datastore_database: {
        id: "Datastore Database",
        labels: ["database_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    spanner_instance: {
        id: "Spanner Instance",
        labels: ["instance_id", "database", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    firestore_database: {
        id: "Firestore Database",
        labels: ["database_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Networking Services
    vpc_flow_log: {
        id: "VPC Flow Log",
        labels: ["subnetwork_name", "region", "vpc_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    gce_network: {
        id: "GCE Network",
        labels: ["network_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    gce_subnetwork: {
        id: "GCE Subnetwork",
        labels: ["subnetwork_name", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    vpn_gateway: {
        id: "VPN Gateway",
        labels: ["gateway_name", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    http_load_balancer: {
        id: "HTTP Load Balancer",
        labels: ["forwarding_rule_name", "target_proxy_name", "url_map_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    tcp_ssl_proxy_load_balancer: {
        id: "TCP/SSL Proxy Load Balancer",
        labels: ["forwarding_rule_name", "target_proxy_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    internal_http_load_balancer: {
        id: "Internal HTTP Load Balancer",
        labels: ["forwarding_rule_name", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    network_load_balancer: {
        id: "Network Load Balancer",
        labels: ["forwarding_rule_name", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Data & Analytics Services
    bigquery_dataset: {
        id: "BigQuery Dataset",
        labels: ["dataset_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    bigquery_project: {
        id: "BigQuery Project",
        labels: ["project_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    dataflow_job: {
        id: "Dataflow Job",
        labels: ["job_name", "job_id", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    dataproc_cluster: {
        id: "Dataproc Cluster",
        labels: ["cluster_name", "cluster_uuid", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    pubsub_topic: {
        id: "Pub/Sub Topic",
        labels: ["topic_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    pubsub_subscription: {
        id: "Pub/Sub Subscription",
        labels: ["subscription_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // AI/ML Services
    ml_job: {
        id: "ML Job",
        labels: ["job_id", "task_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    aiplatform_training_job: {
        id: "AI Platform Training Job",
        labels: ["job_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    aiplatform_endpoint: {
        id: "AI Platform Endpoint",
        labels: ["endpoint_id", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // API & Developer Services
    api_gateway: {
        id: "API Gateway",
        labels: ["gateway_id", "api_id", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    cloud_endpoints_service: {
        id: "Cloud Endpoints Service",
        labels: ["service_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    cloud_build: {
        id: "Cloud Build",
        labels: ["build_id", "build_trigger_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    cloud_source_repo: {
        id: "Cloud Source Repository",
        labels: ["repo_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Monitoring & Operations
    uptime_url: {
        id: "Uptime URL",
        labels: ["check_id", "checker_location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    logging_sink: {
        id: "Logging Sink",
        labels: ["sink_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Security & Identity
    service_account: {
        id: "Service Account",
        labels: ["email_id", "unique_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Scheduler & Tasks
    cloud_scheduler_job: {
        id: "Cloud Scheduler Job",
        labels: ["job_id", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    cloud_tasks_queue: {
        id: "Cloud Tasks Queue",
        labels: ["queue_id", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Cache Services
    redis_instance: {
        id: "Redis Instance",
        labels: ["instance_id", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    memcache_instance: {
        id: "Memcache Instance",
        labels: ["instance_id", "region"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Other Services
    cloud_composer_environment: {
        id: "Cloud Composer Environment",
        labels: ["environment_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
    datastream_stream: {
        id: "Datastream Stream",
        labels: ["stream_id", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    cloud_dns_zone: {
        id: "Cloud DNS Zone",
        labels: ["zone_name"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },
    certificate_manager: {
        id: "Certificate Manager",
        labels: ["certificate_name", "location"],
        additionalQueries: ["severity", "timestamp", "jsonPayload"],
    },

    // Global/Generic Resources
    global: {
        id: "Global",
        labels: [],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload", "labels"],
    },
    project: {
        id: "Project",
        labels: ["project_id"],
        additionalQueries: ["severity", "timestamp", "jsonPayload", "textPayload"],
    },
};

// Additional query value mappings for common fields
export const QUERY_VALUE_MAPPINGS = {
    severity: ["DEFAULT", "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY"],
    timestamp: ["last_hour", "last_24_hours", "last_7_days", "custom_range"],
    location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1", "global"],
    region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    zone: ["us-central1-a", "us-central1-b", "us-east1-a", "us-west1-a", "europe-west1-a"],
};

// Helper function to get service by ID
export function getServiceById(id: string) {
    return GCP_RESOURCE_MAPPINGS[id as keyof typeof GCP_RESOURCE_MAPPINGS];
}

// Helper function to get all resource type keys
export function getAllResourceTypes(): string[] {
    return Object.keys(GCP_RESOURCE_MAPPINGS);
}

// Helper function to get labels for a resource type
export function getLabelsForResourceType(resourceType: string): string[] {
    return GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS]?.labels || [];
}

// Helper function to get additional queries for a resource type
export function getAdditionalQueriesForResourceType(resourceType: string): string[] {
    return GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS]?.additionalQueries || [];
}

// Helper function to get display name for resource type
export function getDisplayNameForResourceType(resourceType: string): string {
    return GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS]?.id || resourceType
        .replace(/_/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase());
}