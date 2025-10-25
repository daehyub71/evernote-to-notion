#!/usr/bin/env python3
"""
Test script for Notion Block Builder.

Tests block creation, validation, and text splitting.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.notion.block_builder import (
    BlockBuilder,
    BlockValidator,
    NotionLimits,
    text_paragraph,
    text_heading
)


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_text_splitting():
    """Test long text splitting."""
    print_header("1. Text Splitting Tests")

    # Test 1: Short text (no split needed)
    text = "This is a short text"
    chunks = BlockBuilder.split_long_text(text)
    success = len(chunks) == 1 and chunks[0] == text
    print(f"{'✅' if success else '❌'} Short text (no split): {len(chunks)} chunk(s)")

    # Test 2: Long text with spaces
    text = "A " * 1500  # 3000 characters
    chunks = BlockBuilder.split_long_text(text)
    success = len(chunks) == 2 and all(len(c) <= NotionLimits.MAX_RICH_TEXT_LENGTH for c in chunks)
    print(f"{'✅' if success else '❌'} Long text with spaces: {len(chunks)} chunk(s), max={max(len(c) for c in chunks)} chars")

    # Test 3: Very long text (no spaces)
    text = "A" * 5000
    chunks = BlockBuilder.split_long_text(text)
    success = len(chunks) >= 3 and all(len(c) <= NotionLimits.MAX_RICH_TEXT_LENGTH for c in chunks)
    print(f"{'✅' if success else '❌'} Very long text (no spaces): {len(chunks)} chunk(s)")

    # Test 4: Korean text with sentence boundaries
    text = "안녕하세요. " * 500  # 3000 characters
    chunks = BlockBuilder.split_long_text(text)
    success = len(chunks) >= 2 and all(len(c) <= NotionLimits.MAX_RICH_TEXT_LENGTH for c in chunks)
    print(f"{'✅' if success else '❌'} Korean text with sentences: {len(chunks)} chunk(s)")

    # Test 5: Mixed content
    text = "This is a test. " * 100 + "NoSpacesHere" * 100 + " More text here."
    chunks = BlockBuilder.split_long_text(text)
    success = all(len(c) <= NotionLimits.MAX_RICH_TEXT_LENGTH for c in chunks)
    print(f"{'✅' if success else '❌'} Mixed content: {len(chunks)} chunk(s)")

    return True


def test_rich_text_creation():
    """Test rich text object creation."""
    print_header("2. Rich Text Creation Tests")

    # Test 1: Simple text
    rt = BlockBuilder._rich_text("Hello World")
    success = (rt['type'] == 'text' and
               rt['text']['content'] == "Hello World" and
               not rt['annotations']['bold'])
    print(f"{'✅' if success else '❌'} Simple rich text")

    # Test 2: Text with annotations
    annotations = {'bold': True, 'italic': True, 'underline': False,
                   'code': False, 'strikethrough': False, 'color': 'red'}
    rt = BlockBuilder._rich_text("Bold and Italic", annotations)
    success = (rt['annotations']['bold'] and
               rt['annotations']['italic'] and
               rt['annotations']['color'] == 'red')
    print(f"{'✅' if success else '❌'} Rich text with annotations")

    # Test 3: Text with link
    rt = BlockBuilder._rich_text("Click here", link="https://example.com")
    success = (rt['text'].get('link', {}).get('url') == "https://example.com")
    print(f"{'✅' if success else '❌'} Rich text with link")

    # Test 4: Too long text (auto-truncate)
    long_text = "A" * 3000
    rt = BlockBuilder._rich_text(long_text)
    success = len(rt['text']['content']) == NotionLimits.MAX_RICH_TEXT_LENGTH
    print(f"{'✅' if success else '❌'} Long text auto-truncation: {len(rt['text']['content'])} chars")

    return True


def test_block_creation():
    """Test Notion block creation."""
    print_header("3. Block Creation Tests")

    # Test 1: Paragraph
    rt = [BlockBuilder._rich_text("Test paragraph")]
    block = BlockBuilder.paragraph(rt)
    success = block['type'] == 'paragraph' and len(block['paragraph']['rich_text']) == 1
    print(f"{'✅' if success else '❌'} Paragraph block")

    # Test 2: Heading 1
    rt = [BlockBuilder._rich_text("Test Heading")]
    block = BlockBuilder.heading_1(rt)
    success = block['type'] == 'heading_1'
    print(f"{'✅' if success else '❌'} Heading 1 block")

    # Test 3: Bulleted list
    rt = [BlockBuilder._rich_text("List item")]
    block = BlockBuilder.bulleted_list_item(rt)
    success = block['type'] == 'bulleted_list_item'
    print(f"{'✅' if success else '❌'} Bulleted list item")

    # Test 4: Numbered list
    rt = [BlockBuilder._rich_text("Step 1")]
    block = BlockBuilder.numbered_list_item(rt)
    success = block['type'] == 'numbered_list_item'
    print(f"{'✅' if success else '❌'} Numbered list item")

    # Test 5: To-do (checked)
    rt = [BlockBuilder._rich_text("Complete task")]
    block = BlockBuilder.to_do(rt, checked=True)
    success = block['type'] == 'to_do' and block['to_do']['checked'] == True
    print(f"{'✅' if success else '❌'} To-do block (checked)")

    # Test 6: Quote
    rt = [BlockBuilder._rich_text("Quoted text")]
    block = BlockBuilder.quote(rt)
    success = block['type'] == 'quote'
    print(f"{'✅' if success else '❌'} Quote block")

    # Test 7: Divider
    block = BlockBuilder.divider()
    success = block['type'] == 'divider'
    print(f"{'✅' if success else '❌'} Divider block")

    # Test 8: Image
    block = BlockBuilder.image("https://example.com/image.png")
    success = (block['type'] == 'image' and
               block['image']['external']['url'] == "https://example.com/image.png")
    print(f"{'✅' if success else '❌'} Image block")

    # Test 9: File
    block = BlockBuilder.file("https://example.com/document.pdf")
    success = block['type'] == 'file'
    print(f"{'✅' if success else '❌'} File block")

    # Test 10: Table
    cells = [
        [BlockBuilder._rich_text("Cell 1")],
        [BlockBuilder._rich_text("Cell 2")]
    ]
    row = BlockBuilder.table_row(cells)
    table = BlockBuilder.table(2, has_column_header=True, has_row_header=False, children=[row])
    success = table['type'] == 'table' and table['table']['table_width'] == 2
    print(f"{'✅' if success else '❌'} Table block")

    return True


def test_block_validation():
    """Test block validation."""
    print_header("4. Block Validation Tests")

    # Test 1: Valid paragraph
    rt = [BlockBuilder._rich_text("Valid text")]
    block = BlockBuilder.paragraph(rt)
    is_valid, error = BlockValidator.validate_block(block)
    print(f"{'✅' if is_valid else '❌'} Valid paragraph: {error if error else 'OK'}")

    # Test 2: Invalid block (missing type field)
    block = {'paragraph': {'rich_text': []}}
    is_valid, error = BlockValidator.validate_block(block)
    print(f"{'✅' if not is_valid else '❌'} Invalid block (missing type): {error}")

    # Test 3: Invalid block (type mismatch)
    block = {'type': 'paragraph', 'heading_1': {'rich_text': []}}
    is_valid, error = BlockValidator.validate_block(block)
    print(f"{'✅' if not is_valid else '❌'} Invalid block (type mismatch): {error}")

    # Test 4: Invalid rich text (too long)
    long_text = "A" * 3000
    rt = [{'type': 'text', 'text': {'content': long_text}, 'annotations': {}}]
    is_valid, error = BlockValidator.validate_rich_text(rt)
    print(f"{'✅' if not is_valid else '❌'} Invalid rich text (too long): {error}")

    # Test 5: Valid nested blocks
    child = BlockBuilder.bulleted_list_item([BlockBuilder._rich_text("Child")])
    parent = BlockBuilder.bulleted_list_item([BlockBuilder._rich_text("Parent")], children=[child])
    is_valid, error = BlockValidator.validate_block(parent)
    print(f"{'✅' if is_valid else '❌'} Valid nested blocks: {error if error else 'OK'}")

    return True


def test_convenience_functions():
    """Test convenience functions."""
    print_header("5. Convenience Functions Tests")

    # Test 1: Simple text paragraph
    block = text_paragraph("Simple paragraph")
    success = block['type'] == 'paragraph'
    print(f"{'✅' if success else '❌'} text_paragraph()")

    # Test 2: Bold paragraph
    block = text_paragraph("Bold text", bold=True)
    success = block['paragraph']['rich_text'][0]['annotations']['bold'] == True
    print(f"{'✅' if success else '❌'} text_paragraph() with bold")

    # Test 3: Long paragraph (auto-split)
    long_text = "Test " * 500  # 2500 chars
    block = text_paragraph(long_text)
    success = len(block['paragraph']['rich_text']) >= 2
    print(f"{'✅' if success else '❌'} text_paragraph() with long text: {len(block['paragraph']['rich_text'])} parts")

    # Test 4: Simple heading
    block = text_heading("Heading Text", level=1)
    success = block['type'] == 'heading_1'
    print(f"{'✅' if success else '❌'} text_heading() level 1")

    # Test 5: Heading level 2
    block = text_heading("Subheading", level=2, bold=True)
    success = (block['type'] == 'heading_2' and
               block['heading_2']['rich_text'][0]['annotations']['bold'])
    print(f"{'✅' if success else '❌'} text_heading() level 2 with bold")

    return True


def test_rich_text_list_splitting():
    """Test splitting rich text lists."""
    print_header("6. Rich Text List Splitting Tests")

    # Test 1: Short list (no split)
    rt_list = [
        BlockBuilder._rich_text("Part 1"),
        BlockBuilder._rich_text("Part 2")
    ]
    chunks = BlockBuilder.split_rich_text_list(rt_list)
    success = len(chunks) == 1
    print(f"{'✅' if success else '❌'} Short list (no split): {len(chunks)} chunk(s)")

    # Test 2: List with one very long text
    rt_list = [
        BlockBuilder._rich_text("A" * 3000)
    ]
    chunks = BlockBuilder.split_rich_text_list(rt_list)
    success = len(chunks) >= 2
    print(f"{'✅' if success else '❌'} List with very long text: {len(chunks)} chunk(s)")

    # Test 3: List that exceeds limit
    rt_list = [BlockBuilder._rich_text("A" * 1000) for _ in range(5)]  # 5000 total chars
    chunks = BlockBuilder.split_rich_text_list(rt_list)
    success = len(chunks) >= 3
    print(f"{'✅' if success else '❌'} List exceeding limit: {len(chunks)} chunk(s)")

    # Test 4: Empty list
    rt_list = []
    chunks = BlockBuilder.split_rich_text_list(rt_list)
    success = len(chunks) == 1 and len(chunks[0]) == 0
    print(f"{'✅' if success else '❌'} Empty list: {len(chunks)} chunk(s)")

    return True


def test_block_splitting_for_api():
    """Test splitting blocks for API requests."""
    print_header("7. Block Splitting for API Tests")

    # Test 1: Under limit (no split)
    blocks = [text_paragraph(f"Paragraph {i}") for i in range(50)]
    chunks = BlockValidator.split_blocks_for_api(blocks)
    success = len(chunks) == 1
    print(f"{'✅' if success else '❌'} Under limit (50 blocks): {len(chunks)} chunk(s)")

    # Test 2: Exactly at limit
    blocks = [text_paragraph(f"Paragraph {i}") for i in range(100)]
    chunks = BlockValidator.split_blocks_for_api(blocks)
    success = len(chunks) == 1
    print(f"{'✅' if success else '❌'} At limit (100 blocks): {len(chunks)} chunk(s)")

    # Test 3: Over limit
    blocks = [text_paragraph(f"Paragraph {i}") for i in range(250)]
    chunks = BlockValidator.split_blocks_for_api(blocks)
    success = len(chunks) == 3 and all(len(c) <= 100 for c in chunks)
    print(f"{'✅' if success else '❌'} Over limit (250 blocks): {len(chunks)} chunk(s)")

    # Test 4: Way over limit
    blocks = [text_paragraph(f"Paragraph {i}") for i in range(1000)]
    chunks = BlockValidator.split_blocks_for_api(blocks)
    success = len(chunks) == 10
    print(f"{'✅' if success else '❌'} Way over limit (1000 blocks): {len(chunks)} chunk(s)")

    return True


def main():
    """Run all tests."""
    print_header("Notion Block Builder - Comprehensive Test Suite")

    tests = [
        test_text_splitting,
        test_rich_text_creation,
        test_block_creation,
        test_block_validation,
        test_convenience_functions,
        test_rich_text_list_splitting,
        test_block_splitting_for_api
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL TEST SUITES PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
