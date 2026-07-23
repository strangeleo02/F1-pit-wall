import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.exceptions import VectorDBUnavailableError

COLLECTION_NAME = "radio_transcripts"
TELEMETRY_COLLECTION_NAME = "race_telemetry"
VECTOR_SIZE = 384  # Dimension for all-MiniLM-L6-v2 embeddings

from qdrant_client.models import PayloadSchemaType

async def ensure_collection_exists(client: AsyncQdrantClient | None) -> None:
    """
    Ensures that both radio_transcripts and race_telemetry Qdrant collections and required payload indexes exist.
    """
    if not client:
        raise VectorDBUnavailableError("Qdrant client is not configured.")

    try:
        collections_response = await client.get_collections()
        existing_names = [col.name for col in collections_response.collections]

        for col_name in [COLLECTION_NAME, TELEMETRY_COLLECTION_NAME]:
            if col_name not in existing_names:
                await client.create_collection(
                    collection_name=col_name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
                )

            # Create payload field indexes required for filtered Qdrant queries
            payload_indexes = [
                ("driver", PayloadSchemaType.KEYWORD),
                ("session", PayloadSchemaType.KEYWORD),
                ("year", PayloadSchemaType.INTEGER),
                ("grand_prix", PayloadSchemaType.KEYWORD),
                ("session_key", PayloadSchemaType.INTEGER)
            ]
            for field, schema in payload_indexes:
                try:
                    await client.create_payload_index(
                        collection_name=col_name,
                        field_name=field,
                        field_schema=schema
                    )
                except Exception:
                    pass
    except Exception as e:
        raise VectorDBUnavailableError(f"Failed to ensure Qdrant collection: {str(e)}")

async def upsert_radio_transcripts(
    client: AsyncQdrantClient | None,
    transcripts: list[dict],
    embeddings: list[list[float]]
) -> int:
    """
    Batch indexes normalized radio transcripts and race control messages with vector embeddings.

    Args:
        client (AsyncQdrantClient | None): Injected AsyncQdrantClient instance.
        transcripts (list[dict]): List of transcript payload dictionaries.
        embeddings (list[list[float]]): Corresponding list of vector embeddings.

    Returns:
        int: Count of points upserted.
    """
    if not client:
        raise VectorDBUnavailableError("Qdrant client is not configured.")

    if len(transcripts) != len(embeddings):
        raise ValueError("Transcripts and embeddings lists must have the same length.")

    if not transcripts:
        return 0

    await ensure_collection_exists(client)

    points = []
    for payload, vector in zip(transcripts, embeddings):
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        )

    try:
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        return len(points)
    except Exception as e:
        raise VectorDBUnavailableError(f"Failed to upsert points into Qdrant: {str(e)}")

async def search_radio_transcripts(
    client: AsyncQdrantClient | None,
    query_embedding: list[float],
    limit: int = 5,
    driver: str | None = None,
    session: str | None = None,
    year: int | None = None,
    grand_prix: str | None = None
) -> list[dict]:
    """
    Asynchronously searches for relevant team radio transcripts in Qdrant with optional payload filters.

    Args:
        client (AsyncQdrantClient | None): Injected AsyncQdrantClient instance.
        query_embedding (list[float]): The vector representation of the search query.
        limit (int): Maximum number of results to return.
        driver (str | None): Filter by 3-letter driver code.
        session (str | None): Filter by session type ('R', 'Q', etc.).
        year (int | None): Filter by race year.
        grand_prix (str | None): Filter by Grand Prix location.

    Returns:
        list[dict]: A list of relevant transcripts with their metadata.
    """
    if not client:
        raise VectorDBUnavailableError("Qdrant client is not configured.")

    def _build_filter(d: str | None, s: str | None, y: int | None, gp: str | None):
        conds = []
        if d:
            conds.append(FieldCondition(key="driver", match=MatchValue(value=d)))
        if s:
            conds.append(FieldCondition(key="session", match=MatchValue(value=s)))
        if y:
            conds.append(FieldCondition(key="year", match=MatchValue(value=y)))
        if gp:
            conds.append(FieldCondition(key="grand_prix", match=MatchValue(value=gp)))
        return Filter(must=conds) if conds else None

    async def _execute_query(q_filter: Filter | None) -> list[dict]:
        try:
            res = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_embedding,
                query_filter=q_filter,
                limit=limit
            )
            return [point.payload for point in res.points if point.payload]
        except AttributeError:
            # Fallback for sync or legacy client structures
            res = await client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=q_filter,
                limit=limit
            )
            return [point.payload for point in res if point.payload]

    try:
        # Primary pass: search with all supplied filters
        query_filter = _build_filter(driver, session, year, grand_prix)
        results = await _execute_query(query_filter)
        if results:
            return results

        # Fallback pass 1: relax grand_prix filter if location string format differs
        if grand_prix:
            fallback_filter = _build_filter(driver, session, year, None)
            results = await _execute_query(fallback_filter)
            if results:
                return results

        # Fallback pass 2: search by year & driver
        if driver and year:
            fallback_filter = _build_filter(driver, None, year, None)
            results = await _execute_query(fallback_filter)
            if results:
                return results

        # Fallback pass 3: search by query embedding only
        results = await _execute_query(None)
        return results
    except VectorDBUnavailableError:
        raise
    except Exception as e:
        raise VectorDBUnavailableError(f"Failed to search Qdrant: {str(e)}")

