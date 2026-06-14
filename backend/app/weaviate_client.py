import weaviate
from .config import COHERE_API_KEY

client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={"X-OpenAI-Api-Key": COHERE_API_KEY}
)

# Ensure schema exists
if not client.schema.exists(class_name="DocumentChunk"):
    schema = {
        "class": "DocumentChunk",
        "properties": [
            {"name": "text", "dataType": ["text"]},
            {"name": "source", "dataType": ["string"]},
        ],
        "vectorizer": "none",
    }
    client.schema.create_class(schema)
