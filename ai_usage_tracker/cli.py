"""
CLI interface for AI Usage Tracker
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from .database import Database

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Track AI API usage and costs across multiple providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-usage-tracker init                    # Initialize database
  ai-usage-tracker status                  # Show database status
  ai-usage-tracker parse ~/.clawdbot/sessions/  # Parse session logs
  ai-usage-tracker summary                 # Show usage summary
  ai-usage-tracker budget --daily 10.0     # Set daily budget
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--db-path", help="Database path (default: ~/.local/share/ai-usage-tracker/usage.db)")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show database status")
    status_parser.add_argument("--db-path", help="Database path")
    
    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse session logs")
    parse_parser.add_argument("path", help="Path to session logs directory")
    parse_parser.add_argument("--db-path", help="Database path")
    parse_parser.add_argument("--recursive", "-r", action="store_true", help="Parse recursively")
    
    # summary command
    summary_parser = subparsers.add_parser("summary", help="Show usage summary")
    summary_parser.add_argument("--db-path", help="Database path")
    summary_parser.add_argument("--period", choices=["day", "week", "month", "all"], default="month", 
                               help="Time period for summary")
    summary_parser.add_argument("--provider", help="Filter by provider")
    
    # budget command
    budget_parser = subparsers.add_parser("budget", help="Manage budgets")
    budget_parser.add_argument("--db-path", help="Database path")
    budget_subparsers = budget_parser.add_subparsers(dest="budget_command", help="Budget command")
    
    # budget set
    budget_set = budget_subparsers.add_parser("set", help="Set budget")
    budget_set.add_argument("--provider", help="Provider name")
    budget_set.add_argument("--model", help="Model ID")
    budget_set.add_argument("--period", required=True, choices=["daily", "weekly", "monthly"], 
                           help="Budget period")
    budget_set.add_argument("--amount", type=float, required=True, help="Budget amount")
    budget_set.add_argument("--threshold", type=float, default=0.8, 
                           help="Alert threshold (0.0-1.0, default: 0.8)")
    
    # budget list
    budget_subparsers.add_parser("list", help="List budgets")
    
    # budget delete
    budget_delete = budget_subparsers.add_parser("delete", help="Delete budget")
    budget_delete.add_argument("budget_id", type=int, help="Budget ID to delete")
    
    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor session logs in real-time")
    monitor_parser.add_argument("path", help="Path to session logs directory")
    monitor_parser.add_argument("--db-path", help="Database path")
    monitor_parser.add_argument("--interval", type=int, default=10, 
                               help="Polling interval in seconds (default: 10)")
    monitor_parser.add_argument("--watch", action="store_true", 
                               help="Watch for file changes (inotify)")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export usage data")
    export_parser.add_argument("--db-path", help="Database path")
    export_parser.add_argument("--format", choices=["csv", "json"], default="csv", 
                              help="Export format")
    export_parser.add_argument("--output", "-o", help="Output file path")
    export_parser.add_argument("--period", choices=["day", "week", "month", "all"], default="all", 
                              help="Time period to export")
    
    # providers command
    providers_parser = subparsers.add_parser("providers", help="List providers and models")
    providers_parser.add_argument("--db-path", help="Database path")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "init":
            cmd_init(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "parse":
            cmd_parse(args)
        elif args.command == "summary":
            cmd_summary(args)
        elif args.command == "budget":
            cmd_budget(args)
        elif args.command == "monitor":
            cmd_monitor(args)
        elif args.command == "export":
            cmd_export(args)
        elif args.command == "providers":
            cmd_providers(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_init(args):
    """Initialize database command"""
    db = Database(args.db_path)
    db.initialize()
    print("✅ Database initialized successfully")

def cmd_status(args):
    """Show database status command"""
    db = Database(args.db_path)
    db.connect()
    
    # Get table info
    tables = db.get_table_info()
    
    print("📊 Database Status")
    print("=" * 50)
    print(f"Database path: {db.db_path}")
    print(f"Total tables: {len(tables)}")
    print()
    
    for table in tables:
        print(f"{table['name']:20} {table['row_count']:>10} rows")
    
    # Get total usage stats
    db.cursor.execute("""
    SELECT COUNT(*) as entries, 
           SUM(total_cost) as total_cost,
           SUM(input_tokens + output_tokens) as total_tokens
    FROM usage_entries
    """)
    
    stats = db.cursor.fetchone()
    if stats[0] > 0:
        print()
        print("📈 Usage Statistics")
        print(f"Total entries: {stats[0]}")
        print(f"Total tokens: {stats[2]:,}")
        print(f"Total cost: ${stats[1]:.4f}")
    
    db.close()

def cmd_parse(args):
    """Parse session logs command"""
    from .parser import SessionParser
    
    print(f"🔍 Parsing session logs from: {args.path}")
    
    # Initialize parser
    parser = SessionParser(args.db_path)
    
    # Parse directory
    files_processed, entries_processed = parser.parse_directory(
        args.path, 
        recursive=args.recursive
    )
    
    print(f"\n✅ Parsing complete")
    print(f"   Files processed: {files_processed}")
    print(f"   Usage entries saved: {entries_processed}")
    
    if entries_processed == 0:
        print("\nℹ️  No usage data found. Make sure:")
        print("   - Session files exist at the specified path")
        print("   - Files are in JSONL format (.jsonl extension)")
        print("   - Files contain usage data from AI API calls")

def cmd_summary(args):
    """Show usage summary command"""
    db = Database(args.db_path)
    db.connect()
    
    # Build WHERE clause based on period
    if args.period == "day":
        where_clause = "WHERE date(timestamp) = date('now')"
    elif args.period == "week":
        where_clause = "WHERE timestamp >= date('now', '-7 days')"
    elif args.period == "month":
        where_clause = "WHERE timestamp >= date('now', '-30 days')"
    else:
        where_clause = ""
    
    # Add provider filter if specified
    if args.provider:
        if where_clause:
            where_clause += f" AND p.name = '{args.provider}'"
        else:
            where_clause = f"WHERE p.name = '{args.provider}'"
    
    query = f"""
    SELECT 
        p.name as provider,
        m.name as model,
        COUNT(*) as requests,
        SUM(u.input_tokens) as input_tokens,
        SUM(u.output_tokens) as output_tokens,
        SUM(u.total_cost) as total_cost
    FROM usage_entries u
    JOIN models m ON u.model_id = m.id
    JOIN providers p ON m.provider_id = p.id
    {where_clause}
    GROUP BY p.name, m.name
    ORDER BY total_cost DESC
    """
    
    db.cursor.execute(query)
    results = db.cursor.fetchall()
    
    print(f"📊 Usage Summary ({args.period})")
    print("=" * 80)
    print(f"{'Provider':15} {'Model':25} {'Requests':>10} {'Input':>10} {'Output':>10} {'Cost':>10}")
    print("-" * 80)
    
    total_requests = 0
    total_input = 0
    total_output = 0
    total_cost = 0.0
    
    for row in results:
        provider, model, requests, input_tokens, output_tokens, cost = row
        print(f"{provider:15} {model:25} {requests:>10} {input_tokens:>10,} {output_tokens:>10,} ${cost:>9.4f}")
        
        total_requests += requests
        total_input += input_tokens
        total_output += output_tokens
        total_cost += cost
    
    print("-" * 80)
    print(f"{'TOTAL':41} {total_requests:>10} {total_input:>10,} {total_output:>10,} ${total_cost:>9.4f}")
    
    if total_requests == 0:
        print("\nℹ️  No usage data found for the specified period")
    
    db.close()

def cmd_budget(args):
    """Manage budgets command"""
    db = Database(args.db_path)
    db.connect()
    
    if args.budget_command == "set":
        # Set budget
        provider_id = None
        model_id = None
        
        if args.provider:
            db.cursor.execute("SELECT id FROM providers WHERE name = ?", (args.provider,))
            result = db.cursor.fetchone()
            if result:
                provider_id = result[0]
            else:
                print(f"Error: Provider '{args.provider}' not found")
                db.close()
                return
        
        if args.model:
            db.cursor.execute("SELECT id FROM models WHERE model_id = ?", (args.model,))
            result = db.cursor.fetchone()
            if result:
                model_id = result[0]
            else:
                print(f"Error: Model '{args.model}' not found")
                db.close()
                return
        
        # Check if budget already exists
        db.cursor.execute("""
        SELECT id FROM budgets 
        WHERE provider_id IS ? AND model_id IS ? AND period = ?
        """, (provider_id, model_id, args.period))
        
        existing = db.cursor.fetchone()
        
        if existing:
            # Update existing budget
            db.cursor.execute("""
            UPDATE budgets 
            SET amount = ?, alert_threshold = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (args.amount, args.threshold, existing[0]))
            print(f"✅ Updated budget ID {existing[0]}")
        else:
            # Insert new budget
            db.cursor.execute("""
            INSERT INTO budgets (provider_id, model_id, period, amount, alert_threshold)
            VALUES (?, ?, ?, ?, ?)
            """, (provider_id, model_id, args.period, args.amount, args.threshold))
            print(f"✅ Created new budget ID {db.cursor.lastrowid}")
        
        db.conn.commit()
        
    elif args.budget_command == "list":
        # List budgets
        query = """
        SELECT 
            b.id,
            COALESCE(p.name, 'Global') as provider,
            COALESCE(m.name, 'All models') as model,
            b.period,
            b.amount,
            b.alert_threshold,
            b.enabled
        FROM budgets b
        LEFT JOIN providers p ON b.provider_id = p.id
        LEFT JOIN models m ON b.model_id = m.id
        ORDER BY provider, model, b.period
        """
        
        db.cursor.execute(query)
        budgets = db.cursor.fetchall()
        
        print("💰 Budgets")
        print("=" * 80)
        print(f"{'ID':>4} {'Provider':15} {'Model':20} {'Period':10} {'Amount':>10} {'Threshold':>10} {'Status':>10}")
        print("-" * 80)
        
        for budget in budgets:
            budget_id, provider, model, period, amount, threshold, enabled = budget
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"{budget_id:>4} {provider:15} {model:20} {period:10} ${amount:>9.2f} {threshold:>9.1%} {status:>10}")
        
        if not budgets:
            print("No budgets configured")
    
    elif args.budget_command == "delete":
        # Delete budget
        db.cursor.execute("DELETE FROM budgets WHERE id = ?", (args.budget_id,))
        db.conn.commit()
        print(f"✅ Deleted budget ID {args.budget_id}")
    
    else:
        print("Error: Budget command required (set, list, delete)")
    
    db.close()

