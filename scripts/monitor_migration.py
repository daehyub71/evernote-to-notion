#!/usr/bin/env python3
"""
Real-time migration progress monitor.

Displays current migration statistics from checkpoint file.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import sys

def load_checkpoint():
    """Load current checkpoint data."""
    checkpoint_file = Path('data/checkpoint/migration_checkpoint.json')
    if not checkpoint_file.exists():
        return None

    with open(checkpoint_file) as f:
        return json.load(f)

def display_progress(data, enex_count=23, expected_notes=1373, expected_resources=1574):
    """Display migration progress."""
    if not data:
        print("No checkpoint found - migration not started")
        return

    stats = data.get('statistics', {})
    metadata = data.get('metadata', {})

    files_processed = stats.get('total_files_processed', 0)
    notes_processed = stats.get('total_notes_processed', 0)
    notes_failed = stats.get('total_notes_failed', 0)
    resources_uploaded = stats.get('total_resources_uploaded', 0)

    files_pct = (files_processed / enex_count * 100) if enex_count > 0 else 0
    notes_pct = (notes_processed / expected_notes * 100) if expected_notes > 0 else 0
    resources_pct = (resources_uploaded / expected_resources * 100) if expected_resources > 0 else 0

    notes_success_rate = ((notes_processed - notes_failed) / notes_processed * 100) if notes_processed > 0 else 0

    print('='*80)
    print('  Migration Progress Monitor')
    print('='*80)
    print()
    print(f'📊 Files:     {files_processed:4}/{enex_count:4} ({files_pct:5.1f}%)')
    print(f'📝 Notes:     {notes_processed:4}/{expected_notes:4} ({notes_pct:5.1f}%) - {notes_failed} failed')
    print(f'📦 Resources: {resources_uploaded:4}/{expected_resources:4} ({resources_pct:5.1f}%)')
    print(f'✅ Success:   {notes_success_rate:5.1f}%')
    print()
    print(f'⏱️  Last updated: {metadata.get("last_updated", "unknown")}')
    print()

    # Completed files list
    completed_files = data.get('completed_files', [])
    if completed_files:
        print(f'📁 Completed files ({len(completed_files)}):')
        for i, filepath in enumerate(completed_files[-5:], 1):  # Show last 5
            filename = Path(filepath).name
            print(f'   {i}. {filename}')
        if len(completed_files) > 5:
            print(f'   ... and {len(completed_files) - 5} more')

    print('='*80)

def monitor_loop(interval=10):
    """Monitor migration progress in a loop."""
    try:
        while True:
            # Clear screen (optional)
            # print('\033[2J\033[H')  # ANSI clear screen

            data = load_checkpoint()
            display_progress(data)

            time.sleep(interval)
    except KeyboardInterrupt:
        print('\n\nMonitoring stopped.')
        sys.exit(0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Monitor migration progress')
    parser.add_argument('--interval', '-i', type=int, default=10, help='Update interval in seconds')
    parser.add_argument('--once', action='store_true', help='Show progress once and exit')
    args = parser.parse_args()

    if args.once:
        data = load_checkpoint()
        display_progress(data)
    else:
        monitor_loop(args.interval)
