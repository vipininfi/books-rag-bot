# API Documentation

## Authentication

All endpoints (except auth) require Bearer token authentication.

### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

## Book Management

### Upload Book
```http
POST /api/v1/books/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf_file>
title: "Book Title"
description: "Book description"
author_id: 1
```

### Get Book Details
```http
GET /api/v1/books/{book_id}
Authorization: Bearer <token>
```

### List Books
```http
GET /api/v1/books?skip=0&limit=100
Authorization: Bearer <token>
```

## Subscriptions

### Subscribe to Author
```http
POST /api/v1/subscriptions/
Authorization: Bearer <token>
Content-Type: application/json

{
  "author_id": 1
}
```

### Get My Subscriptions
```http
GET /api/v1/subscriptions/
Authorization: Bearer <token>
```

### List Available Authors
```http
GET /api/v1/subscriptions/authors?skip=0&limit=100
Authorization: Bearer <token>
```

### Unsubscribe from Author
```http
DELETE /api/v1/subscriptions/{author_id}
Authorization: Bearer <token>
```

## Search & RAG

### Semantic Search
```http
POST /api/v1/search/semantic
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What is confirmation bias?",
  "limit": 10
}
```

Response:
```json
{
  "query": "What is confirmation bias?",
  "results": [
    {
      "id": "chunk_id",
      "text": "Confirmation bias is...",
      "score": 0.85,
      "author_id": 1,
      "book_id": 1,
      "section_title": "Cognitive Biases",
      "chunk_type": "semantic",
      "token_count": 420
    }
  ],
  "total_results": 5,
  "subscribed_authors": [1, 2, 3]
}
```

### RAG Query
```http
POST /api/v1/search/rag
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Explain confirmation bias with examples",
  "max_chunks": 8
}
```

Response:
```json
{
  "answer": "Confirmation bias is the tendency to search for, interpret, and recall information in a way that confirms our pre-existing beliefs...",
  "sources": [
    {
      "book_id": 1,
      "section_title": "Cognitive Biases",
      "score": 0.85,
      "chunk_type": "semantic"
    }
  ],
  "total_chunks": 3,
  "query": "Explain confirmation bias with examples"
}
```

### Search Statistics
```http
GET /api/v1/search/stats
Authorization: Bearer <token>
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- Authentication endpoints: 5 requests per minute
- Search endpoints: 100 requests per minute
- Upload endpoints: 10 requests per hour
- Other endpoints: 1000 requests per hour

## Pagination

List endpoints support pagination:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 1000)