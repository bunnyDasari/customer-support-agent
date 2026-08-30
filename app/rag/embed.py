import json
from sentence_transformers import SentenceTransformer


INPUT_FILE = "data/processed/knowledge.json"
OUTPUT_FILE = "data/processed/embeddings.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def create_embeddings():

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Loading knowledge documents...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"Documents loaded: {len(documents)}")

    # Prepare the text that will be embedded
    texts = []

    for document in documents:

        text = (
            f"Question: {document['question']}\n"
            f"Solution: {document['solution']}\n"
            f"Category: {document['category']}\n"
            f"Sub-category: {document['sub_category']}\n"
            f"Product: {document['product']}"
        )

        texts.append(text)

    print("Creating embeddings...")

    # Encode all documents in batches
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    results = []

    for index, (document, text, embedding) in enumerate(
        zip(documents, texts, embeddings)
    ):

        results.append({
            "id": index,
            "text": text,
            "embedding": embedding.tolist(),
            "metadata": {
                "category": document["category"],
                "sub_category": document["sub_category"],
                "product": document["product"]
            }
        })

    print("Saving embeddings...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f)

    print("\n-----------------------------")
    print("Embedding completed!")
    print("-----------------------------")
    print(f"Documents : {len(results)}")
    print("Dimensions: 384")
    print(f"Output    : {OUTPUT_FILE}")


if __name__ == "__main__":
    create_embeddings()