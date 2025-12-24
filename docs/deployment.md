# Deployment Guide

## Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 12+
- Pinecone API key
- OpenAI API key

### Environment Setup
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Update environment variables

## Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
createdb bookrag

# Run migrations
alembic upgrade head
```

### 3. Start Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Note: Pinecone index will be created automatically on first use.

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/bookrag
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=bookrag
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Cloud Deployment (AWS)

#### 1. Infrastructure Setup
```bash
# RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier bookrag-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password password \
  --allocated-storage 20

# ECS Cluster
aws ecs create-cluster --cluster-name bookrag-cluster

# S3 Bucket for file storage
aws s3 mb s3://bookrag-uploads
```

#### 2. ECS Task Definition
```json
{
  "family": "bookrag-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "bookrag-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/bookrag:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://admin:password@rds-endpoint:5432/bookrag"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bookrag-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Kubernetes Deployment

#### 1. Deployment YAML
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bookrag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bookrag-api
  template:
    metadata:
      labels:
        app: bookrag-api
    spec:
      containers:
      - name: bookrag-api
        image: bookrag:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bookrag-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: bookrag-secrets
              key: openai-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: bookrag-service
spec:
  selector:
    app: bookrag-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Environment Variables

### Required
- `DATABASE_URL`: PostgreSQL connection string
- `PINECONE_API_KEY`: Pinecone API key for vector storage
- `OPENAI_API_KEY`: OpenAI API key for embeddings and RAG
- `SECRET_KEY`: JWT signing key

### Optional
- `PINECONE_ENVIRONMENT`: Pinecone environment (default: us-east-1-aws)
- `PINECONE_INDEX_NAME`: Pinecone index name (default: book-chunks)
- `UPLOAD_DIR`: File upload directory (default: ./uploads)
- `MAX_FILE_SIZE`: Maximum upload size in bytes (default: 100MB)

## Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/api/v1/search/stats
```

### Logging
- Application logs: JSON structured logging
- Access logs: Nginx/ALB format
- Error tracking: Sentry integration recommended

### Metrics
- Response times
- Error rates
- Database connection pool
- Vector search latency
- Embedding API costs

## Security Considerations

### API Security
- HTTPS only in production
- CORS configuration
- Rate limiting
- Input validation

### Database Security
- Connection encryption
- Regular backups
- Access controls

### File Security
- Virus scanning for uploads
- File type validation
- Size limits
- Secure storage

## Scaling

### Horizontal Scaling
- Stateless API design allows multiple instances
- Load balancer distribution
- Database connection pooling

### Vertical Scaling
- CPU: Embedding generation
- Memory: Vector operations
- Storage: PDF files and database

### Performance Optimization
- Redis caching for frequent queries
- CDN for static assets
- Database query optimization
- Vector search tuning