async def upsert_telemetry_records(
    client: AsyncQdrantClient | None,
    records: list[dict],
    embeddings: list[list[float]]
) -> int:
    """
    Batch indexes telemetry summary records into the 'race_telemetry' Qdrant collection.
    """
    if not client:
        raise VectorDBUnavailableError("Qdrant client is not configured.")

    if len(records) != len(embeddings):
        raise ValueError("Records and embeddings lists must have the same length.")

    if not records:
        return 0

    await ensure_collection_exists(client)

    points = []
    for payload, vector in zip(records, embeddings):
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        )

    try:
        await client.upsert(
            collection_name=TELEMETRY_COLLECTION_NAME,
            points=points
        )
        return len(points)
    except Exception as e:
        raise VectorDBUnavailableError(f"Failed to upsert telemetry into Qdrant: {str(e)}")

async def search_race_telemetry(
    client: AsyncQdrantClient | None,
    query_embedding: list[float],
    limit: int = 5,
    driver: str | None = None,
    session: str | None = None,
    year: int | None = None,
    grand_prix: str | None = None
) -> list[dict]:
    """
    Searches the 'race_telemetry' collection in Qdrant.
    """
    if not client:
        raise VectorDBUnavailableError("Qdrant client is not configured.")

    def _build_filter(d: str | None, s: str | None, y: int | None, gp: str | None):
        conds = []
        if d:
            conds.append(FieldCondition(key="driver", match=MatchValue(value=d)))
        if s:
            conds.append(FieldCondition(key="session", match=MatchValue(value=s)))
        if y:
            conds.append(FieldCondition(key="year", match=MatchValue(value=y)))
        if gp:
            conds.append(FieldCondition(key="grand_prix", match=MatchValue(value=gp)))
        return Filter(must=conds) if conds else None

    async def _execute_query(q_filter: Filter | None) -> list[dict]:
        try:
            res = await client.query_points(
                collection_name=TELEMETRY_COLLECTION_NAME,
                query=query_embedding,
                query_filter=q_filter,
                limit=limit
            )
            return [point.payload for point in res.points if point.payload]
        except AttributeError:
            res = await client.search(
                collection_name=TELEMETRY_COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=q_filter,
                limit=limit
            )
            return [point.payload for point in res if point.payload]

    try:
        query_filter = _build_filter(driver, session, year, grand_prix)
        results = await _execute_query(query_filter)
        if results:
            return results

        if grand_prix:
            results = await _execute_query(_build_filter(driver, session, year, None))
            if results:
                return results

        if driver and year:
            results = await _execute_query(_build_filter(driver, None, year, None))
            if results:
                return results

        return await _execute_query(None)
    except VectorDBUnavailableError:
        raise
    except Exception as e:
        raise VectorDBUnavailableError(f"Failed to search race_telemetry Qdrant collection: {str(e)}")
