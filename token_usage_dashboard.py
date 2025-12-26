#!/usr/bin/env python3
"""
Token Usage Dashboard
Simple script to view token usage statistics from the logs.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import argparse

def load_token_logs(days=7):
    """Load token usage logs from the last N days."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ No logs directory found. Make sure the application has been running.")
        return []
    
    all_logs = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = logs_dir / f"token_usage_{date}.jsonl"
        
        if log_file.exists():
            print(f"📖 Reading {log_file}")
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            log_entry = json.loads(line.strip())
                            log_time = datetime.fromisoformat(log_entry["timestamp"])
                            
                            if log_time >= cutoff_date:
                                all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            print(f"⚠️  Skipping invalid JSON on line {line_num} in {log_file}")
                        except Exception as e:
                            print(f"⚠️  Error processing line {line_num} in {log_file}: {e}")
            except Exception as e:
                print(f"❌ Error reading {log_file}: {e}")
    
    return all_logs

def analyze_logs(logs):
    """Analyze token usage logs and generate statistics."""
    if not logs:
        return None
    
    stats = {
        "total_operations": len(logs),
        "total_tokens": 0,
        "total_cost": 0.0,
        "by_user": defaultdict(lambda: {"operations": 0, "tokens": 0, "cost": 0.0}),
        "by_operation": defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0}),
        "by_model": defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0}),
        "by_day": defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0}),
        "success_rate": 0.0,
        "failed_operations": []
    }
    
    successful_ops = 0
    
    for log in logs:
        # Overall stats
        stats["total_tokens"] += log["total_tokens"]
        stats["total_cost"] += log["cost_estimate"]
        
        if log["success"]:
            successful_ops += 1
        else:
            stats["failed_operations"].append({
                "timestamp": log["timestamp"],
                "user_id": log["user_id"],
                "operation": log["operation_type"],
                "error": log.get("error_message", "Unknown error")
            })
        
        # By user
        user_id = log["user_id"]
        stats["by_user"][user_id]["operations"] += 1
        stats["by_user"][user_id]["tokens"] += log["total_tokens"]
        stats["by_user"][user_id]["cost"] += log["cost_estimate"]
        
        # By operation type
        op_type = log["operation_type"]
        stats["by_operation"][op_type]["count"] += 1
        stats["by_operation"][op_type]["tokens"] += log["total_tokens"]
        stats["by_operation"][op_type]["cost"] += log["cost_estimate"]
        
        # By model
        model = log["model_name"]
        stats["by_model"][model]["count"] += 1
        stats["by_model"][model]["tokens"] += log["total_tokens"]
        stats["by_model"][model]["cost"] += log["cost_estimate"]
        
        # By day
        day = log["timestamp"][:10]  # Extract YYYY-MM-DD
        stats["by_day"][day]["count"] += 1
        stats["by_day"][day]["tokens"] += log["total_tokens"]
        stats["by_day"][day]["cost"] += log["cost_estimate"]
    
    stats["success_rate"] = (successful_ops / len(logs)) * 100 if logs else 0
    
    return stats

def print_dashboard(stats, days):
    """Print a formatted dashboard of token usage statistics."""
    if not stats:
        print("❌ No token usage data found.")
        return
    
    print("=" * 80)
    print(f"🪙 TOKEN USAGE DASHBOARD - Last {days} days")
    print("=" * 80)
    
    # Overall stats
    print(f"\n📊 OVERALL STATISTICS")
    print(f"   Total Operations: {stats['total_operations']:,}")
    print(f"   Total Tokens: {stats['total_tokens']:,}")
    print(f"   Total Cost: ${stats['total_cost']:.6f}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Avg Tokens/Op: {stats['total_tokens'] / stats['total_operations']:.1f}")
    
    # By operation type
    print(f"\n🔧 BY OPERATION TYPE")
    for op_type, data in sorted(stats["by_operation"].items()):
        avg_tokens = data["tokens"] / data["count"] if data["count"] > 0 else 0
        print(f"   {op_type:15} | {data['count']:4} ops | {data['tokens']:8,} tokens | ${data['cost']:.6f} | {avg_tokens:.1f} avg")
    
    # By model
    print(f"\n🤖 BY MODEL")
    for model, data in sorted(stats["by_model"].items()):
        avg_tokens = data["tokens"] / data["count"] if data["count"] > 0 else 0
        print(f"   {model:25} | {data['count']:4} ops | {data['tokens']:8,} tokens | ${data['cost']:.6f} | {avg_tokens:.1f} avg")
    
    # By user (top 10)
    print(f"\n👥 BY USER (Top 10)")
    sorted_users = sorted(stats["by_user"].items(), key=lambda x: x[1]["tokens"], reverse=True)
    for user_id, data in sorted_users[:10]:
        avg_tokens = data["tokens"] / data["operations"] if data["operations"] > 0 else 0
        print(f"   User {user_id:8} | {data['operations']:4} ops | {data['tokens']:8,} tokens | ${data['cost']:.6f} | {avg_tokens:.1f} avg")
    
    # Daily breakdown
    print(f"\n📅 DAILY BREAKDOWN")
    for day, data in sorted(stats["by_day"].items(), reverse=True):
        avg_tokens = data["tokens"] / data["count"] if data["count"] > 0 else 0
        print(f"   {day} | {data['count']:4} ops | {data['tokens']:8,} tokens | ${data['cost']:.6f} | {avg_tokens:.1f} avg")
    
    # Failed operations
    if stats["failed_operations"]:
        print(f"\n❌ FAILED OPERATIONS ({len(stats['failed_operations'])})")
        for failure in stats["failed_operations"][-5:]:  # Show last 5 failures
            print(f"   {failure['timestamp']} | User {failure['user_id']} | {failure['operation']} | {failure['error']}")
    
    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Token Usage Dashboard")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    parser.add_argument("--user", type=int, help="Filter by specific user ID")
    parser.add_argument("--operation", type=str, help="Filter by operation type")
    
    args = parser.parse_args()
    
    print(f"🚀 Loading token usage logs for the last {args.days} days...")
    logs = load_token_logs(args.days)
    
    if not logs:
        print("❌ No logs found. Make sure the application has been running and generating token usage logs.")
        sys.exit(1)
    
    # Apply filters
    if args.user:
        logs = [log for log in logs if log["user_id"] == args.user]
        print(f"🔍 Filtered to user {args.user}: {len(logs)} operations")
    
    if args.operation:
        logs = [log for log in logs if log["operation_type"] == args.operation]
        print(f"🔍 Filtered to operation '{args.operation}': {len(logs)} operations")
    
    if not logs:
        print("❌ No logs match the specified filters.")
        sys.exit(1)
    
    # Analyze and display
    stats = analyze_logs(logs)
    print_dashboard(stats, args.days)

if __name__ == "__main__":
    main()