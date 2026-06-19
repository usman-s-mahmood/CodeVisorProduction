#!/bin/bash

# NEXUS-AI RAG Master Controller
# Optimized for Linux Mint on 4GB RAM

# Colors for the terminal
PURPLE='\033[0;35m'
NC='\033[0m' # No Color
GREEN='\033[0;32m'
CYAN='\033[0;36m'

echo -e "${PURPLE}"
echo "    _   _______   _   _ ____        _    ___ "
echo "   | \ | | ____| \/ | | / ___|      / \  |_ _|"
echo "   |  \| |  _|    \ \ | \___ \     / _ \  | | "
echo "   | |\  | |___   / / | |___) |   / ___ \ | | "
echo "   |_| \_|_____| /_/  |_|____/   /_/   \_\___|"
echo -e "${NC}"

echo "------------------------------------------------"
echo "Select an Operation for Nexus-AI Implementation:"
echo "-----------------------------------------------"
echo "1) [PHASE 1] Ingest JSON Knowledge to Pinecone"
echo "2) [PHASE 2] Run RAG Bridge Test (test_rag.py)"
echo "3) [PHASE 3] Start Django Development Server"
echo "4) Exit"
echo "------------------------------------------------"

read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Starting Phase 1: Ingesting Data to Cloud...${NC}"
        python3 ph1_scripts/ph1_ingest_json.py
        ;;
    2)
        echo -e "${CYAN}🧪 Testing Phase 2: Vector Search Bridge...${NC}"
        if [ -f "test_rag.py" ]; then
            python3 test_rag.py
        else
            echo "❌ Error: test_rag.py not found in root!"
        fi
        ;;
    3)
        echo -e "${GREEN}🖥️  Starting Django Server...${NC}"
        # We use --noreload if your RAM is struggling, 
        # but standard runserver is fine for development.
        python3 manage.py runserver
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option."
        ;;
esac