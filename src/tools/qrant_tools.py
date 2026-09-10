import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "olist_reviews"

# 1. Initialize Qdrant and the FastEmbed model
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def search_reviews_in_qdrant(query_text: str, limit: int = 4,score_threshold: float = 0.55) -> list[str]:
    """Converts the query into a vector and performs a semantic similarity search
       on Qdrant. Filters out results below the score threshold."""

    # 2. Convert the text into an embedding vector represented as a list of floats
    query_vector = list(embedding_model.embed([query_text]))[0].tolist()

    # 3. Pass the vector to query_points
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        score_threshold=score_threshold
    )

    # 4. Extract the text field from the retrieved points
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
    def print_scores(query: str):
        q_vec = list(embedding_model.embed([query]))[0].tolist()
        res = client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            limit=3
        )
        print(f"\nQuery: '{query}'")
        for i, pt in enumerate(res.points, 1):
            comment = (pt.payload or {}).get("comment", "")
            print(f"  [{i}] Score: {pt.score:.4f} | comment: {comment}")

    print_scores("adıyaman hava durumu")
    print_scores("kargo çok geç geldi ürün hasarlıydı")