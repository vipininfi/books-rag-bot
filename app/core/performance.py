"""
Performance monitoring and optimization utilities.
"""

import time
import functools
from typing import Dict, Any, Optional
import logging

# Configure performance logger
perf_logger = logging.getLogger("performance")
perf_logger.setLevel(logging.INFO)

# Performance thresholds (in seconds)
PERFORMANCE_THRESHOLDS = {
    "search_total": 2.0,      # Total search should be under 2 seconds
    "embedding": 1.0,         # Embedding generation should be under 1 second
    "vector_search": 0.5,     # Vector search should be under 0.5 seconds
    "db_query": 0.1,          # Database queries should be under 0.1 seconds
    "rag_total": 5.0,         # RAG generation should be under 5 seconds
}

class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, threshold: Optional[float] = None):
        self.operation_name = operation_name
        self.threshold = threshold or PERFORMANCE_THRESHOLDS.get(operation_name.lower(), 1.0)
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Log performance
        if duration > self.threshold:
            perf_logger.warning(
                f"⚠️ SLOW {self.operation_name}: {duration:.3f}s (threshold: {self.threshold:.3f}s)"
            )
        else:
            perf_logger.info(
                f"✅ {self.operation_name}: {duration:.3f}s"
            )
    
    @property
    def duration(self) -> float:
        """Get the duration of the timed operation."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

def performance_monitor(operation_name: str, threshold: Optional[float] = None):
    """Decorator for monitoring function performance."""
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with PerformanceTimer(operation_name, threshold):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceTimer(operation_name, threshold):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class PerformanceMetrics:
    """Collect and analyze performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record(self, operation: str, duration: float):
        """Record a performance metric."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(duration)
        
        # Keep only last 100 measurements
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        return {op: self.get_stats(op) for op in self.metrics.keys()}

# Global performance metrics instance
performance_metrics = PerformanceMetrics()

def log_performance_summary():
    """Log a summary of performance metrics."""
    stats = performance_metrics.get_all_stats()
    
    if not stats:
        return
    
    print("\n📊 PERFORMANCE SUMMARY:")
    print("=" * 50)
    
    for operation, metrics in stats.items():
        if metrics:
            print(f"{operation}:")
            print(f"  Count: {metrics['count']}")
            print(f"  Average: {metrics['avg']:.3f}s")
            print(f"  Min: {metrics['min']:.3f}s")
            print(f"  Max: {metrics['max']:.3f}s")
            print(f"  P95: {metrics['p95']:.3f}s")
            
            # Check if performance is good
            threshold = PERFORMANCE_THRESHOLDS.get(operation.lower(), 1.0)
            if metrics['avg'] > threshold:
                print(f"  ⚠️ Average exceeds threshold ({threshold:.3f}s)")
            else:
                print(f"  ✅ Performance OK")
            print()

# Optimization suggestions based on performance data
def get_optimization_suggestions() -> list:
    """Get optimization suggestions based on performance metrics."""
    suggestions = []
    stats = performance_metrics.get_all_stats()
    
    for operation, metrics in stats.items():
        if not metrics:
            continue
            
        threshold = PERFORMANCE_THRESHOLDS.get(operation.lower(), 1.0)
        
        if metrics['avg'] > threshold:
            if 'embedding' in operation.lower():
                suggestions.append(
                    f"🔧 {operation} is slow ({metrics['avg']:.3f}s). "
                    "Consider implementing embedding caching or using a faster embedding model."
                )
            elif 'vector' in operation.lower():
                suggestions.append(
                    f"🔧 {operation} is slow ({metrics['avg']:.3f}s). "
                    "Consider optimizing Pinecone queries or reducing vector dimensions."
                )
            elif 'db' in operation.lower():
                suggestions.append(
                    f"🔧 {operation} is slow ({metrics['avg']:.3f}s). "
                    "Consider adding database indexes or optimizing queries."
                )
            else:
                suggestions.append(
                    f"🔧 {operation} is slow ({metrics['avg']:.3f}s). "
                    "Consider profiling and optimizing this operation."
                )
    
    return suggestions