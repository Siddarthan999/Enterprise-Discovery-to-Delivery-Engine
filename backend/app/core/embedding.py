from sentence_transformers import SentenceTransformer

# lightweight, fast, production-safe model
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str):
    return model.encode(text).tolist()