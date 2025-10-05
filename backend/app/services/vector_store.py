from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import os
import time

from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from .embeddings import embed_texts, get_embedding_dimension


QDRANT_URL = os.getenv("QDRANT_URL") or "https://f918a415-5908-4859-b76d-8607d7a4c5fc.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.Xja0h1lqYibvkSbm335AbNs5CdPqnk1DGjb-3emJmuU"


class QdrantVectorStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    def ensure_collection(self, name: str) -> None:
        dim = get_embedding_dimension()
        try:
            self.client.get_collection(name)
        except Exception:
            # Create collection with proper indexes for filtering
            self.client.recreate_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=dim,
                    distance=qmodels.Distance.COSINE,
                ),
                optimizers_config=qmodels.OptimizersConfigDiff(indexing_threshold=20000),
            )
            
            # Create indexes for fields commonly used in filters
            try:
                self.client.create_payload_index(
                    collection_name=name,
                    field_name="projectId",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
            except Exception as e:
                print(f"Warning: Could not create projectId index: {e}")
                
            try:
                self.client.create_payload_index(
                    collection_name=name,
                    field_name="serviceId",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
            except Exception as e:
                print(f"Warning: Could not create serviceId index: {e}")
                
            try:
                self.client.create_payload_index(
                    collection_name=name,
                    field_name="severity",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
            except Exception as e:
                print(f"Warning: Could not create severity index: {e}")

    def ensure_indexes(self, name: str) -> None:
        """Ensure that required indexes exist for the collection."""
        indexes_to_create = ["projectId", "serviceId", "severity", "resource.type", "traceId"]
        
        for field_name in indexes_to_create:
            try:
                print(f"Attempting to create index for field: {field_name}")
                self.client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
                print(f"Successfully created index for {field_name}")
                    
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"Index for {field_name} already exists")
                else:
                    print(f"Error creating index for {field_name}: {e}")
                # Continue with other indexes
                continue

    def upsert_logs(
        self,
        collection: str,
        items: List[Dict[str, Any]],
        text_key: str = "message",
    ) -> int:
        """
        Upsert logs into the vector store.
        
        Args:
            collection: Collection name
            items: List of log items to upsert
            text_key: Key in the item dict that contains the text to embed
            
        Returns:
            Number of items successfully upserted
        """
        self.ensure_collection(collection)
        self.ensure_indexes(collection)

        texts = [item.get(text_key, "") for item in items]
        vectors = embed_texts(texts)
        
        if not vectors:
            # If embeddings are not available, skip indexing gracefully
            return 0

        points = []
        now_ms = int(time.time() * 1000)
        for idx, (item, vector) in enumerate(zip(items, vectors)):
            pid = str(item.get("id") or item.get("insertId") or f"log_{now_ms}_{idx}")
            payload = {
                **item,
                "_ingestedAt": now_ms,
            }
            points.append(
                qmodels.PointStruct(id=pid, vector=vector, payload=payload)
            )

        self.client.upsert(collection_name=collection, points=points, wait=True)
        return len(points)

    def search(
        self,
        collection: str,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search with optional payload filters."""
        self.ensure_collection(collection)
        self.ensure_indexes(collection)

        vectors = embed_texts([query])
        if not vectors:
            return []

        must_conditions: List[qmodels.FieldCondition] = []
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if isinstance(value, list):
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            match=qmodels.MatchAny(any=value),
                        )
                    )
                else:
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            match=qmodels.MatchValue(value=value),
                        )
                    )

        # Only use filters if we have them and they're not empty
        use_filters = bool(must_conditions)
        
        if use_filters:
            try:
                qr = self.client.search(
                    collection_name=collection,
                    query_vector=vectors[0],
                    query_filter=qmodels.Filter(must=must_conditions),
                    limit=limit,
                    with_payload=True,
                    with_vectors=False,
                )
            except Exception as e:
                print(f"Search with filters failed: {e}")
                raise e
        else:
            # No filters to apply, search without filters
            qr = self.client.search(
                collection_name=collection,
                query_vector=vectors[0],
                query_filter=None,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

        results: List[Dict[str, Any]] = []
        for point in qr:
            payload = point.payload or {}
            payload["_score"] = float(point.score) if hasattr(point, "score") else 0.0
            results.append(payload)

        return results


