import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

# Configuration
POSTGRES_CONFIG = {
    "dbname": "enterprise_db",
    "user": "admin",
    "password": "password123",
    "host": "localhost",
    "port": 5433
}

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "olist_reviews"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384
BATCH_SIZE = 1000  # Qdrant upsert batch boyutu


def init_qdrant_collection(client: QdrantClient):
    """Deletes the existing collection and creates a new one from scratch."""
    if client.collection_exists(COLLECTION_NAME):
        print(f"Resetting '{COLLECTION_NAME}' collection...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"'{COLLECTION_NAME}' collection initialized successfully.")


def fetch_all_review_records():
    """Fetches all reviews containing text from PostgreSQL along with metadata."""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    query = """
    SELECT 
        r.review_pk,
        r.order_id,
        r.review_score,
        r.review_comment_message,
        COALESCE(p.product_category_name, 'unknown') AS product_category
    FROM order_reviews r
    JOIN order_items oi ON r.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE r.review_comment_message IS NOT NULL 
      AND TRIM(r.review_comment_message) <> '';
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def ingest_all_reviews_to_qdrant():
    """Generates embeddings for all reviews and uploads them to Qdrant in batches."""
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    init_qdrant_collection(qdrant)

    print("Fetching all text-containing reviews from PostgreSQL...")
    rows = fetch_all_review_records()
    total_count = len(rows)
    print(f"✓ Fetched {total_count:,} text-containing records in total.")

    print(f"Starting embedding generation using '{EMBEDDING_MODEL_NAME}'...")
    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    texts = [row[3] for row in rows]
    # Using a batch size to speed up embedding generation
    embeddings = list(embedding_model.embed(texts, batch_size=256))

    points = []
    for idx, row in enumerate(rows):
        review_pk, order_id, score, message, category = row
        points.append(
            PointStruct(
                id=review_pk,
                vector=embeddings[idx].tolist(),
                payload={
                    "order_id": order_id,
                    "review_score": score,
                    "comment": message,
                    "product_category": category
                }
            )
        )

    print(f"\nStarting upload to Qdrant (Batch size: {BATCH_SIZE})...")
    for i in range(0, total_count, BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        current_loaded = min(i + BATCH_SIZE, total_count)
        print(f"  -> {current_loaded:,} / {total_count:,} uploaded  (%{(current_loaded / total_count) * 100:.1f})")

    print(f"\n✓ Success! All {total_count:,} reviews were successfully ")


if __name__ == "__main__":
    ingest_all_reviews_to_qdrant()