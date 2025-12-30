"""
Token Usage Tracking Service
Tracks and logs token consumption for OpenAI API calls.
"""

import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from app.db.database import SessionLocal
from app.models.usage import UsageLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token usage data structure."""
    timestamp: str
    user_id: int
    operation_type: str  # 'search', 'rag_answer', 'embedding'
    query: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: float
    response_time: float
    success: bool
    error_message: Optional[str] = None

class TokenTracker:
    """Tracks token usage across all AI operations."""
    
    def __init__(self):
        # Token costs per 1K tokens (as of Dec 2024)
        self.token_costs = {
            "gpt-4o-mini": {
                "input": 0.00015,   # $0.15 per 1M input tokens
                "output": 0.0006    # $0.60 per 1M output tokens
            },
            "text-embedding-3-small": {
                "input": 0.00002,   # $0.02 per 1M tokens
                "output": 0.0       # No output tokens for embeddings
            },
            "text-embedding-3-large": {
                "input": 0.00013,   # $0.13 per 1M tokens
                "output": 0.0
            }
        }
        
        # Create logs directory if it doesn't exist (keeping for backward compatibility/backup)
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.logs_dir / f"token_usage_{today}.jsonl"
        
        logger.info(f"TokenTracker initialized. Logging to database and {self.log_file}")
    
    def calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost for token usage."""
        if model_name not in self.token_costs:
            logger.warning(f"Unknown model: {model_name}. Using default cost.")
            return 0.0
        
        costs = self.token_costs[model_name]
        
        # Convert to cost per token (from per 1K tokens)
        input_cost = (prompt_tokens / 1000) * costs["input"]
        output_cost = (completion_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def log_usage(
        self,
        user_id: int,
        operation_type: str,
        query: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        response_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> TokenUsage:
        """Log token usage for an operation."""
        
        total_tokens = prompt_tokens + completion_tokens
        cost_estimate = self.calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            operation_type=operation_type,
            query=query[:200],  # Truncate long queries
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate,
            response_time=response_time,
            success=success,
            error_message=error_message
        )
        
        # Write to database
        db = SessionLocal()
        try:
            db_log = UsageLog(
                user_id=user_id,
                operation_type=operation_type,
                query=query[:200],
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_estimate=cost_estimate,
                response_time=response_time,
                success=success,
                error_message=error_message
            )
            db.add(db_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to write token usage to database: {e}")
            db.rollback()
        finally:
            db.close()

        # Write to log file (keeping as backup)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(usage)) + "\n")
        except Exception as e:
            logger.error(f"Failed to write token usage log: {e}")
        
        # Log to console for immediate visibility
        logger.info(
            f"🪙 TOKEN USAGE | User:{user_id} | {operation_type} | "
            f"Model:{model_name} | Tokens:{total_tokens} "
            f"(prompt:{prompt_tokens}, completion:{completion_tokens}) | "
            f"Cost:${cost_estimate:.6f} | Time:{response_time:.3f}s"
        )
        
        return usage
    
    def log_openai_response(
        self,
        user_id: int,
        operation_type: str,
        query: str,
        response: Any,
        response_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[TokenUsage]:
        """Log token usage from OpenAI response object."""
        
        try:
            if hasattr(response, 'usage') and response.usage:
                # Handle different response types
                if hasattr(response.usage, 'completion_tokens'):
                    # Chat completion response
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                else:
                    # Embedding response (no completion tokens)
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = 0
                
                return self.log_usage(
                    user_id=user_id,
                    operation_type=operation_type,
                    query=query,
                    model_name=response.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time=response_time,
                    success=success,
                    error_message=error_message
                )
            else:
                logger.warning(f"No usage data in OpenAI response for {operation_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract token usage from response: {e}")
            return None
    
    def get_usage_stats(
        self, 
        user_id: Optional[int] = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        """Get token usage statistics from the database."""
        
        stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "operations_count": 0,
            "breakdown": {
                "book_processing": {"tokens": 0, "cost": 0.0, "count": 0},
                "ai_conversations": {
                    "tokens": 0, "cost": 0.0, "count": 0,
                    "embedding": {"tokens": 0, "cost": 0.0},
                    "prompt": {"tokens": 0, "cost": 0.0},
                    "answer": {"tokens": 0, "cost": 0.0}
                },
                "search_activity": {"tokens": 0, "cost": 0.0, "count": 0}
            },
            "by_day": {}
        }
        
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = db.query(UsageLog).filter(UsageLog.timestamp >= cutoff_date)
            
            if user_id:
                query = query.filter(UsageLog.user_id == user_id)
            
            logs = query.all()
            
            for log in logs:
                # Update global stats
                stats["total_tokens"] += log.total_tokens
                stats["total_cost"] += log.cost_estimate
                stats["operations_count"] += 1
                
                # Granular breakdown
                op_type = log.operation_type
                tokens = log.total_tokens
                cost = log.cost_estimate
                prompt_tokens = log.prompt_tokens
                completion_tokens = log.completion_tokens
                
                # Calculate prompt/completion costs
                model = log.model_name
                costs_config = self.token_costs.get(model, {"input": 0, "output": 0})
                prompt_cost = (prompt_tokens / 1000) * costs_config.get("input", 0)
                completion_cost = (completion_tokens / 1000) * costs_config.get("output", 0)

                if op_type == "book_batch_embedding":
                    stats["breakdown"]["book_processing"]["tokens"] += tokens
                    stats["breakdown"]["book_processing"]["cost"] += cost
                    stats["breakdown"]["book_processing"]["count"] += 1
                
                elif op_type == "rag_answer":
                    stats["breakdown"]["ai_conversations"]["tokens"] += tokens
                    stats["breakdown"]["ai_conversations"]["cost"] += cost
                    stats["breakdown"]["ai_conversations"]["count"] += 1
                    stats["breakdown"]["ai_conversations"]["prompt"]["tokens"] += prompt_tokens
                    stats["breakdown"]["ai_conversations"]["prompt"]["cost"] += prompt_cost
                    stats["breakdown"]["ai_conversations"]["answer"]["tokens"] += completion_tokens
                    stats["breakdown"]["ai_conversations"]["answer"]["cost"] += completion_cost
                
                elif op_type == "rag_embedding":
                    stats["breakdown"]["ai_conversations"]["embedding"]["tokens"] += tokens
                    stats["breakdown"]["ai_conversations"]["embedding"]["cost"] += cost
                
                elif op_type == "search_embedding":
                    stats["breakdown"]["search_activity"]["tokens"] += tokens
                    stats["breakdown"]["search_activity"]["cost"] += cost
                    stats["breakdown"]["search_activity"]["count"] += 1
                
                # By day
                day = log.timestamp.strftime("%Y-%m-%d")
                if day not in stats["by_day"]:
                    stats["by_day"][day] = {"tokens": 0, "cost": 0.0}
                stats["by_day"][day]["tokens"] += tokens
                stats["by_day"][day]["cost"] += cost
                
        except Exception as e:
            logger.error(f"Error getting usage stats from database: {e}")
        finally:
            db.close()
        
        return stats
    
    def get_recent_operations(
        self, 
        user_id: Optional[int] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent operations from the database."""
        
        db = SessionLocal()
        try:
            query = db.query(UsageLog).order_by(UsageLog.timestamp.desc())
            
            if user_id:
                query = query.filter(UsageLog.user_id == user_id)
            
            logs = query.limit(limit).all()
            
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "operation_type": log.operation_type,
                    "query": log.query,
                    "model_name": log.model_name,
                    "prompt_tokens": log.prompt_tokens,
                    "completion_tokens": log.completion_tokens,
                    "total_tokens": log.total_tokens,
                    "cost_estimate": log.cost_estimate,
                    "response_time": log.response_time,
                    "success": log.success,
                    "error_message": log.error_message
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error getting recent operations from database: {e}")
            return []
        finally:
            db.close()

# Global token tracker instance
token_tracker = TokenTracker()