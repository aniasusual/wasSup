# backend/logs.py
from google.cloud import logging_v2
from google.oauth2 import service_account

def get_logs(filter_str: str = None, limit: int = 50):
    credentials = service_account.Credentials.from_service_account_file(
        'app/secrets/test_key.json'
    )
    client = logging_v2.Client(credentials=credentials)

    # Filter string (e.g., 'resource.type="cloud_function"')
    iterator = client.list_entries(filter_=filter_str, page_size=limit)

    logs = []
    for entry in iterator:
        logs.append({
            "timestamp": entry.timestamp.isoformat(),
            "severity": entry.severity,
            "message": entry.payload if isinstance(entry.payload, str) else str(entry.payload),
            "resource": entry.resource.type,
        })

    return logs