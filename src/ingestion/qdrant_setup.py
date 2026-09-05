import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

# Konfigürasyon
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
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_SIZE = 384
BATCH_SIZE = 1000  # Qdrant upsert batch boyutu


def init_qdrant_collection(client: QdrantClient):
    """Qdrant üzerinde koleksiyonu temizleyip sıfırdan oluşturur."""
    if client.collection_exists(COLLECTION_NAME):
        print(f"'{COLLECTION_NAME}' koleksiyonu sıfırlanıyor...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"✓ '{COLLECTION_NAME}' koleksiyonu başarıyla hazırlandı.")


def fetch_all_review_records():
    """PostgreSQL'den metin içeren tüm yorumları metadata ile çeker."""
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
    """Tüm verileri vektörleştirip gruplar halinde Qdrant'a yükler."""
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    init_qdrant_collection(qdrant)

    print("PostgreSQL üzerinden metin içeren tüm yorumlar çekiliyor...")
    rows = fetch_all_review_records()
    total_count = len(rows)
    print(f"✓ Toplam {total_count:,} adet metinli kayıt çekildi.")

    print(f"'{EMBEDDING_MODEL_NAME}' modeli ile embedding üretimi başlıyor...")
    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    texts = [row[3] for row in rows]
    # batch_size vererek embedding üretimini hızlandırıyoruz
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

    print(f"\nQdrant'a aktarım başlıyor (Batch boyutu: {BATCH_SIZE})...")
    for i in range(0, total_count, BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        current_loaded = min(i + BATCH_SIZE, total_count)
        print(f"  -> {current_loaded:,} / {total_count:,} yüklendi (%{(current_loaded / total_count) * 100:.1f})")

    print(f"\n✓ Tebrikler! Toplam {total_count:,} adet yorum eksiksiz olarak Qdrant'a aktarıldı!")


if __name__ == "__main__":
    ingest_all_reviews_to_qdrant()