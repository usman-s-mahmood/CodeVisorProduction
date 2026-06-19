import cohere
from decouple import config

# Initialize the client once
co = cohere.Client(config('COHERE_API_KEY'))

def get_query_embedding(text):
    """Turns the user query into a vector for searching."""
    response = co.embed(
        texts=[text],
        model='embed-english-v3.0',
        input_type='search_query'  # Crucial: Use 'search_query' for RAG retrieval
    )
    return response.embeddings[0]