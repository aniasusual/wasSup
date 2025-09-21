"""
MMM: Architecture-Specific Filters (helper library)

Provides safe, architecture-aware label clauses for Google Cloud Logging
filters using the Service Registry (XX). This module does NOT guess or
fallback; it only promotes labels that are explicitly present in the
registry for a given service.

Usage:
  - build_label_clauses_for_services(service_ids, registry_index) -> List[str]
  - The returned clauses are of the form: resource.labels.<key>="<value>"
"""

from typing import Dict, Any, List


def _label_clause(key: str, value: Any) -> str:
    v = str(value).replace('"', '\\"')
    return f'resource.labels.{key}="{v}"'


def build_label_clauses_for_entry(entry: Dict[str, Any]) -> List[str]:
    """
    Build architecture-specific label clauses for a single service registry entry.
    Strict: only uses labels provided in entry["resource_labels"]. No inference.
    """
    rt = entry.get("resource_type")
    labels: Dict[str, Any] = entry.get("resource_labels") or {}
    if not rt or not isinstance(labels, dict) or not labels:
        return []

    clauses: List[str] = []
    # Cloud Run revision: service_name
    if rt == "cloud_run_revision" and labels.get("service_name"):
        clauses.append(_label_clause("service_name", labels["service_name"]))
    # App Engine: module_id
    if rt == "gae_app" and labels.get("module_id"):
        clauses.append(_label_clause("module_id", labels["module_id"]))
    # GKE/K8s: cluster_name, namespace_name
    if rt == "k8s_container":
        if labels.get("cluster_name"):
            clauses.append(_label_clause("cluster_name", labels["cluster_name"]))
        if labels.get("namespace_name"):
            clauses.append(_label_clause("namespace_name", labels["namespace_name"]))
    # GCE instance: instance_id if present
    if rt == "gce_instance" and labels.get("instance_id"):
        clauses.append(_label_clause("instance_id", labels["instance_id"]))
    # Cloud SQL: database_id or instance_id when present
    if rt == "cloudsql_database":
        if labels.get("database_id"):
            clauses.append(_label_clause("database_id", labels["database_id"]))
        if labels.get("instance_id"):
            clauses.append(_label_clause("instance_id", labels["instance_id"]))
    # BigQuery dataset: dataset_id
    if rt == "bigquery_dataset" and labels.get("dataset_id"):
        clauses.append(_label_clause("dataset_id", labels["dataset_id"]))

    return clauses


def build_label_clauses_for_services(service_ids: List[str], registry_index: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Build a combined list of label clauses for the provided service_ids
    using the registry index { service_id -> entry }.
    """
    out: List[str] = []
    for sid in service_ids or []:
        entry = registry_index.get(sid)
        if not entry:
            continue
        for c in build_label_clauses_for_entry(entry):
            if c not in out:
                out.append(c)
    return out

