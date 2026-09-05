from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from fastembed import TextEmbedding

# Bağlantı ve Model
qdrant = QdrantClient(host="localhost", port=6333)
collection_name = "olist_reviews"
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def search_customer_feedback(query_text: str, max_score: int = None, limit: int = 3):
    print(f"\nSorgu: '{query_text}'")
    if max_score:
        print(f"Filtre: Yalnızca {max_score} ve altı puanlar hedefleniyor.")

    # 1. Kullanıcı sorusunu anlık vektörleştir
    query_vector = list(embedding_model.embed([query_text]))[0].tolist()

    # 2. Opsiyonel Metadata Filtresi
    query_filter = None
    if max_score is not None:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="review_score",
                    range=Range(lte=max_score)
                )
            ]
        )

    # 3. Güncel query_points API'si ile semantik arama
    response = qdrant.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=query_filter,
        limit=limit
    )

    print("-" * 60)
    for idx, hit in enumerate(response.points, 1):
        payload = hit.payload
        print(f"[{idx}] Benzerlik Skoru: {hit.score:.4f} | Puan: {payload['review_score']}/5 | Kategori: {payload['product_category']}")
        print(f"    Sipariş ID: {payload['order_id']}")
        print(f"    Yorum: \"{payload['comment']}\"\n")

if __name__ == "__main__":
    # Test 1: Kırık/hasarlı teslimat şikayetleri (Puan <= 2)
    search_customer_feedback(
        query_text="O produto veio quebrado e a embalagem estava danificada",
        max_score=2,
        limit=2
    )

    # Test 2: Hızlı teslimat memnuniyeti
    search_customer_feedback(
        query_text="Chegou muito rápido antes do prazo excelente",
        limit=2
    )