import json
import cohere
from pinecone import Pinecone, ServerlessSpec
from decouple import config

# 1. Init Clients
co = cohere.Client(config('COHERE_API_KEY'))
pc = Pinecone(api_key=config('PINECONE_API_KEY'))
index_name = config('PINECONE_INDEX_NAME')

# 2. Check/Create Pinecone Index (Dimension 1024 for Cohere v3)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1024,
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

index = pc.Index(index_name)

def run_ingestion():
    # Load the JSON Knowledge Base
    with open('ph1_data/ph1_dsa_knowledge.json', 'r') as f:
        data = json.load(f)

    print(f"🚀 Starting Ingestion: {len(data)} items found.")

    for item in data:
        # Generate the math vector for the content
        response = co.embed(
            texts=[item['content']],
            model='embed-english-v3.0',
            input_type='search_document'
        )
        
        # Push to Cloud
        index.upsert(vectors=[{
            'id': item['id'],
            'values': response.embeddings[0],
            'metadata': {
                'title': item['title'],
                'text': item['content'],
                **item['metadata']
            }
        }])
        print(f"✅ Indexed: {item['title']}")

if __name__ == "__main__":
    run_ingestion()