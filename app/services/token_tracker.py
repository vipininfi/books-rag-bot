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
        
        # Create logs directory if it doesn't exist
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.logs_dir / f"token_usage_{today}.jsonl"
        
        logger.info(f"TokenTracker initialized. Logging to: {self.log_file}")
    
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
        
        # Write to log file
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
        """Get token usage statistics."""
        
        stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "operations_count": 0,
            "by_operation": {},
            "by_model": {},
            "by_day": {},
            "average_tokens_per_operation": 0,
            "success_rate": 0.0
        }
        
        # Read recent log files
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.logs_dir / f"token_usage_{date}.jsonl"
            
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                usage_data = json.loads(line.strip())
                                usage_time = datetime.fromisoformat(usage_data["timestamp"])
                                
                                # Skip if outside date range or wrong user
                                if usage_time < cutoff_date:
                                    continue
                                if user_id and usage_data["user_id"] != user_id:
                                    continue
                                
                                # Update stats
                                stats["total_tokens"] += usage_data["total_tokens"]
                                stats["total_cost"] += usage_data["cost_estimate"]
                                stats["operations_count"] += 1
                                
                                # By operation type
                                op_type = usage_data["operation_type"]
                                if op_type not in stats["by_operation"]:
                                    stats["by_operation"][op_type] = {
                                        "count": 0, "tokens": 0, "cost": 0.0
                                    }
                                stats["by_operation"][op_type]["count"] += 1
                                stats["by_operation"][op_type]["tokens"] += usage_data["total_tokens"]
                                stats["by_operation"][op_type]["cost"] += usage_data["cost_estimate"]
                                
                                # By model
                                model = usage_data["model_name"]
                                if model not in stats["by_model"]:
                                    stats["by_model"][model] = {
                                        "count": 0, "tokens": 0, "cost": 0.0
                                    }
                                stats["by_model"][model]["count"] += 1
                                stats["by_model"][model]["tokens"] += usage_data["total_tokens"]
                                stats["by_model"][model]["cost"] += usage_data["cost_estimate"]
                                
                                # By day
                                day = usage_time.strftime("%Y-%m-%d")
                                if day not in stats["by_day"]:
                                    stats["by_day"][day] = {
                                        "count": 0, "tokens": 0, "cost": 0.0
                                    }
                                stats["by_day"][day]["count"] += 1
                                stats["by_day"][day]["tokens"] += usage_data["total_tokens"]
                                stats["by_day"][day]["cost"] += usage_data["cost_estimate"]
                                
                            except json.JSONDecodeError:
                                continue
                                
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
        
        # Calculate averages
        if stats["operations_count"] > 0:
            stats["average_tokens_per_operation"] = stats["total_tokens"] / stats["operations_count"]
        
        return stats
    
    def get_recent_operations(
        self, 
        user_id: Optional[int] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent operations for debugging."""
        
        operations = []
        
        # Read today's log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"token_usage_{today}.jsonl"
        
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                # Read from end of file (most recent first)
                for line in reversed(lines[-limit:]):
                    try:
                        usage_data = json.loads(line.strip())
                        
                        # Filter by user if specified
                        if user_id and usage_data["user_id"] != user_id:
                            continue
                            
                        operations.append(usage_data)
                        
                        if len(operations) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                logger.error(f"Error reading recent operations: {e}")
        
        return operations

# Global token tracker instance
token_tracker = TokenTracker()