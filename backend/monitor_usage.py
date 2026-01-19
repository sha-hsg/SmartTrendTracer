#!/usr/bin/env python3
"""
Monitor Twitter API usage for Basic Account
Shows current usage, projections, and recommendations
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich import box

# Load environment
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.smarttrendtracer

# Constants
MONTHLY_LIMIT = 10000
DAILY_BUDGET = 333
TIMELINE_LIMIT_PER_WINDOW = 15
SEARCH_LIMIT_PER_WINDOW = 60

console = Console()

def get_monthly_stats():
    """Get monthly usage statistics"""
    current_date = datetime.now()
    month_start = datetime(current_date.year, current_date.month, 1, tzinfo=timezone.utc)
    
    # Count tweets collected this month
    tweet_count = db.tweets.count_documents({
        "collected_at": {"$gte": month_start}
    })
    
    # Calculate projections
    days_elapsed = current_date.day
    days_in_month = 30  # Approximate
    daily_rate = tweet_count / days_elapsed if days_elapsed > 0 else 0
    projected_monthly = daily_rate * days_in_month
    
    return {
        "collected": tweet_count,
        "limit": MONTHLY_LIMIT,
        "used_percentage": (tweet_count / MONTHLY_LIMIT) * 100,
        "remaining": MONTHLY_LIMIT - tweet_count,
        "daily_average": daily_rate,
        "projected": projected_monthly,
        "days_elapsed": days_elapsed,
        "days_remaining": days_in_month - days_elapsed
    }

def get_daily_stats():
    """Get daily usage statistics"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    
    # Count tweets collected today
    tweet_count = db.tweets.count_documents({
        "collected_at": {"$gte": today_start}
    })
    
    # Calculate hourly rate
    hours_elapsed = (datetime.now(timezone.utc) - today_start).total_seconds() / 3600
    hourly_rate = tweet_count / hours_elapsed if hours_elapsed > 0 else 0
    projected_daily = hourly_rate * 24
    
    return {
        "collected": tweet_count,
        "budget": DAILY_BUDGET,
        "used_percentage": (tweet_count / DAILY_BUDGET) * 100,
        "remaining": DAILY_BUDGET - tweet_count,
        "hourly_rate": hourly_rate,
        "projected": projected_daily,
        "hours_elapsed": hours_elapsed
    }

