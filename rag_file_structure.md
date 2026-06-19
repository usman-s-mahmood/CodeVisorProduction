Project_Root/
├── .env                              <-- (PH1: Store COHERE_API_KEY & PINECONE_API_KEY)
├── manage.py
├── rag_setup.sh
│
├── ph1_data/                         <-- (PH1: Data Collection)
│   └── ph1_leetcode_snippets.json    <-- Your raw coding context/problems
│
├── ph1_scripts/                      <-- (PH1: Cloud Ingestion - Run Once)
│   └── ph1_ingest_to_pinecone.py     <-- Scripts to embed & upload data to Pinecone
│
├── AIChatbotApp/
│   ├── ph2_ai_logic/                 <-- (PH2: The RAG Engine - Independent of Django)
│   │   ├── __init__.py
│   │   ├── ph2_cohere_client.py      <-- Handles embeddings & Command R (03-2025)
│   │   └── ph2_pinecone_search.py    <-- Handles the vector retrieval logic
│   │
│   ├── static/NexusAIApp/
│   │   ├── chat.css                  <-- (PH5: Tweaks for citation badges)
│   │   └── chat.js                   <-- (PH4: Handle 'sources' in JSON response)
│   │
│   ├── templates/NexusAIApp/
│   │   └── chat.html                 <-- (PH4: Citation UI container)
│   │
│   ├── ph3_views_logic.py            <-- (PH3: The Router - "Slim Shady" vs "LeetCode")
│   ├── views.py                      <-- (PH3: Hooking ph3_views_logic into your endpoints)
│   └── models.py                     <-- (PH5: Optional - Store which docs were cited)
│
└── virt/                             <-- Your Virtual Env
