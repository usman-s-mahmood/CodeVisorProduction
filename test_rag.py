# Temporary Test Script
from AIChatbotApp.ph2_ai_logic.ph2_pinecone_helper import search_knowledge_base

question = "How do I solve a subarray problem efficiently?"
docs = search_knowledge_base(question)

print("--- RAG SEARCH RESULTS ---")
for d in docs:
    print(f"Match Found: {d['title']}")