// Complete fallback test data for all GCP resource types
export const FALLBACK_DATA: Record<string, Record<string, string[]>> = {
    // // Compute Services
    // cloud_run_revision: {
    //     service_name: ["api-service", "web-service", "worker-service", "auth-service", "payment-service"],
    //     revision_name: ["api-service-00001", "api-service-00002", "web-service-00001", "worker-service-00001", "auth-service-00003"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // k8s_container: {
    //     cluster_name: ["production-cluster", "staging-cluster", "dev-cluster", "test-cluster"],
    //     namespace_name: ["default", "kube-system", "monitoring", "application", "ingress-nginx", "cert-manager"],
    //     pod_name: ["api-pod-1", "api-pod-2", "worker-pod-1", "nginx-pod-1", "database-pod-1"],
    //     container_name: ["api-container", "worker-container", "sidecar", "nginx", "prometheus"],
    // },

    // k8s_cluster: {
    //     cluster_name: ["production-cluster", "staging-cluster", "dev-cluster", "test-cluster"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // k8s_node: {
    //     cluster_name: ["production-cluster", "staging-cluster", "dev-cluster", "test-cluster"],
    //     node_name: ["node-1", "node-2", "node-3", "node-pool-1-abc", "node-pool-2-def", "preemptible-node-1"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // k8s_pod: {
    //     cluster_name: ["production-cluster", "staging-cluster", "dev-cluster", "test-cluster"],
    //     namespace_name: ["default", "kube-system", "monitoring", "application", "ingress-nginx"],
    //     pod_name: ["api-pod-1", "api-pod-2", "worker-pod-1", "nginx-pod-1", "database-pod-1"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // gce_instance: {
    //     instance_id: ["1234567890123456789", "2345678901234567890", "3456789012345678901", "4567890123456789012"],
    //     zone: ["us-central1-a", "us-central1-b", "us-central1-c", "us-east1-a", "us-west1-a", "europe-west1-a"],
    // },

    // cloud_function: {
    //     function_name: ["process-data", "send-email", "validate-input", "resize-image", "generate-report", "webhook-handler"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // gae_app: {
    //     service: ["default", "api", "worker", "admin", "auth"],
    //     version: ["20240101t120000", "20240102t130000", "v1", "v2", "staging"],
    //     instance_id: ["00c61b117c123456", "00c61b117c654321", "dynamic-1", "dynamic-2", "auto-scaled-3"],
    // },

    // // Storage Services
    // cloudsql_database: {
    //     database_id: ["mysql-instance-1", "postgres-instance-1", "sqlserver-instance-1", "mysql-prod", "postgres-dev"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // gcs_bucket: {
    //     bucket_name: ["my-data-bucket", "backup-bucket", "static-assets", "user-uploads", "analytics-data", "ml-models"],
    //     location: ["us-central1", "us-east1", "global", "europe-west1", "multi-region"],
    // },

    // bigtable_instance: {
    //     instance_id: ["bigtable-prod", "bigtable-dev", "analytics-bt", "timeseries-bt"],
    //     cluster: ["cluster-1", "cluster-2", "prod-cluster", "dev-cluster"],
    //     zone: ["us-central1-a", "us-central1-b", "us-east1-a", "europe-west1-a"],
    // },

    // datastore_database: {
    //     database_id: ["(default)", "analytics-db", "user-db", "session-db"],
    // },

    // spanner_instance: {
    //     instance_id: ["spanner-prod", "spanner-test", "analytics-spanner", "financial-spanner"],
    //     database: ["users", "transactions", "analytics", "logs", "inventory"],
    //     region: ["us-central1", "us-east1", "europe-west1", "multi-region"],
    // },

    // firestore_database: {
    //     database_id: ["(default)", "analytics", "user-data", "chat-data"],
    // },

    // // Networking Services
    // vpc_flow_log: {
    //     subnetwork_name: ["default", "private-subnet", "public-subnet", "db-subnet", "k8s-subnet"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    //     vpc_name: ["default", "production-vpc", "staging-vpc", "development-vpc"],
    // },

    // gce_network: {
    //     network_name: ["default", "production-vpc", "staging-vpc", "development-vpc", "peering-network"],
    // },

    // gce_subnetwork: {
    //     subnetwork_name: ["default", "private-subnet", "public-subnet", "db-subnet", "k8s-subnet", "gke-nodes"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // vpn_gateway: {
    //     gateway_name: ["vpn-gateway-1", "vpn-gateway-2", "site-to-site-vpn", "branch-office-vpn"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // http_load_balancer: {
    //     forwarding_rule_name: ["http-lb-rule", "api-lb-rule", "web-lb-rule", "cdn-lb-rule"],
    //     target_proxy_name: ["http-lb-proxy", "api-lb-proxy", "web-lb-proxy", "cdn-lb-proxy"],
    //     url_map_name: ["http-lb-map", "api-lb-map", "web-lb-map", "cdn-lb-map"],
    // },

    // tcp_ssl_proxy_load_balancer: {
    //     forwarding_rule_name: ["tcp-lb-rule", "ssl-lb-rule", "database-lb-rule"],
    //     target_proxy_name: ["tcp-lb-proxy", "ssl-lb-proxy", "database-lb-proxy"],
    // },

    // internal_http_load_balancer: {
    //     forwarding_rule_name: ["internal-lb-rule", "backend-lb-rule", "microservices-lb"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // network_load_balancer: {
    //     forwarding_rule_name: ["network-lb-rule", "tcp-lb-rule", "udp-lb-rule"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // // Data & Analytics Services
    // bigquery_dataset: {
    //     dataset_id: ["analytics", "logs", "user_data", "transactions", "events", "ml_features", "dwh_staging"],
    // },

    // bigquery_project: {
    //     project_id: ["my-project-123", "analytics-project", "data-warehouse", "ml-project"],
    // },

    // dataflow_job: {
    //     job_name: ["process-events", "etl-pipeline", "data-transform", "stream-processor", "batch-loader"],
    //     job_id: ["2024-01-01_12_00_00-123456789", "2024-01-02_14_30_00-987654321", "streaming-job-abc123"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // dataproc_cluster: {
    //     cluster_name: ["spark-cluster", "hadoop-cluster", "analytics-cluster", "ml-training-cluster"],
    //     cluster_uuid: ["12345678-1234-1234-1234-123456789012", "87654321-4321-4321-4321-210987654321"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // pubsub_topic: {
    //     topic_id: ["user-events", "system-logs", "notifications", "analytics-events", "order-events", "payment-events"],
    // },

    // pubsub_subscription: {
    //     subscription_id: ["events-processor", "log-analyzer", "notification-handler", "analytics-consumer", "order-processor"],
    // },

    // // AI/ML Services
    // ml_job: {
    //     job_id: ["training_job_123", "prediction_job_456", "evaluation_job_789", "hyperparameter_tuning_012"],
    //     task_name: ["train", "predict", "evaluate", "preprocess", "feature_extraction"],
    // },

    // aiplatform_training_job: {
    //     job_id: ["training-pipeline-123", "custom-training-456", "automl-training-789"],
    // },

    // aiplatform_endpoint: {
    //     endpoint_id: ["model-endpoint-123", "prediction-endpoint-456", "automl-endpoint-789"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // // API & Developer Services
    // api_gateway: {
    //     gateway_id: ["api-gateway-1", "public-api-gateway", "internal-gateway", "partner-gateway"],
    //     api_id: ["users-api", "orders-api", "auth-api", "payment-api"],
    //     location: ["us-central1", "global", "europe-west1", "asia-east1"],
    // },

    // cloud_endpoints_service: {
    //     service_name: [
    //         "users-api.endpoints.my-project.cloud.goog",
    //         "orders-api.endpoints.my-project.cloud.goog",
    //         "auth-api.endpoints.my-project.cloud.goog"
    //     ],
    // },

    // cloud_build: {
    //     build_id: ["12345678-1234-1234-1234-123456789012", "87654321-4321-4321-4321-210987654321"],
    //     build_trigger_id: ["github-trigger-1", "manual-trigger-2", "webhook-trigger-3"],
    // },

    // cloud_source_repo: {
    //     repo_name: ["my-app-repo", "backend-repo", "frontend-repo", "infrastructure-repo"],
    // },

    // // Monitoring & Operations
    // uptime_url: {
    //     check_id: ["website-check", "api-check", "database-check", "service-health-check"],
    //     checker_location: ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"],
    // },

    // logging_sink: {
    //     sink_name: ["audit-logs-sink", "error-logs-sink", "analytics-sink", "security-sink"],
    // },

    // // Security & Identity
    // service_account: {
    //     email_id: [
    //         "compute@my-project.iam.gserviceaccount.com",
    //         "storage@my-project.iam.gserviceaccount.com",
    //         "bigquery@my-project.iam.gserviceaccount.com",
    //         "dataflow@my-project.iam.gserviceaccount.com"
    //     ],
    //     unique_id: ["123456789012345678901", "210987654321098765432", "345678901234567890123"],
    // },

    // // Scheduler & Tasks
    // cloud_scheduler_job: {
    //     job_id: ["daily-backup", "weekly-report", "hourly-sync", "monthly-cleanup"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // cloud_tasks_queue: {
    //     queue_id: ["email-queue", "processing-queue", "webhook-queue", "notification-queue"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // // Cache Services
    // redis_instance: {
    //     instance_id: ["redis-cache-1", "session-store", "rate-limiter", "chat-cache"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // memcache_instance: {
    //     instance_id: ["memcache-1", "cache-cluster", "session-cache", "query-cache"],
    //     region: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // // Other Services
    // cloud_composer_environment: {
    //     environment_name: ["airflow-prod", "data-pipeline", "etl-environment", "ml-pipeline"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // datastream_stream: {
    //     stream_id: ["mysql-to-bq", "postgres-to-gcs", "realtime-sync", "cdc-stream"],
    //     location: ["us-central1", "us-east1", "us-west1", "europe-west1"],
    // },

    // cloud_dns_zone: {
    //     zone_name: ["my-domain-com", "api-domain-com", "internal-zone", "staging-domain-com"],
    // },

    // certificate_manager: {
    //     certificate_name: ["ssl-cert-1", "api-cert", "wildcard-cert", "internal-cert"],
    //     location: ["global", "us-central1", "us-east1", "europe-west1"],
    // },

    // // Global/Generic Resources
    // global: {
    //     // Global resources don't have specific labels
    // },

    // project: {
    //     project_id: ["my-project-123", "production-project", "staging-project", "development-project"],
    // },
};