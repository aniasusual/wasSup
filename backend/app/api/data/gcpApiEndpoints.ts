// Complete API endpoints configuration - COMPREHENSIVE VERSION
export const GCP_API_ENDPOINTS = {
    // Compute Services
    cloud_run_revision: {
        service_name: {
            endpoint: (projectId: string) =>
                `https://run.googleapis.com/v1/projects/${projectId}/locations/-/services`,
            transform: (data: any) =>
                data.items?.map((s: any) => s.metadata?.name) || [],
        },
        revision_name: {
            endpoint: (projectId: string, serviceName: string) =>
                `https://run.googleapis.com/v1/projects/${projectId}/locations/-/services/${serviceName}/revisions`,
            transform: (data: any) =>
                data.items?.map((r: any) => r.metadata?.name) || [],
            dependsOn: "service_name",
        },
        location: {
            endpoint: (projectId: string) =>
                `https://run.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    k8s_container: {
        cluster_name: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations/-/clusters`,
            transform: (data: any) => data.clusters?.map((c: any) => c.name) || [],
        },
        namespace_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
        pod_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
        container_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
    },

    k8s_cluster: {
        cluster_name: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations/-/clusters`,
            transform: (data: any) => data.clusters?.map((c: any) => c.name) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    k8s_node: {
        cluster_name: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations/-/clusters`,
            transform: (data: any) => data.clusters?.map((c: any) => c.name) || [],
        },
        node_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    k8s_pod: {
        cluster_name: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations/-/clusters`,
            transform: (data: any) => data.clusters?.map((c: any) => c.name) || [],
        },
        namespace_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
        pod_name: {
            // Requires Kubernetes API access through cluster proxy
            endpoint: (projectId: string) => `#kubernetes-api-required`,
            transform: (data: any) => [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://container.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    gce_instance: {
        instance_id: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/instances`,
            transform: (data: any) => {
                const instances: string[] = [];
                Object.values(data.items || {}).forEach((zoneData: any) => {
                    if (zoneData.instances) {
                        instances.push(...zoneData.instances.map((i: any) => i.id));
                    }
                });
                return instances;
            },
        },
        zone: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/zones`,
            transform: (data: any) => data.items?.map((z: any) => z.name) || [],
        },
    },

    cloud_function: {
        function_name: {
            endpoint: (projectId: string) =>
                `https://cloudfunctions.googleapis.com/v1/projects/${projectId}/locations/-/functions`,
            transform: (data: any) =>
                data.functions?.map((f: any) => f.name.split("/").pop()) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://cloudfunctions.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    gae_app: {
        service: {
            endpoint: (projectId: string) =>
                `https://appengine.googleapis.com/v1/apps/${projectId}/services`,
            transform: (data: any) => data.services?.map((s: any) => s.id) || [],
        },
        version: {
            endpoint: (projectId: string, serviceName: string) =>
                `https://appengine.googleapis.com/v1/apps/${projectId}/services/${serviceName}/versions`,
            transform: (data: any) => data.versions?.map((v: any) => v.id) || [],
            dependsOn: "service",
        },
        instance_id: {
            endpoint: (projectId: string, serviceName: string, versionId: string) =>
                `https://appengine.googleapis.com/v1/apps/${projectId}/services/${serviceName}/versions/${versionId}/instances`,
            transform: (data: any) => data.instances?.map((i: any) => i.id) || [],
            dependsOn: ["service", "version"],
        },
    },

    // Storage Services
    cloudsql_database: {
        database_id: {
            endpoint: (projectId: string) =>
                `https://sqladmin.googleapis.com/sql/v1beta4/projects/${projectId}/instances`,
            transform: (data: any) => data.items?.map((i: any) => i.name) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    gcs_bucket: {
        bucket_name: {
            endpoint: (projectId: string) =>
                `https://storage.googleapis.com/storage/v1/b?project=${projectId}`,
            transform: (data: any) => data.items?.map((b: any) => b.name) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://storage.googleapis.com/storage/v1/b?project=${projectId}`,
            transform: (data: any) => {
                const locations = new Set();
                data.items?.forEach((b: any) => {
                    if (b.location) locations.add(b.location);
                });
                return Array.from(locations);
            },
        },
    },

    bigtable_instance: {
        instance_id: {
            endpoint: (projectId: string) =>
                `https://bigtableadmin.googleapis.com/v2/projects/${projectId}/instances`,
            transform: (data: any) =>
                data.instances?.map((i: any) => i.name.split("/").pop()) || [],
        },
        cluster: {
            endpoint: (projectId: string, instanceId: string) =>
                `https://bigtableadmin.googleapis.com/v2/projects/${projectId}/instances/${instanceId}/clusters`,
            transform: (data: any) =>
                data.clusters?.map((c: any) => c.name.split("/").pop()) || [],
            dependsOn: "instance_id",
        },
        zone: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/zones`,
            transform: (data: any) => data.items?.map((z: any) => z.name) || [],
        },
    },

    datastore_database: {
        database_id: {
            endpoint: (projectId: string) =>
                `https://datastore.googleapis.com/v1/projects/${projectId}/databases`,
            transform: (data: any) =>
                data.databases?.map((d: any) => d.name.split("/").pop()) || ["(default)"],
        },
    },

    spanner_instance: {
        instance_id: {
            endpoint: (projectId: string) =>
                `https://spanner.googleapis.com/v1/projects/${projectId}/instances`,
            transform: (data: any) =>
                data.instances?.map((i: any) => i.name.split("/").pop()) || [],
        },
        database: {
            endpoint: (projectId: string, instanceId: string) =>
                `https://spanner.googleapis.com/v1/projects/${projectId}/instances/${instanceId}/databases`,
            transform: (data: any) =>
                data.databases?.map((d: any) => d.name.split("/").pop()) || [],
            dependsOn: "instance_id",
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    firestore_database: {
        database_id: {
            endpoint: (projectId: string) =>
                `https://firestore.googleapis.com/v1/projects/${projectId}/databases`,
            transform: (data: any) =>
                data.databases?.map((d: any) => d.name.split("/").pop()) || ["(default)"],
        },
    },

    // Networking Services
    vpc_flow_log: {
        subnetwork_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/subnetworks`,
            transform: (data: any) => {
                const subnetworks: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.subnetworks) {
                        subnetworks.push(
                            ...regionData.subnetworks.map((s: any) => s.name)
                        );
                    }
                });
                return subnetworks;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
        vpc_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/networks`,
            transform: (data: any) => data.items?.map((n: any) => n.name) || [],
        },
    },

    gce_network: {
        network_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/networks`,
            transform: (data: any) => data.items?.map((n: any) => n.name) || [],
        },
    },

    gce_subnetwork: {
        subnetwork_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/subnetworks`,
            transform: (data: any) => {
                const subnetworks: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.subnetworks) {
                        subnetworks.push(
                            ...regionData.subnetworks.map((s: any) => s.name)
                        );
                    }
                });
                return subnetworks;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    vpn_gateway: {
        gateway_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/vpnGateways`,
            transform: (data: any) => {
                const gateways: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.vpnGateways) {
                        gateways.push(...regionData.vpnGateways.map((g: any) => g.name));
                    }
                });
                return gateways;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    // Load Balancers
    http_load_balancer: {
        forwarding_rule_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/forwardingRules`,
            transform: (data: any) => data.items?.map((f: any) => f.name) || [],
        },
        target_proxy_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/targetHttpProxies`,
            transform: (data: any) => data.items?.map((p: any) => p.name) || [],
        },
        url_map_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/urlMaps`,
            transform: (data: any) => data.items?.map((u: any) => u.name) || [],
        },
    },

    tcp_ssl_proxy_load_balancer: {
        forwarding_rule_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/forwardingRules`,
            transform: (data: any) => data.items?.map((f: any) => f.name) || [],
        },
        target_proxy_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/targetTcpProxies`,
            transform: (data: any) => data.items?.map((p: any) => p.name) || [],
        },
    },

    internal_http_load_balancer: {
        forwarding_rule_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/forwardingRules`,
            transform: (data: any) => {
                const rules: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.forwardingRules) {
                        rules.push(
                            ...regionData.forwardingRules.map((r: any) => r.name)
                        );
                    }
                });
                return rules;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    network_load_balancer: {
        forwarding_rule_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/forwardingRules`,
            transform: (data: any) => {
                const rules: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.forwardingRules) {
                        rules.push(
                            ...regionData.forwardingRules.map((r: any) => r.name)
                        );
                    }
                });
                return rules;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    // Data & Analytics Services
    bigquery_dataset: {
        dataset_id: {
            endpoint: (projectId: string) =>
                `https://bigquery.googleapis.com/bigquery/v2/projects/${projectId}/datasets`,
            transform: (data: any) =>
                data.datasets?.map((d: any) => d.datasetReference.datasetId) || [],
        },
    },

    bigquery_project: {
        project_id: {
            endpoint: (projectId: string) =>
                `https://cloudresourcemanager.googleapis.com/v1/projects`,
            transform: (data: any) =>
                data.projects?.map((p: any) => p.projectId) || [],
        },
    },

    dataflow_job: {
        job_name: {
            endpoint: (projectId: string) =>
                `https://dataflow.googleapis.com/v1b3/projects/${projectId}/jobs`,
            transform: (data: any) => data.jobs?.map((j: any) => j.name) || [],
        },
        job_id: {
            endpoint: (projectId: string) =>
                `https://dataflow.googleapis.com/v1b3/projects/${projectId}/jobs`,
            transform: (data: any) => data.jobs?.map((j: any) => j.id) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    dataproc_cluster: {
        cluster_name: {
            endpoint: (projectId: string) =>
                `https://dataproc.googleapis.com/v1/projects/${projectId}/regions/-/clusters`,
            transform: (data: any) =>
                data.clusters?.map((c: any) => c.clusterName) || [],
        },
        cluster_uuid: {
            endpoint: (projectId: string) =>
                `https://dataproc.googleapis.com/v1/projects/${projectId}/regions/-/clusters`,
            transform: (data: any) =>
                data.clusters?.map((c: any) => c.clusterUuid) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    pubsub_topic: {
        topic_id: {
            endpoint: (projectId: string) =>
                `https://pubsub.googleapis.com/v1/projects/${projectId}/topics`,
            transform: (data: any) =>
                data.topics?.map((t: any) => t.name.split("/").pop()) || [],
        },
    },

    pubsub_subscription: {
        subscription_id: {
            endpoint: (projectId: string) =>
                `https://pubsub.googleapis.com/v1/projects/${projectId}/subscriptions`,
            transform: (data: any) =>
                data.subscriptions?.map((s: any) => s.name.split("/").pop()) || [],
        },
    },

    // AI/ML Services
    ml_job: {
        job_id: {
            endpoint: (projectId: string) =>
                `https://ml.googleapis.com/v1/projects/${projectId}/jobs`,
            transform: (data: any) => data.jobs?.map((j: any) => j.jobId) || [],
        },
        task_name: {
            // Task names are dynamic and not available via API
            endpoint: (projectId: string) => `#dynamic-task-names`,
            transform: (data: any) => [],
        },
    },

    aiplatform_training_job: {
        job_id: {
            endpoint: (projectId: string) =>
                `https://aiplatform.googleapis.com/v1/projects/${projectId}/locations/-/trainingPipelines`,
            transform: (data: any) =>
                data.trainingPipelines?.map((p: any) => p.name.split("/").pop()) || [],
        },
    },

    aiplatform_endpoint: {
        endpoint_id: {
            endpoint: (projectId: string) =>
                `https://aiplatform.googleapis.com/v1/projects/${projectId}/locations/-/endpoints`,
            transform: (data: any) =>
                data.endpoints?.map((e: any) => e.name.split("/").pop()) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://aiplatform.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    // API & Developer Services
    api_gateway: {
        gateway_id: {
            endpoint: (projectId: string) =>
                `https://apigateway.googleapis.com/v1/projects/${projectId}/locations/-/gateways`,
            transform: (data: any) =>
                data.gateways?.map((g: any) => g.name.split("/").pop()) || [],
        },
        api_id: {
            endpoint: (projectId: string) =>
                `https://apigateway.googleapis.com/v1/projects/${projectId}/locations/global/apis`,
            transform: (data: any) =>
                data.apis?.map((a: any) => a.name.split("/").pop()) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://apigateway.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    cloud_endpoints_service: {
        service_name: {
            endpoint: (projectId: string) =>
                `https://servicemanagement.googleapis.com/v1/services?producerProjectId=${projectId}`,
            transform: (data: any) =>
                data.services?.map((s: any) => s.serviceName) || [],
        },
    },

    cloud_build: {
        build_id: {
            endpoint: (projectId: string) =>
                `https://cloudbuild.googleapis.com/v1/projects/${projectId}/builds`,
            transform: (data: any) => data.builds?.map((b: any) => b.id) || [],
        },
        build_trigger_id: {
            endpoint: (projectId: string) =>
                `https://cloudbuild.googleapis.com/v1/projects/${projectId}/triggers`,
            transform: (data: any) => data.triggers?.map((t: any) => t.id) || [],
        },
    },

    cloud_source_repo: {
        repo_name: {
            endpoint: (projectId: string) =>
                `https://sourcerepo.googleapis.com/v1/projects/${projectId}/repos`,
            transform: (data: any) =>
                data.repos?.map((r: any) => r.name.split("/").pop()) || [],
        },
    },

    // Monitoring & Operations
    uptime_url: {
        check_id: {
            endpoint: (projectId: string) =>
                `https://monitoring.googleapis.com/v3/projects/${projectId}/uptimeCheckConfigs`,
            transform: (data: any) =>
                data.uptimeCheckConfigs?.map((c: any) => c.name.split("/").pop()) || [],
        },
        checker_location: {
            // Static list of available uptime check locations
            endpoint: (projectId: string) => null, // No API call needed
            transform: (data: any) => [
                "us-central1",
                "us-east1",
                "us-west1",
                "us-east4",
                "us-west2",
                "us-west3",
                "us-west4",
                "europe-west1",
                "europe-west2",
                "europe-west3",
                "europe-west4",
                "europe-west6",
                "europe-north1",
                "asia-east1",
                "asia-east2",
                "asia-northeast1",
                "asia-northeast2",
                "asia-northeast3",
                "asia-south1",
                "asia-southeast1",
                "asia-southeast2",
                "australia-southeast1",
                "southamerica-east1",
            ],
        },
    },

    logging_sink: {
        sink_name: {
            endpoint: (projectId: string) =>
                `https://logging.googleapis.com/v2/projects/${projectId}/sinks`,
            transform: (data: any) => data.sinks?.map((s: any) => s.name) || [],
        },
    },

    // Security & Identity
    service_account: {
        email_id: {
            endpoint: (projectId: string) =>
                `https://iam.googleapis.com/v1/projects/${projectId}/serviceAccounts`,
            transform: (data: any) => data.accounts?.map((a: any) => a.email) || [],
        },
        unique_id: {
            endpoint: (projectId: string) =>
                `https://iam.googleapis.com/v1/projects/${projectId}/serviceAccounts`,
            transform: (data: any) => data.accounts?.map((a: any) => a.uniqueId) || [],
        },
    },

    // Scheduler & Tasks
    cloud_scheduler_job: {
        job_id: {
            endpoint: (projectId: string, location: string) =>
                `https://cloudscheduler.googleapis.com/v1/projects/${projectId}/locations/${location}/jobs`,
            transform: (data: any) =>
                data.jobs?.map((j: any) => j.name.split("/").pop()) || [],
            dependsOn: "location",
        },
        location: {
            endpoint: (projectId: string) =>
                `https://cloudscheduler.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    cloud_tasks_queue: {
        queue_id: {
            endpoint: (projectId: string, location: string) =>
                `https://cloudtasks.googleapis.com/v2/projects/${projectId}/locations/${location}/queues`,
            transform: (data: any) =>
                data.queues?.map((q: any) => q.name.split("/").pop()) || [],
            dependsOn: "location",
        },
        location: {
            endpoint: (projectId: string) =>
                `https://cloudtasks.googleapis.com/v2/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    // Cache Services
    redis_instance: {
        instance_id: {
            endpoint: (projectId: string) =>
                `https://redis.googleapis.com/v1/projects/${projectId}/locations/-/instances`,
            transform: (data: any) =>
                data.instances?.map((i: any) => i.name.split("/").pop()) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    memcache_instance: {
        instance_id: {
            endpoint: (projectId: string) =>
                `https://memcache.googleapis.com/v1/projects/${projectId}/locations/-/instances`,
            transform: (data: any) =>
                data.instances?.map((i: any) => i.name.split("/").pop()) || [],
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    // Other Services
    cloud_composer_environment: {
        environment_name: {
            endpoint: (projectId: string) =>
                `https://composer.googleapis.com/v1/projects/${projectId}/locations/-/environments`,
            transform: (data: any) =>
                data.environments?.map((e: any) => e.name.split("/").pop()) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://composer.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    datastream_stream: {
        stream_id: {
            endpoint: (projectId: string) =>
                `https://datastream.googleapis.com/v1/projects/${projectId}/locations/-/streams`,
            transform: (data: any) =>
                data.streams?.map((s: any) => s.name.split("/").pop()) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://datastream.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    cloud_dns_zone: {
        zone_name: {
            endpoint: (projectId: string) =>
                `https://dns.googleapis.com/dns/v1/projects/${projectId}/managedZones`,
            transform: (data: any) =>
                data.managedZones?.map((z: any) => z.name) || [],
        },
    },

    certificate_manager: {
        certificate_name: {
            endpoint: (projectId: string) =>
                `https://certificatemanager.googleapis.com/v1/projects/${projectId}/locations/-/certificates`,
            transform: (data: any) =>
                data.certificates?.map((c: any) => c.name.split("/").pop()) || [],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://certificatemanager.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    // Global/Generic Resources
    global: {
        // Global resources don't have specific endpoints
        // They should be handled at the application level
    },

    project: {
        project_id: {
            endpoint: (projectId: string) =>
                `https://cloudresourcemanager.googleapis.com/v1/projects`,
            transform: (data: any) =>
                data.projects?.map((p: any) => p.projectId) || [],
        },
    },

    // Additional Services (previously missing)
    cloud_trace: {
        trace_id: {
            endpoint: (projectId: string) => `#trace-data-not-listable`,
            transform: (data: any) => [],
        },
    },

    cloud_monitoring: {
        metric_type: {
            endpoint: (projectId: string) =>
                `https://monitoring.googleapis.com/v3/projects/${projectId}/metricDescriptors`,
            transform: (data: any) =>
                data.metricDescriptors?.map((m: any) => m.type) || [],
        },
    },

    cloud_error_reporting: {
        error_group_id: {
            endpoint: (projectId: string) => `#error-groups-not-directly-listable`,
            transform: (data: any) => [],
        },
    },

    cloud_logging: {
        log_name: {
            endpoint: (projectId: string) =>
                `https://logging.googleapis.com/v2/projects/${projectId}/logs`,
            transform: (data: any) =>
                data.logNames?.map((name: string) => name.split("/").pop()) || [],
        },
    },

    cloud_storage_transfer: {
        job_name: {
            endpoint: (projectId: string) =>
                `https://storagetransfer.googleapis.com/v1/transferJobs?filter={"project_id":"${projectId}"}`,
            transform: (data: any) => data.transferJobs?.map((j: any) => j.name) || [],
        },
    },

    cloud_kms: {
        key_ring_name: {
            endpoint: (projectId: string, location: string) =>
                `https://cloudkms.googleapis.com/v1/projects/${projectId}/locations/${location}/keyRings`,
            transform: (data: any) =>
                data.keyRings?.map((kr: any) => kr.name.split("/").pop()) || [],
            dependsOn: "location",
        },
        key_name: {
            endpoint: (projectId: string, location: string, keyRing: string) =>
                `https://cloudkms.googleapis.com/v1/projects/${projectId}/locations/${location}/keyRings/${keyRing}/cryptoKeys`,
            transform: (data: any) =>
                data.cryptoKeys?.map((k: any) => k.name.split("/").pop()) || [],
            dependsOn: ["location", "key_ring_name"],
        },
        location: {
            endpoint: (projectId: string) =>
                `https://cloudkms.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    cloud_secret_manager: {
        secret_name: {
            endpoint: (projectId: string) =>
                `https://secretmanager.googleapis.com/v1/projects/${projectId}/secrets`,
            transform: (data: any) =>
                data.secrets?.map((s: any) => s.name.split("/").pop()) || [],
        },
    },

    cloud_filestore: {
        instance_id: {
            endpoint: (projectId: string, location: string) =>
                `https://file.googleapis.com/v1/projects/${projectId}/locations/${location}/instances`,
            transform: (data: any) =>
                data.instances?.map((i: any) => i.name.split("/").pop()) || [],
            dependsOn: "location",
        },
        location: {
            endpoint: (projectId: string) =>
                `https://file.googleapis.com/v1/projects/${projectId}/locations`,
            transform: (data: any) =>
                data.locations?.map((l: any) => l.locationId) || [],
        },
    },

    cloud_armor: {
        security_policy_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/securityPolicies`,
            transform: (data: any) => data.items?.map((p: any) => p.name) || [],
        },
    },

    cloud_cdn: {
        backend_service_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/backendServices`,
            transform: (data: any) => data.items?.map((bs: any) => bs.name) || [],
        },
    },

    cloud_interconnect: {
        interconnect_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/global/interconnects`,
            transform: (data: any) => data.items?.map((i: any) => i.name) || [],
        },
        attachment_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/interconnectAttachments`,
            transform: (data: any) => {
                const attachments: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.interconnectAttachments) {
                        attachments.push(
                            ...regionData.interconnectAttachments.map((a: any) => a.name)
                        );
                    }
                });
                return attachments;
            },
        },
    },

    cloud_router: {
        router_name: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/aggregated/routers`,
            transform: (data: any) => {
                const routers: string[] = [];
                Object.values(data.items || {}).forEach((regionData: any) => {
                    if (regionData.routers) {
                        routers.push(...regionData.routers.map((r: any) => r.name));
                    }
                });
                return routers;
            },
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },

    cloud_nat: {
        nat_name: {
            endpoint: (projectId: string, region: string, router: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions/${region}/routers/${router}`,
            transform: (data: any) => data.nats?.map((n: any) => n.name) || [],
            dependsOn: ["region", "router_name"],
        },
        router_name: {
            endpoint: (projectId: string, region: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions/${region}/routers`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
            dependsOn: "region",
        },
        region: {
            endpoint: (projectId: string) =>
                `https://compute.googleapis.com/compute/v1/projects/${projectId}/regions`,
            transform: (data: any) => data.items?.map((r: any) => r.name) || [],
        },
    },
};