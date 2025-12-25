# Migration Guide: BGE + Gemini → OpenAI

This guide will help you migrate from BGE embeddings + Gemini to OpenAI embeddings + GPT-4o mini.

## 🎯 What's Changed

### Before (Old Setup):
- **Embeddings**: BGE-base-en-v1.5 (768 dimensions, local model)
- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: Pinecone index with 768 dimensions
- **Dependencies**: sentence-transformers, torch, google-generativeai

### After (New Setup):
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **LLM**: OpenAI GPT-4o mini
- **Vector DB**: New Pinecone index with 1536 dimensions
- **Dependencies**: openai (much lighter!)

## 💰 Cost Comparison

### OpenAI Pricing (Much Cheaper!):
- **Embeddings**: $0.00002 per 1K tokens (~$0.02 per book)
- **GPT-4o mini**: $0.00015 per 1K input + $0.0006 per 1K output tokens
- **Monthly estimate**: ~$15-25 for 1000 users

### Previous Costs:
- **Gemini**: More expensive per token
- **Local BGE**: Free but requires GPU/CPU resources
- **Infrastructure**: Higher server costs for local models

## 🚀 Migration Steps

### Step 1: Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add billing information (required for API access)
4. Copy your API key

### Step 2: Update Environment Configuration
```bash
# Edit your .env file
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### Step 3: Install New Dependencies
```bash
# Install new requirements
pip install -r requirements.txt

# This will install:
# - openai==1.54.4 (replaces google-generativeai)
# - Remove heavy dependencies: sentence-transformers, torch, transformers
```

### Step 4: Setup New Pinecone Index
```bash
# Run the setup script
python setup_openai_index.py

# This will:
# - Create new index with 1536 dimensions
# - Verify your OpenAI API key
# - Guide you through the process
```

### Step 5: Clear Old Vector Data
```bash
# Clear the old vector database
python clear_vector_db.py

# This will:
# - Delete all old 768-dimension vectors
# - Reset book processing status
# - Prepare for new embeddings
```

### Step 6: Test the New Setup
```bash
# Start the server
python start_server.py

# Upload a test book to verify:
# 1. New embeddings are generated (1536 dimensions)
# 2. Search works with OpenAI embeddings
# 3. RAG responses use GPT-4o mini
```

## 🔧 Technical Changes Made

### Files Modified:
1. **`.env`** - Updated API keys and model names
2. **`app/core/config.py`** - OpenAI configuration
3. **`app/services/embedding_service.py`** - Complete rewrite for OpenAI
4. **`app/services/rag_service.py`** - Complete rewrite for OpenAI
5. **`app/services/vector_store.py`** - Updated dimensions (768→1536)
6. **`requirements.txt`** - Replaced dependencies

### New Files:
1. **`setup_openai_index.py`** - Automated Pinecone setup
2. **`MIGRATION_TO_OPENAI.md`** - This guide

## ⚡ Performance Improvements

### Speed:
- **Faster startup**: No local model loading
- **Faster embeddings**: OpenAI API vs local processing
- **Better scaling**: No GPU/CPU constraints

### Quality:
- **Better embeddings**: OpenAI's latest embedding model
- **Improved responses**: GPT-4o mini vs Gemini
- **More reliable**: Hosted API vs local models

### Resource Usage:
- **Lower memory**: No local models in memory
- **Lower CPU**: No local inference
- **Smaller Docker images**: Fewer dependencies

## 🛠️ Troubleshooting

### Common Issues:

#### 1. OpenAI API Key Issues
```bash
# Error: "Invalid API key"
# Solution: Check your API key in .env file
# Make sure you have billing enabled on OpenAI account
```

#### 2. Pinecone Dimension Mismatch
```bash
# Error: "Dimension mismatch"
# Solution: Run setup_openai_index.py to create new index
# Or delete old index and create new one
```

#### 3. Import Errors
```bash
# Error: "No module named 'sentence_transformers'"
# Solution: Install new requirements.txt
pip install -r requirements.txt
```

#### 4. Old Vector Data
```bash
# Error: Search returns no results
# Solution: Clear old vectors and re-upload books
python clear_vector_db.py
```

## 📊 Monitoring & Verification

### Check Migration Success:
1. **API Logs**: Look for "OpenAI" instead of "BGE" or "Gemini"
2. **Vector Dimensions**: New vectors should be 1536-dimensional
3. **Response Quality**: Test RAG responses for improvement
4. **Cost Tracking**: Monitor OpenAI usage dashboard

### Health Checks:
```python
# Test embedding service
from app.services.embedding_service import EmbeddingService
service = EmbeddingService()
print(service.get_model_info())
# Should show: text-embedding-3-small, 1536 dimensions

# Test RAG service  
from app.services.rag_service import RAGService
rag = RAGService()
print(rag.get_model_info())
# Should show: gpt-4o-mini
```

## 🎉 Benefits After Migration

### For Users:
- **Faster responses**: API calls vs local processing
- **Better accuracy**: Improved embeddings and LLM
- **More reliable**: No local model crashes

### For Developers:
- **Easier deployment**: No GPU requirements
- **Lower costs**: Cheaper API pricing
- **Better scaling**: Cloud-native architecture
- **Simpler maintenance**: No local model updates

### For Business:
- **Reduced infrastructure costs**: Smaller servers
- **Better user experience**: Faster, more accurate responses
- **Easier scaling**: Pay-per-use model
- **Future-proof**: Latest OpenAI models

## 📞 Support

If you encounter issues during migration:

1. **Check logs**: Look for specific error messages
2. **Verify API keys**: Ensure OpenAI key is valid and has billing
3. **Test components**: Use the health checks above
4. **Clear and restart**: Clear vectors and restart server

The migration should significantly improve both performance and cost-effectiveness of your Book RAG system!