#!/usr/bin/env python3
"""
Test script for Page Creator.

Creates test pages from real ENEX notes.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from app.parsers.enex_parser import EnexParser
from app.notion.client import NotionClient
from app.notion.page_creator import PageCreator, PageCreationError


def test_single_note():
    """Test creating a single page from a real note."""
    print("\n" + "=" * 80)
    print("  Test 1: Create Page from Real Note")
    print("=" * 80)

    # Load environment
    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    # Find test file
    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse ENEX
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        if not notes:
            print("❌ No notes found in file")
            return False

        # Get first note
        note = notes[0]
        print(f"📝 Note: {note.title}")
        print(f"   Created: {note.created}")
        print(f"   Tags: {', '.join(note.tags) if note.tags else 'None'}")
        print(f"   Resources: {len(note.resources)}")

        # Create Notion client
        client = NotionClient(api_key)

        # Create page creator
        creator = PageCreator(client, parent_id)

        # Create page
        print(f"\n🔄 Creating Notion page...")
        page_id = creator.create_from_note(note, include_metadata=True)

        print(f"✅ Page created successfully!")
        print(f"   Page ID: {page_id}")
        print(f"   URL: https://notion.so/{page_id.replace('-', '')}")

        return True

    except PageCreationError as e:
        print(f"❌ Page creation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dry_run():
    """Test dry run (block conversion only)."""
    print("\n" + "=" * 80)
    print("  Test 2: Dry Run (Block Conversion Only)")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"❌ Test file not found")
        return False

    try:
        parser = EnexParser(test_file)
        notes = list(parser.parse())
        note = notes[1] if len(notes) > 1 else notes[0]  # Get second note

        print(f"📝 Note: {note.title}")

        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        # Dry run
        print(f"\n🔄 Dry run conversion...")
        result = creator.create_from_note(note, dry_run=True)

        print(f"✅ Dry run successful!")
        print(f"   Note would be converted (no page created)")

        return True

    except Exception as e:
        print(f"❌ Dry run failed: {e}")
        return False


def test_batch_creation():
    """Test creating multiple pages."""
    print("\n" + "=" * 80)
    print("  Test 3: Batch Page Creation")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"❌ Test file not found")
        return False

    try:
        # Parse notes
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        # Limit to first 3 notes for testing
        test_notes = notes[:3]
        print(f"📚 Testing with {len(test_notes)} notes")

        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        # Progress callback
        def progress(current, total, title):
            print(f"   [{current}/{total}] Processing: {title[:50]}...")

        # Create batch
        print(f"\n🔄 Creating {len(test_notes)} pages...")
        results = creator.create_batch(test_notes, progress_callback=progress)

        print(f"\n✅ Batch creation complete!")
        print(f"   Success: {results['success']}")
        print(f"   Failed: {results['failed']}")

        if results['failed'] > 0:
            print(f"\n❌ Errors:")
            for error in results['errors']:
                print(f"   - {error['note_title']}: {error['error']}")

        return results['failed'] == 0

    except Exception as e:
        print(f"❌ Batch creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_preservation():
    """Test metadata preservation."""
    print("\n" + "=" * 80)
    print("  Test 4: Metadata Preservation")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"❌ Test file not found")
        return False

    try:
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        # Find note with tags
        note_with_tags = None
        for note in notes:
            if note.tags:
                note_with_tags = note
                break

        if not note_with_tags:
            print("⚠️  No note with tags found, using first note")
            note_with_tags = notes[0]

        print(f"📝 Note: {note_with_tags.title}")
        print(f"   Created: {note_with_tags.created}")
        print(f"   Updated: {note_with_tags.updated}")
        print(f"   Tags: {', '.join(note_with_tags.tags) if note_with_tags.tags else 'None'}")
        print(f"   Author: {note_with_tags.author or 'None'}")
        print(f"   Source: {note_with_tags.source or 'None'}")

        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        # Create with metadata
        print(f"\n🔄 Creating page with metadata...")
        page_id = creator.create_from_note(note_with_tags, include_metadata=True)

        print(f"✅ Page created with metadata!")
        print(f"   Check the page to verify metadata callout block")
        print(f"   URL: https://notion.so/{page_id.replace('-', '')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("  Page Creator Test Suite")
    print("=" * 80)

    # Check environment
    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    if not api_key or not parent_id:
        print("❌ Missing environment variables")
        print("   Please ensure .env file has NOTION_API_KEY and NOTION_PARENT_PAGE_ID")
        return 1

    results = []

    # Test 1: Single note
    result = test_single_note()
    results.append(("Single Note Creation", result))

    # Test 2: Dry run
    result = test_dry_run()
    results.append(("Dry Run", result))

    # Test 3: Batch creation
    result = test_batch_creation()
    results.append(("Batch Creation", result))

    # Test 4: Metadata preservation
    result = test_metadata_preservation()
    results.append(("Metadata Preservation", result))

    # Summary
    print("\n" + "=" * 80)
    print("  Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nCheck your Notion 'evernote' page for the created test pages!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
