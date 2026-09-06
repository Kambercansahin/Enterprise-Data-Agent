import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "olist_reviews"

# 1. Qdrant ve FastEmbed modellerini başlatıyoruz
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def search_reviews_in_qdrant(query_text: str, limit: int = 4) -> list[str]:
    """Soruyu vektöre çevirip Qdrant'ta arar ve yorum metinlerini döndürür."""

    # 2. Metni float listesi olan bir embedding vektörüne çeviriyoruz
    query_vector = list(embedding_model.embed([query_text]))[0].tolist()

    # 3. Vektörü query_points'e iletiyoruz
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    # 4. Dönen noktalardan metin alanını ayıklıyoruz
    retrieved_texts = []
    for point in response.points:
        payload = point.payload or {}
        text = (
                payload.get("review_comment_message")
                or payload.get("review_text")
                or payload.get("text")
                or str(payload)
        )
        retrieved_texts.append(text)

    return retrieved_texts


if __name__ == "__main__":
    test_soru = "adıyaman hava durumu"
    yorumlar = search_reviews_in_qdrant(test_soru, limit=3)

    print(f"--- Qdrant'tan Gelen Sonuçlar ({len(yorumlar)} adet) ---")
    for i, y in enumerate(yorumlar, 1):
        print(f"\n[{i}] {y}")