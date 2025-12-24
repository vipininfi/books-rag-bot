# System Architecture

## Overview
This is a subscription-based book search and RAG (Retrieval-Augmented Generation) system that allows users to search and query content from books by authors they've subscribed to.

## Core Components

### 1. PDF Processing Pipeline
- **PDF Processor**: Extracts text with layout awareness using PyMuPDF
- **Chunking Engine**: Implements hybrid chunking (structural + selective semantic)
- **Embedding Service**: Generates embeddings using OpenAI text-embedding-3-small
- **Vector Store**: Stores and searches embeddings using Pinecone

### 2. Access Control
- **Subscription Model**: Users subscribe to authors
- **Filtered Search**: Vector search respects subscription boundaries
- **Metadata Filtering**: Access control enforced at database level

### 3. Search & RAG
- **Semantic Search**: Vector similarity search with metadata filtering
- **RAG Generation**: Context-aware answer generation using GPT-4o-mini
- **Source Attribution**: All answers include source references

## Data Flow

```
PDF Upload → Text Extraction → Structural Analysis → Chunking → Embedding → Vector Storage
                                                                                    ↓
User Query → Query Embedding → Filtered Vector Search → Context Assembly → RAG Answer
```

## Database Schema

### Core Tables
- `users`: User accounts and authentication
- `authors`: Author information
- `books`: Book metadata and processing status
- `subscriptions`: User-author subscription relationships

### Vector Storage
- Pinecone index with metadata filtering
- Each chunk includes author_id for access control

## Cost Optimization

### Embedding Strategy
- Uses text-embedding-3-small (6.5x cheaper than large)
- Batch processing for efficiency
- One-time embedding cost per book

### Chunking Strategy
- 85-90% fixed chunking (fast, predictable)
- 10-15% semantic chunking (high-value sections only)
- Bounded semantic calls per book

### Query Optimization
- Metadata filtering at vector DB level
- Reranking for relevance improvement
- Configurable result limits

## Security

### Authentication
- JWT-based authentication
- Password hashing with bcrypt

### Authorization
- Subscription-based access control
- Vector search filtered by author_id
- No post-query filtering (prevents data leakage)

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Background processing for book ingestion
- Vector DB handles scaling automatically

### Performance
- Sub-second query response times
- Efficient metadata filtering
- Batch embedding generation

## Deployment Architecture

### Development
- Local PostgreSQL + Pinecone
- File-based PDF storage
- Direct OpenAI API calls

### Production
- Managed PostgreSQL (RDS/Cloud SQL)
- Pinecone managed service
- Object storage for PDFs (S3/GCS)
- Load balancer + multiple API instances

## Monitoring & Observability

### Key Metrics
- Query latency
- Embedding costs
- Storage usage
- User subscription patterns
- Search quality metrics

### Error Handling
- Graceful degradation
- Retry mechanisms for external APIs
- Comprehensive logging
- Background task monitoring