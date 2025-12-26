# Token Usage Tracking

This system now includes comprehensive token usage tracking for all OpenAI API calls. This helps you monitor costs and optimize usage patterns.

## Features

### 🪙 Token Tracking
- **Real-time logging** of all OpenAI API calls
- **Cost estimation** based on current OpenAI pricing
- **Operation categorization** (search, RAG answers, embeddings)
- **User-specific tracking** for multi-user environments
- **Performance metrics** including response times

### 📊 Analytics & Reporting
- **Daily logs** stored in JSONL format
- **Web dashboard** for visual analytics
- **CLI dashboard** for quick terminal access
- **API endpoints** for programmatic access

## Usage

### Web Dashboard
Visit `/token-usage` in your browser to see:
- Total operations, tokens, and costs
- Breakdown by operation type and model
- Daily usage patterns
- User-specific statistics

### CLI Dashboard
```bash
# View last 7 days
python token_usage_dashboard.py

# View last 30 days
python token_usage_dashboard.py --days 30

# Filter by user
python token_usage_dashboard.py --user 123

# Filter by operation type
python token_usage_dashboard.py --operation rag_answer
```

### API Endpoints

#### Get User Token Usage
```bash
GET /api/v1/search/token-usage?days=7
```

#### Get Recent Operations
```bash
GET /api/v1/search/token-usage/recent?limit=20
```

#### Get System-wide Stats (Admin)
```bash
GET /api/v1/search/token-usage/all?days=7
```

## Log Format

Token usage logs are stored in `logs/token_usage_YYYY-MM-DD.jsonl`:

```json
{
  "timestamp": "2024-12-26T10:30:45.123456",
  "user_id": 123,
  "operation_type": "rag_answer",
  "query": "What is the meaning of life?",
  "model_name": "gpt-4o-mini",
  "prompt_tokens": 1250,
  "completion_tokens": 150,
  "total_tokens": 1400,
  "cost_estimate": 0.000285,
  "response_time": 2.34,
  "success": true,
  "error_message": null
}
```

## Operation Types

- **`embedding`** - Text embedding generation for search queries
- **`batch_embedding`** - Bulk embedding generation for PDF uploads
- **`rag_answer`** - Full RAG response generation
- **`rag_streaming`** - Streaming RAG responses

## 🔍 **Why You Might Not See Search Token Usage**

**Normal Search (`/semantic`)** DOES use AI calls, but you might not see them because:

### 1. **Aggressive Caching** 
- **Session cache**: Same query in one session = no API call
- **Persistent cache**: Same query ever used = no API call  
- **Search results cache**: Entire search results are cached

### 2. **Small Token Counts**
- **Embeddings**: Usually 5-50 tokens (very cheap)
- **RAG answers**: 1000-3000+ tokens (much more expensive)
- You'll notice RAG costs much more than search costs

### 3. **Cache Hit Rate**
The system shows cache statistics like:
```
📊 Cache: 85.2% hit rate | Session: 45 | Persistent: 1,234
```

### 🧪 **Test Token Tracking**

To verify search token tracking is working:

```bash
# Test with unique queries to avoid cache
python3 test_search_tokens.py
```

### 📊 **Expected Token Usage**

**For a typical search:**
- **First time**: ~10-30 tokens for embedding
- **Cached**: 0 tokens (no API call)

**For a typical RAG answer:**
- **Search embedding**: ~10-30 tokens  
- **Answer generation**: 1000-3000+ tokens
- **Total**: Much higher cost

### 💡 **Pro Tip**
Use unique, varied search queries to see embedding token usage. Repeated or similar queries will use cached embeddings.

## Cost Estimation

Current pricing (as of Dec 2024):
- **GPT-4o Mini**: $0.15/1M input tokens, $0.60/1M output tokens
- **text-embedding-3-small**: $0.02/1M tokens
- **text-embedding-3-large**: $0.13/1M tokens

## Monitoring & Alerts

### High Usage Detection
The system logs warnings for:
- Operations exceeding expected token counts
- Failed API calls
- Unusual usage patterns

### Cost Optimization Tips
1. **Cache embeddings** - The system already caches embeddings aggressively
2. **Optimize chunk sizes** - Smaller chunks = fewer tokens per search
3. **Limit search results** - Fewer results = smaller context = fewer tokens
4. **Monitor streaming vs. regular** - Streaming may use slightly more tokens

## Configuration

### Token Costs
Update costs in `app/services/token_tracker.py`:

```python
self.token_costs = {
    "gpt-4o-mini": {
        "input": 0.00015,   # $0.15 per 1M input tokens
        "output": 0.0006    # $0.60 per 1M output tokens
    }
}
```

### Log Retention
Logs are stored daily. You may want to implement log rotation:

```bash
# Keep only last 30 days
find logs/ -name "token_usage_*.jsonl" -mtime +30 -delete
```

## Integration Examples

### Budget Alerts
```python
from app.services.token_tracker import token_tracker

# Check daily usage
stats = token_tracker.get_usage_stats(days=1)
if stats["total_cost"] > 10.0:  # $10 daily limit
    send_alert(f"Daily token cost exceeded: ${stats['total_cost']:.2f}")
```

### User Limits
```python
# Check user's monthly usage
user_stats = token_tracker.get_usage_stats(user_id=123, days=30)
if user_stats["total_cost"] > 50.0:  # $50 monthly limit
    raise HTTPException(status_code=429, detail="Monthly token limit exceeded")
```

## Troubleshooting

### No Logs Generated
1. Check if `logs/` directory exists and is writable
2. Verify token tracker is imported and used in services
3. Check console output for token usage messages

### Inaccurate Cost Estimates
1. Update pricing in `token_tracker.py`
2. For streaming responses, costs are estimated (OpenAI doesn't always provide exact usage)
3. Check OpenAI usage dashboard for actual billing

### Performance Impact
Token tracking adds minimal overhead:
- ~1ms per API call for logging
- Logs are written asynchronously
- No impact on API response times

## Future Enhancements

- **Real-time alerts** via webhooks
- **Budget enforcement** with automatic limits
- **Usage predictions** based on historical data
- **Integration with billing systems**
- **Advanced analytics** with charts and trends