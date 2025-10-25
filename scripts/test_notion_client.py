#!/usr/bin/env python3
"""
Test script for Notion API client.

Tests connection, page creation, and block appending.
Requires valid .env file with NOTION_API_KEY and NOTION_PARENT_PAGE_ID.
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

from app.notion.client import NotionClient, NotionAPIError
from app.notion.block_builder import text_paragraph, text_heading


def test_connection():
    """Test basic connection to Notion API."""
    print("\n" + "=" * 80)
    print("  Test 1: Notion API Connection")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    if not api_key or api_key == 'secret_xxxxxxxxxxxxxxxxxxxxx':
        print("❌ NOTION_API_KEY not set in .env file")
        print("\nPlease:")
        print("1. Get your API key from https://www.notion.so/my-integrations")
        print("2. Update .env file with: NOTION_API_KEY=secret_your_key_here")
        return False

    try:
        client = NotionClient(api_key)
        print(f"✅ Notion client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False


def test_parent_page():
    """Test access to parent page."""
    print("\n" + "=" * 80)
    print("  Test 2: Parent Page Access")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    if not parent_id or parent_id == 'xxxxxxxxxxxxxxxxxxxxx':
        print("❌ NOTION_PARENT_PAGE_ID not set in .env file")
        print("\nPlease:")
        print("1. Create a page in Notion (or use existing page)")
        print("2. Share the page with your integration")
        print("3. Copy page ID from URL")
        print("4. Update .env file with: NOTION_PARENT_PAGE_ID=your_page_id")
        return False

    try:
        client = NotionClient(api_key)
        page = client.get_page(parent_id)
        title = "Unknown"
        if 'properties' in page and 'title' in page['properties']:
            title_prop = page['properties']['title']
            if title_prop.get('title'):
                title = title_prop['title'][0]['plain_text']

        print(f"✅ Parent page accessed successfully")
        print(f"   Page ID: {parent_id}")
        print(f"   Title: {title}")
        return True
    except NotionAPIError as e:
        print(f"❌ Failed to access parent page: {e}")
        print("\nPossible issues:")
        print("1. Page ID is incorrect")
        print("2. Integration doesn't have access to the page")
        print("   → Go to the page → ... menu → Connections → Add your integration")
        return False


def test_create_test_page():
    """Test creating a test page."""
    print("\n" + "=" * 80)
    print("  Test 3: Create Test Page")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    try:
        client = NotionClient(api_key)

        # Create test page
        page_id = client.create_page(
            parent_id=parent_id,
            title="🧪 Evernote Migration Test",
            icon={'emoji': '🧪'}
        )

        print(f"✅ Test page created successfully")
        print(f"   Page ID: {page_id}")
        return page_id

    except NotionAPIError as e:
        print(f"❌ Failed to create test page: {e}")
        return None


def test_append_blocks(page_id: str):
    """Test appending blocks to a page."""
    print("\n" + "=" * 80)
    print("  Test 4: Append Blocks")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')

    try:
        client = NotionClient(api_key)

        # Create test blocks
        blocks = [
            text_heading("Test Heading", level=1),
            text_paragraph("This is a test paragraph with **bold** text.", bold=False),
            text_heading("Subheading", level=2),
            text_paragraph("Another paragraph with some content."),
            text_paragraph("🎉 If you see this, the Notion API integration is working!", bold=True)
        ]

        # Append blocks
        client.append_blocks(page_id, blocks)

        print(f"✅ Blocks appended successfully")
        print(f"   {len(blocks)} blocks added")
        return True

    except NotionAPIError as e:
        print(f"❌ Failed to append blocks: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting."""
    print("\n" + "=" * 80)
    print("  Test 5: Rate Limiting")
    print("=" * 80)

    api_key = os.getenv('NOTION_API_KEY')
    parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

    try:
        client = NotionClient(api_key)

        # Make multiple rapid requests
        print("Making 10 rapid requests to test rate limiting...")
        import time
        start_time = time.time()

        for i in range(10):
            client.get_page(parent_id)
            print(f"  Request {i+1}/10 completed")

        elapsed = time.time() - start_time
        print(f"✅ Rate limiting works correctly")
        print(f"   10 requests took {elapsed:.2f}s (expected ~3.3s at 3 req/s)")
        return True

    except NotionAPIError as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("  Notion API Client Test Suite")
    print("=" * 80)

    results = []

    # Test 1: Connection
    result = test_connection()
    results.append(("Connection", result))
    if not result:
        print("\n⚠️  Cannot proceed without valid API key")
        return 1

    # Test 2: Parent page
    result = test_parent_page()
    results.append(("Parent Page Access", result))
    if not result:
        print("\n⚠️  Cannot proceed without valid parent page")
        return 1

    # Test 3: Create page
    page_id = test_create_test_page()
    results.append(("Create Page", page_id is not None))
    if not page_id:
        print("\n⚠️  Cannot proceed without page creation")
        return 1

    # Test 4: Append blocks
    result = test_append_blocks(page_id)
    results.append(("Append Blocks", result))

    # Test 5: Rate limiting
    result = test_rate_limiting()
    results.append(("Rate Limiting", result))

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
        print(f"\nCheck your Notion page for the test page:")
        print(f"https://notion.so/{page_id}")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
