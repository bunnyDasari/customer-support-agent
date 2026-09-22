from sentence_transformers import SentenceTransformer
from app.rag.vectorstore import get_collection
import re


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def extract_order_number(text):
    """
    Extract an order number from text.
    Supports:
        123456
        BB123456
        #123456
        #BB123456
    """

    match = re.search(r"\b(?:BB)?\d+\b", text, re.IGNORECASE)

    if match:
        return match.group(0).upper().replace("#", "")

    return None


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

    # --------------------------------------------------
    # Exact order-number filtering
    # --------------------------------------------------

    order_number = extract_order_number(query)

    if order_number:

        filtered_documents = []

        for document in results["documents"][0]:

            document_order_number = extract_order_number(document)

            if document_order_number == order_number:
                filtered_documents.append(document)

        # Only return exact order-number matches
        results["documents"][0] = filtered_documents

    return results


if __name__ == "__main__":

    query = """
    Customer goal: ORDER_STATUS
    Order number: 123456
    """

    results = retrieve(query)

    print("\nCustomer Query:")
    print(query)

    print("\nRetrieved Evidence:")

    for i, document in enumerate(results["documents"][0]):
        print(f"\n--- Result {i + 1} ---")
        print(document)