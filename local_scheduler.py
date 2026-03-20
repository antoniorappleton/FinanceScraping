import time
import subprocess
import sys
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

def start_scheduler(interval_hours=4):
    """
    Background scheduler loop.
    Runs a fast sync immediately, then every X hours.
    """
    print("="*60)
    print("        LOCAL SCRAPER SCHEDULER (BYPASS GITHUB BILLING)")
    print("="*60)
    print(f"Interval: Every {interval_hours} hours")
    print("Press Ctrl+C to stop the scheduler.")
    
    try:
        last_full_sync_date = None
        while True:
            now = datetime.now()
            # If it's Sunday and we haven't done a full sync today
            if now.weekday() == 6 and last_full_sync_date != now.date():
                run_scraper(mode="full")
                last_full_sync_date = now.date()
                # Also do a fast sync for price updates
                run_scraper(mode="fast")
            else:
                run_scraper(mode="fast")
            
            next_run = datetime.now() + timedelta(hours=interval_hours)
            print(f"\nSleeping for {interval_hours} hours...")
            print(f"Next sync scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        print("\nScheduler stopped by user. Goodbye!")

if __name__ == "__main__":
    # If passed as an argument, we could handle different intervals
    start_scheduler(interval_hours=4)
