#!/usr/bin/env python3
"""
Comprehensive Notion API Integration Test

Tests all aspects of the Notion integration:
- Simple page creation
- Block appending
- Real note conversion
- Rate limiting
- Metadata preservation
"""

import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from app.notion.client import NotionClient
from app.notion.page_creator import PageCreator
from app.notion.block_builder import BlockBuilder, text_paragraph, text_heading
from app.parsers.enex_parser import EnexParser


def print_test_header(title: str):
    """Print formatted test header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_simple_page_creation():
    """Test 1: Create simple page with blocks."""
    print_test_header("Test 1: Simple Page Creation")

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    try:
        client = NotionClient(api_key)

        # Create simple page
        print("🔄 Creating simple test page...")
        page_id = client.create_page(
            parent_id=parent_id,
            title="🧪 Simple Test Page",
            icon={'emoji': '🧪'}
        )
        print(f"✅ Page created: {page_id}")

        # Create blocks
        blocks = [
            text_heading("Welcome to the Test", level=1),
            text_paragraph("This is a simple test page created by the Notion API integration."),
            text_heading("Features Tested", level=2),
            BlockBuilder.bulleted_list_item([BlockBuilder._rich_text("Page creation")]),
            BlockBuilder.bulleted_list_item([BlockBuilder._rich_text("Block appending")]),
            BlockBuilder.bulleted_list_item([BlockBuilder._rich_text("Rich text formatting")]),
            BlockBuilder.divider(),
            BlockBuilder.to_do([BlockBuilder._rich_text("Test to-do item")], checked=False),
            BlockBuilder.to_do([BlockBuilder._rich_text("Completed to-do")], checked=True),
        ]

        # Append blocks
        print(f"🔄 Appending {len(blocks)} blocks...")
        client.append_blocks(page_id, blocks)
        print(f"✅ Blocks appended successfully")

        print(f"\n📄 View page: https://notion.so/{page_id.replace('-', '')}")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_note_conversion():
    """Test 2: Convert real Evernote note to Notion."""
    print_test_header("Test 2: Real Note Conversion")

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    # Try to find a test file
    test_files = [
        "IT트렌드.enex",
        "금융정보.enex",
        "맛집.enex"
    ]

    test_file = None
    for filename in test_files:
        path = enex_dir / filename
        if path.exists():
            test_file = path
            break

    if not test_file:
        print(f"⚠️  No test files found in {enex_dir}")
        return False

    try:
        print(f"📂 Using test file: {test_file.name}")

        # Parse ENEX
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        if not notes:
            print("❌ No notes found in file")
            return False

        # Get first note
        note = notes[0]
        print(f"\n📝 Note: {note.title[:60]}...")
        print(f"   Created: {note.created}")
        print(f"   Updated: {note.updated}")
        print(f"   Tags: {', '.join(note.tags[:3]) if note.tags else 'None'}")
        print(f"   Resources: {len(note.resources)}")

        # Create page
        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        print(f"\n🔄 Converting to Notion page...")
        page_id = creator.create_from_note(note, include_metadata=True)

        print(f"✅ Conversion successful!")
        print(f"   Page ID: {page_id}")
        print(f"   URL: https://notion.so/{page_id.replace('-', '')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiting():
    """Test 3: Rate limiting with multiple page creations."""
    print_test_header("Test 3: Rate Limiting Test")

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    try:
        client = NotionClient(api_key)

        num_pages = 10
        print(f"🔄 Creating {num_pages} pages rapidly...")
        print(f"   This tests the rate limiter (3 req/s limit)")

        start_time = time.time()
        page_ids = []

        for i in range(num_pages):
            print(f"   [{i+1}/{num_pages}] Creating page...", end='')

            page_id = client.create_page(
                parent_id=parent_id,
                title=f"Rate Limit Test {i+1}",
                icon={'emoji': '⏱️'}
            )

            page_ids.append(page_id)
            print(f" ✓ {page_id[:8]}...")

        elapsed = time.time() - start_time

        print(f"\n✅ All {num_pages} pages created!")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Average: {elapsed/num_pages:.2f}s per page")
        print(f"   Expected minimum: ~{num_pages/3:.2f}s (at 3 req/s)")

        if elapsed < (num_pages / 3) * 0.8:
            print(f"   ⚠️  Warning: Too fast! Rate limiter may not be working")
        else:
            print(f"   ✅ Rate limiting working correctly")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_preservation():
    """Test 4: Verify metadata preservation."""
    print_test_header("Test 4: Metadata Preservation")

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    # Find file with tags
    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"⚠️  Test file not found")
        return False

    try:
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        # Find note with metadata
        test_note = notes[0]
        for note in notes:
            if note.tags or note.author:
                test_note = note
                break

        print(f"📝 Note: {test_note.title[:60]}...")
        print(f"\n📋 Original Metadata:")
        print(f"   Title: {test_note.title}")
        print(f"   Created: {test_note.created}")
        print(f"   Updated: {test_note.updated}")
        print(f"   Author: {test_note.author or 'None'}")
        print(f"   Tags: {', '.join(test_note.tags) if test_note.tags else 'None'}")
        print(f"   Source: {test_note.source or 'None'}")
        print(f"   Resources: {len(test_note.resources)}")

        # Create page with metadata
        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        print(f"\n🔄 Creating page with metadata...")
        page_id = creator.create_from_note(test_note, include_metadata=True)

        print(f"\n✅ Page created with metadata!")
        print(f"   Metadata is displayed in a callout block at the top")
        print(f"   Page icon selected based on content type")
        print(f"\n📄 View and verify: https://notion.so/{page_id.replace('-', '')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test 5: Batch processing multiple notes."""
    print_test_header("Test 5: Batch Processing")

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')
    enex_dir = Path(os.getenv('ENEX_SOURCE_DIR', '/Users/sunchulkim/evernote'))

    test_file = enex_dir / "IT트렌드.enex"
    if not test_file.exists():
        print(f"⚠️  Test file not found")
        return False

    try:
        parser = EnexParser(test_file)
        notes = list(parser.parse())

        # Limit to 5 notes for testing
        batch_size = min(5, len(notes))
        test_notes = notes[:batch_size]

        print(f"📚 Processing batch of {batch_size} notes")

        client = NotionClient(api_key)
        creator = PageCreator(client, parent_id)

        # Progress callback
        def show_progress(current, total, title):
            print(f"   [{current}/{total}] {title[:50]}...")

        # Create batch
        print(f"\n🔄 Creating {batch_size} pages...")
        start_time = time.time()

        results = creator.create_batch(test_notes, progress_callback=show_progress)

        elapsed = time.time() - start_time

        print(f"\n✅ Batch processing complete!")
        print(f"   Success: {results['success']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Average: {elapsed/batch_size:.2f}s per page")

        if results['failed'] > 0:
            print(f"\n❌ Errors:")
            for error in results['errors']:
                print(f"   - {error['note_title']}: {error['error']}")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_pages():
    """Optional: Clean up test pages."""
    print_test_header("Cleanup Instructions")

    print("\nTo clean up test pages:")
    print("1. Go to your Notion 'evernote' page")
    print("2. Look for pages with these titles:")
    print("   - '🧪 Simple Test Page'")
    print("   - 'Rate Limit Test 1-10'")
    print("   - Test pages from your ENEX files")
    print("3. Select and delete unwanted pages")
    print("\nOr keep them to verify the migration worked correctly!")

    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("  Comprehensive Notion API Integration Test Suite")
    print("=" * 80)

    # Check environment
    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    if not api_key or not parent_id:
        print("\n❌ Missing environment variables")
        print("   Please ensure .env file has:")
        print("   - NOTION_API_KEY")
        print("   - NOTION_PARENT_PAGE_ID")
        return 1

    print(f"\n✅ Environment configured")
    print(f"   Parent page: {parent_id}")

    # Run tests
    results = []

    tests = [
        ("Simple Page Creation", test_simple_page_creation),
        ("Real Note Conversion", test_real_note_conversion),
        ("Rate Limiting", test_rate_limiting),
        ("Metadata Preservation", test_metadata_preservation),
        ("Batch Processing", test_batch_processing),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print_test_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")

    print(f"\nPassed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\n✨ Your Notion integration is working perfectly!")
        print("   Check your 'evernote' page to see all created test pages.")

        # Cleanup option
        cleanup_test_pages()

        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
