# Cost Analysis

## Executive Summary

This document provides a detailed cost breakdown for the Book RAG System, covering embedding generation, storage, query processing, and operational costs.

## Assumptions

### Scale
- **Authors**: 200
- **Books per author**: 5 (average)
- **Total books**: 1,000
- **Average book size**: 300 pages
- **Tokens per page**: 500
- **Total tokens**: 150M tokens
- **Chunks per book**: 300
- **Total chunks**: 300,000

### Usage Patterns
- **Daily queries**: 10,000
- **Monthly active users**: 1,000
- **Average subscriptions per user**: 3 authors
- **RAG vs Search ratio**: 30% RAG, 70% search-only

## One-Time Costs (Setup)

### Embedding Generation
| Component | Cost per 1M tokens | Total tokens | Total cost |
|-----------|-------------------|--------------|------------|
| BGE-Base (Local) | $0 | 150M | **$0** |
| text-embedding-3-small | $0.02 | 150M | $3.00 |
| text-embedding-3-large | $0.13 | 150M | $19.50 |

**Recommendation**: Use BGE-Base for zero ongoing embedding costs.

### Development & Setup
| Component | Cost |
|-----------|------|
| Initial development | $15,000 - $25,000 |
| Testing & QA | $3,000 - $5,000 |
| Documentation | $2,000 - $3,000 |
| **Total** | **$20,000 - $33,000** |

## Monthly Operational Costs

### 1. Vector Database Storage

#### Pinecone (Managed - Recommended)
| Tier | Storage | Monthly cost |
|-------|---------|--------------|
| Starter | 100k vectors | $70 |
| Standard | 1M vectors | $70 + usage |
| **For 300k vectors** | **~300k vectors** | **$70** |

#### Alternative: Qdrant (Self-hosted)
| Component | Specification | Monthly cost |
|-----------|---------------|--------------|
| Server (4 vCPU, 16GB RAM) | AWS c5.xlarge | $140 |
| Storage (100GB SSD) | EBS gp3 | $10 |
| **Total Qdrant** | | **$150** |

### 2. Database (PostgreSQL)
| Provider | Specification | Monthly cost |
|----------|---------------|--------------|
| AWS RDS | db.t3.small | $25 |
| Google Cloud SQL | db-f1-micro | $15 |
| **Self-hosted** | **2 vCPU, 4GB RAM** | **$35** |

### 3. Application Hosting
| Provider | Specification | Monthly cost |
|----------|---------------|--------------|
| AWS ECS Fargate | 0.5 vCPU, 1GB RAM | $15 |
| Google Cloud Run | 1 vCPU, 2GB RAM | $20 |
| **DigitalOcean Droplet** | **2 vCPU, 4GB RAM** | **$24** |

### 4. File Storage
| Component | Storage needed | Monthly cost |
|-----------|----------------|--------------|
| PDF files | 50GB | $1.15 (S3) |
| Backups | 20GB | $0.46 (S3) |
| **Total Storage** | | **$1.61** |

### 5. Query Processing Costs

#### Gemini API Usage
| Operation | Volume/month | Cost per 1M tokens | Monthly cost |
|-----------|--------------|-------------------|--------------|
| Query embeddings | 300k queries | $0 (BGE local) | $0 |
| RAG completions | 90k queries × 2k tokens | $0.075 (Gemini 2.0 Flash) | $13.50 |
| **Total AI APIs** | | | **$13.50** |

#### Alternative: Local Models
| Component | Specification | Monthly cost |
|-----------|---------------|--------------|
| GPU server | NVIDIA T4 | $120 |
| Embedding model | BGE-large | $0 |
| LLM | Llama-2-7B | $0 |
| **Total Local** | | **$120** |

## Total Monthly Costs

### Recommended Configuration
| Component | Monthly cost |
|-----------|--------------|
| Pinecone | $70 |
| PostgreSQL (self-hosted) | $35 |
| Application hosting | $24 |
| File storage | $2 |
| Gemini API | $14 |
| **Total** | **$145/month** |

