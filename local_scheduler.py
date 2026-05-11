import time
import subprocess
import sys
import argparse
from datetime import datetime, timedelta

def run_scraper(mode="fast"):
    """Runs the scraper script in a subprocess."""
    print(f"\n[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] Triggering {mode.upper()} sync...")
    try:
        # We use sys.executable to ensure we use the same Python environment
        result = subprocess.run([sys.executable, "cron_scraper.py", "--mode", mode], capture_output=False)
        if result.returncode == 0:
            print(f"[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] {mode.upper()} sync completed successfully.")
        else:
            print(f"[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] Scraper exited with error code {result.returncode}.")
    except Exception as e:
        print(f"[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] Error running scraper: {e}")

def parse_interval(arg):
    """Parse interval like '10m', '4h', or '240' to minutes."""
    if arg.endswith('h'):
        return int(arg[:-1]) * 60
    elif arg.endswith('m'):
        return int(arg[:-1])
    else:
        return int(arg)

def start_scheduler(interval_minutes=240):  # Default 4 hours
    """
    Background scheduler loop.
    Runs fast sync every interval_minutes, full on Sundays.
    """
    print("="*60)
    print("        LOCAL SCRAPER SCHEDULER (BYPASS GITHUB BILLING)")
    print("="*60)
    print(f"Interval: Every {interval_minutes//60 if interval_minutes >=60 else interval_minutes}m")
    print("Press Ctrl+C to stop.")
    
    try:
        last_full_sync_time = None
        last_holdings_sync_day = None  # To track which day we ran the holdings sync
        
        while True:
            now = datetime.now()
            
            # 1. Check if it's the WEEKEND (Saturday=5, Sunday=6) for Holdings Sync
            # We run it only once per weekend day
            if now.weekday() >= 5 and last_holdings_sync_day != now.date():
                print(f"\n[ {now.strftime('%Y-%m-%d %H:%M:%S')} ] Weekend detected! Running FULL HOLDINGS sync for all assets...")
                try:
                    # Run first for 'ativos' (priority)
                    subprocess.run([sys.executable, "scripts/sync_ativos_holdings.py"], capture_output=False)
                    # Then run for all 'acoesDividendos'
                    subprocess.run([sys.executable, "scripts/sync_all_holdings_weekend.py"], capture_output=False)
                    last_holdings_sync_day = now.date()
                except Exception as e:
                    print(f"Error running holdings sync: {e}")

            # 2. Normal sync logic
            # Run FULL sync if it's the first time OR if 20 hours have passed since last full
            should_run_full = (last_full_sync_time is None or 
                              (now - last_full_sync_time).total_seconds() > 20 * 3600)
            
            if should_run_full:
                run_scraper("full")
                last_full_sync_time = now
            else:
                run_scraper("fast")
            
            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            print(f"\nSleeping for {interval_minutes} min...")
            print(f"Next at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local scheduler for market scraper")
    parser.add_argument("--interval-minutes", "-i", type=str, default="240", help="Interval (e.g. '10m', '4h', 240)")
    args = parser.parse_args()
    min_interval = parse_interval(args.interval_minutes)
    start_scheduler(interval_minutes=min_interval)
