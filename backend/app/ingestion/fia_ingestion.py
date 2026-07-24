import uuid
from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.services.embedding_service import get_embedding_model

FIA_COLLECTION_NAME = "fia_documents"

SAMPLE_FIA_DECISIONS = [
    {
        "doc_id": "FIA-MON-2023-01",
        "grand_prix": "Monaco",
        "year": 2023,
        "title": "Document 42 - Offence: Car 16 Track Limits Turn 10",
        "driver": "LEC",
        "decision": "Lap time 1:11.450 deleted under Article 33.3 of FIA Sporting Regulations (Track Limits at Nouvelle Chicane).",
        "category": "TRACK_LIMITS"
    },
    {
        "doc_id": "FIA-MON-2023-02",
        "grand_prix": "Monza",
        "year": 2023,
        "title": "Document 38 - Incident: Car 55 & Car 4 Impeding at Turn 1",
        "driver": "SAI",
        "decision": "No further action. Both drivers took evasive action in traffic during Qualifying Q3.",
        "category": "IMPEDING"
    },
    {
        "doc_id": "FIA-SIL-2023-01",
        "grand_prix": "Silverstone",
        "year": 2023,
        "title": "Document 51 - Technical Delegate Report: Power Unit Component Change",
        "driver": "HAM",
        "decision": "Car 44 fitted with 3rd Energy Store (ES) of the season. 5-place grid penalty applied.",
        "category": "TECHNICAL_PENALTY"
    }
]

async def ensure_fia_collection_exists(client: AsyncQdrantClient) -> None:
    """Ensures Qdrant collection for fia_documents exists."""
    collections_res = await client.get_collections()
    existing = [c.name for c in collections_res.collections]
    if FIA_COLLECTION_NAME not in existing:
        await client.create_collection(
            collection_name=FIA_COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

async def ingest_fia_documents(client: AsyncQdrantClient, docs: Optional[list[dict]] = None) -> int:
    """
    Ingests FIA steward decision documents into Qdrant vector database.
    """
    await ensure_fia_collection_exists(client)

    target_docs = docs or SAMPLE_FIA_DECISIONS
    model = get_embedding_model()

    points = []
    for doc in target_docs:
        text_content = f"{doc['title']} - Driver: {doc['driver']}. Decision: {doc['decision']}"
        vector = model.encode(text_content).tolist()
        
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "doc_id": doc.get("doc_id", ""),
                "grand_prix": doc.get("grand_prix", ""),
                "year": int(doc.get("year", 2023)),
                "driver": doc.get("driver", ""),
                "title": doc.get("title", ""),
                "decision": doc.get("decision", ""),
                "category": doc.get("category", "DECISION"),
                "text_content": text_content
            }
        ))

    if points:
        await client.upsert(collection_name=FIA_COLLECTION_NAME, points=points)

    return len(points)