def get_account_stats():
    """Get per-account collection statistics"""
    pipeline = [
        {
            "$match": {
                "collected_at": {
                    "$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                }
            }
        },
        {
            "$group": {
                "_id": "$author_username",
                "count": {"$sum": 1},
                "latest": {"$max": "$created_at"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    return list(db.tweets.aggregate(pipeline))

def get_collection_state():
    """Get last collection times for all accounts"""
    states = {}
    for state in db.collection_state.find():
        if state.get("last_run"):
            # Handle both string IDs and ObjectIds
            state_id = str(state["_id"])
            username = state_id.replace("twitter_", "").replace("twitter_search_", "")
            if username not in states or state["last_run"] > states[username]:
                states[username] = state["last_run"]
    return states

def display_dashboard():
    """Display usage dashboard"""
    console.clear()
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]Twitter API Usage Monitor - Basic Account[/bold cyan]",
        border_style="cyan"
    ))
    
    # Get stats
    monthly = get_monthly_stats()
    daily = get_daily_stats()
    accounts = get_account_stats()
    last_runs = get_collection_state()
    
    # Monthly Usage Panel
    monthly_table = Table(box=box.ROUNDED)
    monthly_table.add_column("Metric", style="cyan")
    monthly_table.add_column("Value", justify="right")
    monthly_table.add_column("Status")
    
    monthly_table.add_row(
        "Tweets Collected",
        f"{monthly['collected']:,}",
        f"[green]{monthly['used_percentage']:.1f}%[/green]" if monthly['used_percentage'] < 80 
        else f"[yellow]{monthly['used_percentage']:.1f}%[/yellow]" if monthly['used_percentage'] < 90
        else f"[red]{monthly['used_percentage']:.1f}%[/red]"
    )
    monthly_table.add_row("Monthly Limit", f"{monthly['limit']:,}", "")
    monthly_table.add_row("Remaining", f"{monthly['remaining']:,}", 
                         "[green]✓[/green]" if monthly['remaining'] > 2000 else "[yellow]⚠[/yellow]")
    monthly_table.add_row("Daily Average", f"{monthly['daily_average']:.0f}", "")
    monthly_table.add_row(
        "Projected Total",
        f"{monthly['projected']:,.0f}",
        "[green]✓[/green]" if monthly['projected'] < MONTHLY_LIMIT * 0.9 else "[red]⚠[/red]"
    )
    monthly_table.add_row("Days Elapsed", f"{monthly['days_elapsed']}", f"{monthly['days_remaining']} remaining")
    
    console.print(Panel(monthly_table, title="[bold]Monthly Usage[/bold]", border_style="blue"))
    
    # Daily Usage Panel
    daily_table = Table(box=box.ROUNDED)
    daily_table.add_column("Metric", style="cyan")
    daily_table.add_column("Value", justify="right")
    daily_table.add_column("Status")
    
    daily_table.add_row(
        "Tweets Today",
        f"{daily['collected']}",
        f"[green]{daily['used_percentage']:.1f}%[/green]" if daily['used_percentage'] < 100
        else f"[red]{daily['used_percentage']:.1f}%[/red]"
    )
    daily_table.add_row("Daily Budget", f"{daily['budget']}", "")
    daily_table.add_row("Remaining", f"{daily['remaining']}", 
                       "[green]✓[/green]" if daily['remaining'] > 50 else "[yellow]⚠[/yellow]")
    daily_table.add_row("Hourly Rate", f"{daily['hourly_rate']:.1f}", "")
    daily_table.add_row(
        "Projected Today",
        f"{daily['projected']:.0f}",
        "[green]✓[/green]" if daily['projected'] < DAILY_BUDGET else "[red]⚠[/red]"
    )
    
    console.print(Panel(daily_table, title="[bold]Daily Usage[/bold]", border_style="green"))
    
    # Account Activity
    if accounts:
        account_table = Table(box=box.ROUNDED)
        account_table.add_column("Account", style="cyan")
        account_table.add_column("Tweets Today", justify="right")
        account_table.add_column("Last Tweet", justify="right")
        account_table.add_column("Last Check", justify="right")
        
        current_time = datetime.now(timezone.utc)
        for acc in accounts[:10]:  # Top 10
            username = acc["_id"]
            
            # Get last check time
            last_check = last_runs.get(username)
            if last_check:
                if last_check.tzinfo is None:
                    last_check = last_check.replace(tzinfo=timezone.utc)
                hours_ago = (current_time - last_check).total_seconds() / 3600
                last_check_str = f"{hours_ago:.1f}h ago"
            else:
                last_check_str = "Never"
            
            # Format last tweet time
            if acc["latest"]:
                if acc["latest"].tzinfo is None:
                    acc["latest"] = acc["latest"].replace(tzinfo=timezone.utc)
                tweet_hours = (current_time - acc["latest"]).total_seconds() / 3600
                last_tweet_str = f"{tweet_hours:.1f}h ago"
            else:
                last_tweet_str = "Unknown"
            
            account_table.add_row(
                f"@{username}",
                str(acc["count"]),
                last_tweet_str,
                last_check_str
            )
        
        console.print(Panel(account_table, title="[bold]Account Activity Today[/bold]", border_style="yellow"))
    
    # Recommendations
    recommendations = []
    
    if monthly['projected'] > MONTHLY_LIMIT * 0.95:
        recommendations.append("[red]• Reduce collection frequency - projected to exceed monthly limit![/red]")
    elif monthly['projected'] > MONTHLY_LIMIT * 0.85:
        recommendations.append("[yellow]• Monitor usage closely - approaching monthly limit[/yellow]")
    else:
        recommendations.append("[green]• Monthly usage on track[/green]")
    
    if daily['projected'] > DAILY_BUDGET:
        recommendations.append("[yellow]• Daily budget exceeded - consider reducing frequency today[/yellow]")
    else:
        recommendations.append("[green]• Daily usage within budget[/green]")
    
    if monthly['remaining'] < 1000:
        recommendations.append("[red]• Less than 1,000 tweets remaining this month![/red]")
    
    # Rate limit info
    recommendations.append(f"\n[dim]Rate Limits:[/dim]")
    recommendations.append(f"[dim]• Timeline: {TIMELINE_LIMIT_PER_WINDOW} requests per 15 min[/dim]")
    recommendations.append(f"[dim]• Search: {SEARCH_LIMIT_PER_WINDOW} requests per 15 min[/dim]")
    
    console.print(Panel("\n".join(recommendations), title="[bold]Recommendations[/bold]", border_style="magenta"))
    
    # Footer
    console.print(f"\n[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print("[dim]Press Ctrl+C to exit[/dim]")

def main():
    """Main monitoring loop"""
    try:
        import time
        while True:
            display_dashboard()
            time.sleep(30)  # Refresh every 30 seconds
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
        mongo_client.close()

if __name__ == "__main__":
    # Check if rich is installed
    try:
        import rich
    except ImportError:
        print("Installing required package: rich")
        os.system("pip install rich")
    
    main()