def cmd_monitor(args):
    """Monitor session logs command"""
    import time
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from .parser import SessionParser
    
    print(f"👁️  Monitoring session logs at: {args.path}")
    print(f"   Polling interval: {args.interval} seconds")
    print(f"   Watch mode: {'Enabled' if args.watch else 'Disabled'}")
    
    if args.watch:
        print("\n⚠️  Watch mode requires 'watchdog' package")
        print("   Install with: pip install watchdog")
        print("   Falling back to polling mode")
    
    # Initialize parser
    parser = SessionParser(args.db_path)
    
    print("\nStarting monitoring... (Press Ctrl+C to stop)")
    print("-" * 50)
    
    try:
        last_check = time.time()
        total_entries = 0
        
        while True:
            current_time = time.time()
            
            # Check if it's time to poll
            if current_time - last_check >= args.interval:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking for new session files...")
                
                files_processed, entries_processed = parser.parse_directory(
                    args.path, 
                    recursive=True
                )
                
                if entries_processed > 0:
                    total_entries += entries_processed
                    print(f"   Found {entries_processed} new usage entries")
                    print(f"   Total entries processed: {total_entries}")
                
                last_check = current_time
            
            # Sleep for a short time to avoid busy waiting
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Monitoring stopped")
        print(f"   Total entries processed during session: {total_entries}")
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure required packages are installed:")
        print("   pip install watchdog")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def cmd_export(args):
    """Export usage data command"""
    import csv
    import json
    
    db = Database(args.db_path)
    db.connect()
    
    # Build WHERE clause based on period
    if args.period == "day":
        where_clause = "WHERE date(timestamp) = date('now')"
    elif args.period == "week":
        where_clause = "WHERE timestamp >= date('now', '-7 days')"
    elif args.period == "month":
        where_clause = "WHERE timestamp >= date('now', '-30 days')"
    else:
        where_clause = ""
    
    # Query usage data
    query = f"""
    SELECT 
        u.timestamp,
        p.name as provider,
        m.name as model,
        u.input_tokens,
        u.output_tokens,
        u.total_cost,
        u.metadata_json
    FROM usage_entries u
    JOIN models m ON u.model_id = m.id
    JOIN providers p ON m.provider_id = p.id
    {where_clause}
    ORDER BY u.timestamp
    """
    
    db.cursor.execute(query)
    rows = db.cursor.fetchall()
    
    if not rows:
        print("No usage data found to export")
        db.close()
        return
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"ai_usage_export_{timestamp}.{args.format}"
    
    print(f"Exporting {len(rows)} usage entries to {output_file} ({args.format} format)")
    
    try:
        if args.format == "csv":
            # Export as CSV
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['timestamp', 'provider', 'model', 'input_tokens', 
                               'output_tokens', 'total_cost', 'metadata'])
                
                # Write data
                for row in rows:
                    writer.writerow(row)
            
            print(f"✅ CSV export complete: {output_file}")
            
        elif args.format == "json":
            # Export as JSON
            data = []
            for row in rows:
                entry = {
                    'timestamp': row[0],
                    'provider': row[1],
                    'model': row[2],
                    'input_tokens': row[3],
                    'output_tokens': row[4],
                    'total_cost': row[5],
                    'metadata': json.loads(row[6]) if row[6] else {}
                }
                data.append(entry)
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"✅ JSON export complete: {output_file}")
    
    except Exception as e:
        print(f"❌ Export failed: {e}")
    
    db.close()