### Budget Configuration
| Component | Monthly cost |
|-----------|--------------|
| Qdrant (self-hosted) | $150 |
| PostgreSQL (managed) | $25 |
| Application hosting | $15 |
| File storage | $2 |
| OpenAI API | $27 |
| **Total** | **$219/month** |

### Enterprise Configuration
| Component | Monthly cost |
|-----------|--------------|
| Pinecone (enterprise) | $200 |
| PostgreSQL (managed HA) | $150 |
| Application hosting (HA) | $100 |
| File storage + CDN | $25 |
| OpenAI API | $27 |
| Monitoring & logging | $50 |
| **Total** | **$552/month** |

## Cost Per User

### Monthly Active Users: 1,000
- **Recommended**: $0.16 per user per month
- **Budget**: $0.22 per user per month
- **Enterprise**: $0.55 per user per month

### Break-even Analysis
| Subscription price | Users needed (recommended config) |
|-------------------|-----------------------------------|
| $5/month | 32 users |
| $10/month | 16 users |
| $20/month | 8 users |

## Cost Optimization Strategies

### 1. Embedding Optimization
- **Current**: text-embedding-3-small at $3 one-time
- **Alternative**: Self-hosted BGE model (higher infra cost, zero API cost)
- **Recommendation**: Stick with OpenAI for volumes <1B tokens

### 2. Vector Database Optimization
- **Pinecone managed**: Best for production reliability
- **Qdrant self-hosted**: Best cost/performance for >1M vectors
- **pgvector**: Cheapest for <100k vectors

### 3. Query Optimization
- **Caching**: Redis for frequent queries (-30% API costs)
- **Batch processing**: Group similar queries (-20% API costs)
- **Smart routing**: Search-only vs RAG based on query type

### 4. Storage Optimization
- **Compression**: Reduce vector storage by 40%
- **Tiered storage**: Move old chunks to cheaper storage
- **Deduplication**: Remove duplicate content across books

## Scaling Projections

### 10x Scale (10,000 books, 100k daily queries)
| Component | Current | 10x scale | Multiplier |
|-----------|---------|-----------|------------|
| Vector storage | $70 | $200 | 2.9x |
| Database | $35 | $150 | 4.3x |
| API costs | $27 | $270 | 10x |
| **Total** | **$158** | **$720** | **4.6x** |

### Cost per query at scale
- **Current**: $0.016 per query
- **10x scale**: $0.007 per query
- **Efficiency gain**: 2.3x improvement

## ROI Analysis

### Revenue Potential
| Metric | Conservative | Optimistic |
|--------|--------------|------------|
| Paying users (month 12) | 500 | 2,000 |
| Average subscription | $15 | $25 |
| Monthly revenue | $7,500 | $50,000 |
| Annual revenue | $90,000 | $600,000 |

### Profitability Timeline
- **Break-even**: Month 3-6 (depending on user acquisition)
- **Positive cash flow**: Month 6-12
- **ROI**: 200-400% by year 2

## Recommendations

### Phase 1 (MVP)
- Use recommended configuration ($158/month)
- Target 100 paying users at $10/month
- Focus on user acquisition over cost optimization

### Phase 2 (Growth)
- Implement caching and query optimization
- Consider self-hosted Qdrant for cost savings
- Add usage-based pricing tiers

### Phase 3 (Scale)
- Evaluate local model deployment
- Implement advanced cost optimization
- Consider enterprise features and pricing

## Risk Factors

### Cost Risks
- **OpenAI price increases**: 20-30% annually
- **Usage spikes**: Implement rate limiting
- **Storage growth**: Monitor and optimize regularly

### Mitigation Strategies
- **Multi-provider strategy**: Support multiple embedding providers
- **Cost monitoring**: Real-time alerts and budgets
- **Usage analytics**: Identify and optimize expensive queries