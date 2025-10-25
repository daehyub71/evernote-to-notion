#!/usr/bin/env python3
"""
Test script for ENEX parser.

Usage:
    python scripts/test_enex_parse.py --file "맛집.enex"
    python scripts/test_enex_parse.py --all
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.enex_parser import EnexParser


def test_single_file(file_path: str, verbose: bool = False):
    """Test parsing a single ENEX file."""
    print(f"\n{'='*80}")
    print(f"Testing: {Path(file_path).name}")
    print('='*80)

    try:
        parser = EnexParser(file_path)
        notes = list(parser.parse())

        print(f"\n✅ Successfully parsed {len(notes)} notes\n")

        # Show summary
        total_resources = sum(len(note.resources) for note in notes)
        print(f"Summary:")
        print(f"  Total notes: {len(notes)}")
        print(f"  Total resources: {total_resources}")
        print(f"  Tags found: {len(set(tag for note in notes for tag in note.tags))}")

        # Show first few notes
        print(f"\n{'─'*80}")
        print("Sample Notes:")
        print('─'*80)

        for i, note in enumerate(notes[:3], 1):
            print(f"\nNote {i}:")
            print(f"  Title: {note.title}")
            print(f"  Created: {note.created}")
            print(f"  Updated: {note.updated}")
            print(f"  Tags: {note.tags}")
            print(f"  Author: {note.author}")
            print(f"  Source: {note.source}")
            print(f"  Content length: {len(note.content)} chars")
            print(f"  Resources: {len(note.resources)}")

            if verbose and note.resources:
                print(f"\n  Resource details:")
                for j, res in enumerate(note.resources, 1):
                    print(f"    {j}. {res.mime}")
                    print(f"       Hash: {res.hash}")
                    print(f"       Filename: {res.filename}")
                    if res.width and res.height:
                        print(f"       Size: {res.width}x{res.height}")
                    print(f"       Data: {len(res.data)} bytes")

        if len(notes) > 3:
            print(f"\n  ... and {len(notes) - 3} more notes")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def test_all_files(source_dir: str, verbose: bool = False):
    """Test parsing all ENEX files in directory."""
    source_path = Path(source_dir)
    enex_files = sorted(source_path.glob('*.enex'))

    if not enex_files:
        print(f"No ENEX files found in {source_dir}")
        return

    print(f"\n{'='*80}")
    print(f"Testing all ENEX files in: {source_dir}")
    print(f"Found {len(enex_files)} files")
    print('='*80)

    results = []
    total_notes = 0
    total_resources = 0

    for enex_file in enex_files:
        try:
            parser = EnexParser(str(enex_file))
            notes = list(parser.parse())

            note_count = len(notes)
            resource_count = sum(len(note.resources) for note in notes)

            total_notes += note_count
            total_resources += resource_count

            results.append({
                'file': enex_file.name,
                'notes': note_count,
                'resources': resource_count,
                'success': True
            })

        except Exception as e:
            results.append({
                'file': enex_file.name,
                'notes': 0,
                'resources': 0,
                'success': False,
                'error': str(e)
            })

    # Print results table
    print(f"\n{'─'*80}")
    print(f"{'File':<40} | {'Notes':>6} | {'Resources':>10} | {'Status':>10}")
    print('─'*80)

    for result in results:
        status = '✅ OK' if result['success'] else '❌ FAIL'
        print(f"{result['file']:<40} | {result['notes']:>6} | {result['resources']:>10} | {status:>10}")

        if not result['success'] and verbose:
            print(f"  Error: {result.get('error', 'Unknown')}")

    # Print summary
    print('='*80)
    print(f"\nSummary:")
    print(f"  Total files: {len(enex_files)}")
    print(f"  Successful: {sum(1 for r in results if r['success'])}")
    print(f"  Failed: {sum(1 for r in results if not r['success'])}")
    print(f"  Total notes: {total_notes}")
    print(f"  Total resources: {total_resources}")


def main():
    parser = argparse.ArgumentParser(description='Test ENEX parser')
    parser.add_argument('--file', help='Test a single ENEX file')
    parser.add_argument('--all', action='store_true', help='Test all ENEX files')
    parser.add_argument('--dir', default='/Users/sunchulkim/evernote',
                       help='Directory containing ENEX files')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output')

    args = parser.parse_args()

    if args.file:
        # Test single file
        file_path = Path(args.dir) / args.file if not Path(args.file).is_absolute() else Path(args.file)
        success = test_single_file(str(file_path), verbose=args.verbose)
        sys.exit(0 if success else 1)

    elif args.all:
        # Test all files
        test_all_files(args.dir, verbose=args.verbose)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