def cmd_providers(args):
    """List providers and models command"""
    db = Database(args.db_path)
    db.connect()
    
    query = """
    SELECT 
        p.name as provider,
        m.model_id,
        m.name as model_name,
        m.input_cost,
        m.output_cost,
        COUNT(u.id) as usage_count
    FROM providers p
    JOIN models m ON p.id = m.provider_id
    LEFT JOIN usage_entries u ON m.id = u.model_id
    GROUP BY p.name, m.model_id, m.name, m.input_cost, m.output_cost
    ORDER BY p.name, m.name
    """
    
    db.cursor.execute(query)
    providers = db.cursor.fetchall()
    
    print("🤖 Providers & Models")
    print("=" * 80)
    
    current_provider = None
    for row in providers:
        provider, model_id, model_name, input_cost, output_cost, usage_count = row
        
        if provider != current_provider:
            print(f"\n{provider.upper()}")
            print("-" * 40)
            current_provider = provider
        
        cost_str = f"${input_cost}/in, ${output_cost}/out" if input_cost and output_cost else "No pricing"
        usage_str = f"({usage_count} uses)" if usage_count > 0 else ""
        print(f"  {model_name:25} {model_id:30} {cost_str:25} {usage_str}")
    
    if not providers:
        print("No providers configured")
    
    db.close()

if __name__ == "__main__":
    main()