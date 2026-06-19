from pinecone import Pinecone
from decouple import config
from .ph2_cohere_bridge import get_query_embedding

pc = Pinecone(api_key=config('PINECONE_API_KEY'))
index = pc.Index(config('PINECONE_INDEX_NAME'))

def search_knowledge_base(query, top_k=2):
    """
    1. Embeds the query
    2. Searches Pinecone
    3. Returns formatted documents for the LLM
    """
    # Get the math vector for the question
    query_vector = get_query_embedding(query)
    
    # Search the cloud
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    # Format the results into the structure Cohere Command R expects
    documents = []
    for match in results['matches']:
        documents.append({
            "title": match['metadata']['title'],
            "snippet": match['metadata']['text']
        })
    
    return documents