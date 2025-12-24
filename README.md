# Subscription-Based Book Search & RAG System

## Overview
A production-grade system where authors upload large PDF books, users subscribe to authors, and can search/query content only from their subscribed authors using RAG (Retrieval-Augmented Generation).

## Key Features
- PDF ingestion with hybrid chunking (structural + semantic)
- Subscription-based access control
- Vector search with metadata filtering
- Optional RAG for question answering
- Cost-optimized embedding strategy
- Support for 500+ page books from 200+ authors

## Architecture
```
PDF Upload → Text Extraction → Chunking → Embedding → Vector DB → Search API → RAG
```

## Tech Stack
- **Backend**: FastAPI
- **PDF Processing**: PyMuPDF
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Pinecone
- **Database**: PostgreSQL
- **Authentication**: JWT

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables (see `.env.example`)
3. Run migrations: `python -m alembic upgrade head`
4. Start server: `uvicorn app.main:app --reload`

## Project Structure
See `/docs/architecture.md` for detailed system design.