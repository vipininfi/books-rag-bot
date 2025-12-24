# Quick Start Guide

## ✅ Status Check

Your Book RAG System is now configured with:
- ✅ **Pinecone**: Connected and ready (index: `book-chunks`)
- ⚠️  **OpenAI**: API key needed for full functionality
- ⚠️  **PostgreSQL**: Database setup needed

## 🚀 Next Steps

### 1. Add OpenAI API Key
Edit `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 2. Setup Database
```bash
# Install PostgreSQL (if not installed)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb bookrag

# Update database URL in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/bookrag

# Run migrations
alembic upgrade head
```

### 3. Start the API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API
Visit: http://localhost:8000/docs

## 🧪 Test Commands

### Test Pinecone Connection
```bash
python test_pinecone.py
```

### Test Full Integration (after adding OpenAI key)
```bash
python test_pinecone.py
```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login user

### Books
- `POST /api/v1/books/upload` - Upload PDF book
- `GET /api/v1/books/{book_id}` - Get book details

### Subscriptions
- `POST /api/v1/subscriptions/` - Subscribe to author
- `GET /api/v1/subscriptions/` - Get my subscriptions

### Search & RAG
- `POST /api/v1/search/semantic` - Semantic search
- `POST /api/v1/search/rag` - RAG question answering

## 💰 Current Configuration

**Monthly Costs:**
- Pinecone: $70 (300k vectors)
- OpenAI: ~$27 (10k queries/month)
- **Total: ~$97/month** (excluding hosting)

**Break-even:** 10 users at $10/month

## 🔧 Troubleshooting

### Common Issues

1. **Import Error**: Run `pip install -r requirements.txt`
2. **Database Error**: Check PostgreSQL is running and database exists
3. **Pinecone Error**: Verify API key in `.env` file
4. **OpenAI Error**: Add valid API key to `.env` file

### Get Help
- Check logs: `tail -f app.log`
- Test components: `python test_pinecone.py`
- API docs: http://localhost:8000/docs