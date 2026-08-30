from sentence_transformers import SentenceTransformer
from app.rag.vectorstore import get_collection


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def retrieve(query, top_k=3):

    # Load embedding model
    model = SentenceTransformer(MODEL_NAME)

    # Convert customer query into a vector
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    # Get ChromaDB collection
    collection = get_collection()

    # Search for similar documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results


if __name__ == "__main__":

    query = "Where is my order?"

    results = retrieve(query)

    print("\nCustomer Query:")
    print(query)

    print("\nRetrieved Evidence:")

    for i, document in enumerate(results["documents"][0]):
        print(f"\n--- Result {i + 1} ---")
        print(document)