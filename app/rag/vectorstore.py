import json
import chromadb


DB_PATH = "data/chroma"
COLLECTION_NAME = "customer_support"
EMBEDDINGS_FILE = "data/processed/embeddings.json"


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection


def insert_embeddings():

    collection = get_collection()

    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for item in data:
        ids.append(str(item["id"]))
        documents.append(item["text"])
        embeddings.append(item["embedding"])
        metadatas.append(item["metadata"])

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print("Embeddings inserted successfully!")
    print("Documents in ChromaDB:", collection.count())


if __name__ == "__main__":
    insert_embeddings()