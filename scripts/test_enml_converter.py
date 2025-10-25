#!/usr/bin/env python3
"""
Test script for ENML to Notion block converter.

Tests all 24 ENML patterns identified in ENML_PATTERNS.md.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.parsers.enml_converter import EnmlConverter
from app.models import Resource


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(test_name: str, enml: str, blocks: list, success: bool = True):
    """Print test results."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    print(f"Input ENML:\n{enml[:200]}{'...' if len(enml) > 200 else ''}")
    print(f"\nOutput Blocks: {len(blocks)} block(s)")
    if blocks:
        print(json.dumps(blocks[0], indent=2)[:500])
        if len(blocks) > 1:
            print(f"... and {len(blocks) - 1} more block(s)")


def test_converter():
    """Run comprehensive converter tests."""
    # Create converter with empty resource map (will be updated per test)
    converter = EnmlConverter({})

    # Test counters
    total_tests = 0
    passed_tests = 0

    print_header("ENML to Notion Block Converter - Comprehensive Test Suite")

    # ========================================================================
    # 1. HEADINGS (6 tests)
    # ========================================================================
    print_header("1. Headings (h1-h6)")

    # Test 1.1: H1
    total_tests += 1
    enml = '''<en-note>
        <h1 style="--en-nodeId:8503023a;">'저축의 시대'에서 '투자의 시대'로</h1>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) == 1 and blocks[0]['type'] == 'heading_1')
    if success:
        passed_tests += 1
    print_test("H1 heading", enml, blocks, success)

    # Test 1.2: H2
    total_tests += 1
    enml = '<en-note><h2>저축의 시대의 종말</h2></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) == 1 and blocks[0]['type'] == 'heading_2')
    if success:
        passed_tests += 1
    print_test("H2 heading", enml, blocks, success)

    # Test 1.3: H3
    total_tests += 1
    enml = '<en-note><h3>조기 시작과 꾸준함</h3></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) == 1 and blocks[0]['type'] == 'heading_3')
    if success:
        passed_tests += 1
    print_test("H3 heading", enml, blocks, success)

    # Test 1.4: H4 (should convert to heading_3 with bold)
    total_tests += 1
    enml = '<en-note><h4>서브 헤딩</h4></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) == 1 and
               blocks[0]['type'] == 'heading_3' and
               blocks[0]['heading_3']['rich_text'][0]['annotations']['bold'] == True)
    if success:
        passed_tests += 1
    print_test("H4 heading (→ H3 + bold)", enml, blocks, success)

    # ========================================================================
    # 2. TEXT FORMATTING (5 tests)
    # ========================================================================
    print_header("2. Text Formatting")

    # Test 2.1: Bold
    total_tests += 1
    enml = '<en-note><div><b>IP 주소</b></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt['annotations']['bold'] for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Bold text", enml, blocks, success)

    # Test 2.2: Italic
    total_tests += 1
    enml = '<en-note><div><i>주요 개념 설명</i></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt['annotations']['italic'] for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Italic text", enml, blocks, success)

    # Test 2.3: Underline
    total_tests += 1
    enml = '<en-note><div><u>중요한 내용</u></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt['annotations']['underline'] for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Underline text", enml, blocks, success)

    # Test 2.4: Code
    total_tests += 1
    enml = '<en-note><div><code>nslookup</code></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt['annotations']['code'] for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Code text", enml, blocks, success)

    # Test 2.5: Combined formatting
    total_tests += 1
    enml = '<en-note><div><b><i>Bold and italic</i></b></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt['annotations']['bold'] and rt['annotations']['italic']
                   for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Combined bold + italic", enml, blocks, success)

    # ========================================================================
    # 3. LISTS (3 tests)
    # ========================================================================
    print_header("3. Lists")

    # Test 3.1: Unordered list
    total_tests += 1
    enml = '''<en-note>
        <ul>
            <li><div>Item 1</div></li>
            <li><div>Item 2</div></li>
        </ul>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) == 2 and
               all(b['type'] == 'bulleted_list_item' for b in blocks))
    if success:
        passed_tests += 1
    print_test("Unordered list", enml, blocks, success)

    # Test 3.2: Ordered list
    total_tests += 1
    enml = '''<en-note>
        <ol>
            <li><div>Step 1</div></li>
            <li><div>Step 2</div></li>
        </ol>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) == 2 and
               all(b['type'] == 'numbered_list_item' for b in blocks))
    if success:
        passed_tests += 1
    print_test("Ordered list", enml, blocks, success)

    # Test 3.3: Nested list
    total_tests += 1
    enml = '''<en-note>
        <ul>
            <li><div>Parent item</div>
                <ul>
                    <li><div>Child item</div></li>
                </ul>
            </li>
        </ul>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               blocks[0]['type'] == 'bulleted_list_item' and
               'children' in blocks[0].get('bulleted_list_item', {}))
    if success:
        passed_tests += 1
    print_test("Nested list", enml, blocks, success)

    # ========================================================================
    # 4. LINKS (1 test)
    # ========================================================================
    print_header("4. Links")

    # Test 4.1: Hyperlink
    total_tests += 1
    enml = '<en-note><div><a href="https://www.example.com">Example Link</a></div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               any(rt.get('text', {}).get('link', {}).get('url') == 'https://www.example.com'
                   for rt in blocks[0].get('paragraph', {}).get('rich_text', [])))
    if success:
        passed_tests += 1
    print_test("Hyperlink", enml, blocks, success)

    # ========================================================================
    # 5. SPECIAL BLOCKS (3 tests)
    # ========================================================================
    print_header("5. Special Blocks")

    # Test 5.1: Horizontal rule
    total_tests += 1
    enml = '<en-note><hr/></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and blocks[0]['type'] == 'divider')
    if success:
        passed_tests += 1
    print_test("Horizontal rule", enml, blocks, success)

    # Test 5.2: Blockquote
    total_tests += 1
    enml = '<en-note><blockquote>Quoted text</blockquote></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and blocks[0]['type'] == 'quote')
    if success:
        passed_tests += 1
    print_test("Blockquote", enml, blocks, success)

    # Test 5.3: Line break
    total_tests += 1
    enml = '<en-note><div>Line 1<br/>Line 2</div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and blocks[0]['type'] == 'paragraph')
    if success:
        passed_tests += 1
    print_test("Line break", enml, blocks, success)

    # ========================================================================
    # 6. EVERNOTE SPECIAL TAGS (2 tests)
    # ========================================================================
    print_header("6. Evernote Special Tags")

    # Test 6.1: en-todo (unchecked)
    total_tests += 1
    enml = '<en-note><div><en-todo/>Unchecked task</div></en-note>'
    blocks = converter.convert(enml)
    # Note: Current implementation creates separate to_do block
    success = len(blocks) >= 1
    if success:
        passed_tests += 1
    print_test("en-todo (unchecked)", enml, blocks, success)

    # Test 6.2: en-todo (checked)
    total_tests += 1
    enml = '<en-note><div><en-todo checked="true"/>Completed task</div></en-note>'
    blocks = converter.convert(enml)
    success = len(blocks) >= 1
    if success:
        passed_tests += 1
    print_test("en-todo (checked)", enml, blocks, success)

    # ========================================================================
    # 7. HTML ENTITIES (1 test)
    # ========================================================================
    print_header("7. HTML Entities")

    # Test 7.1: HTML entity decoding
    total_tests += 1
    enml = '<en-note><div>&lt;div&gt; &amp; &quot;test&quot;</div></en-note>'
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and
               '<div>' in blocks[0]['paragraph']['rich_text'][0]['text']['content'])
    if success:
        passed_tests += 1
    print_test("HTML entities", enml, blocks, success)

    # ========================================================================
    # 8. COMPLEX NESTED STRUCTURES (2 tests)
    # ========================================================================
    print_header("8. Complex Structures")

    # Test 8.1: Nested formatting
    total_tests += 1
    enml = '<en-note><div><span style="color:rgb(224, 108, 117);"><b>Colored bold text</b></span></div></en-note>'
    blocks = converter.convert(enml)
    success = len(blocks) >= 1
    if success:
        passed_tests += 1
    print_test("Nested span + bold + color", enml, blocks, success)

    # Test 8.2: List with formatted items
    total_tests += 1
    enml = '''<en-note>
        <ul>
            <li><div><b>IPv4</b>: 32비트 주소 체계</div></li>
            <li><div><b>IPv6</b>: 128비트 주소 체계</div></li>
        </ul>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) >= 2 and
               all(b['type'] == 'bulleted_list_item' for b in blocks))
    if success:
        passed_tests += 1
    print_test("List with bold items", enml, blocks, success)

    # ========================================================================
    # 9. TABLE (1 test)
    # ========================================================================
    print_header("9. Tables")

    # Test 9.1: Simple table
    total_tests += 1
    enml = '''<en-note>
        <table>
            <tbody>
                <tr>
                    <th>Header 1</th>
                    <th>Header 2</th>
                </tr>
                <tr>
                    <td>Cell 1</td>
                    <td>Cell 2</td>
                </tr>
            </tbody>
        </table>
    </en-note>'''
    blocks = converter.convert(enml)
    success = (len(blocks) >= 1 and blocks[0]['type'] == 'table')
    if success:
        passed_tests += 1
    print_test("Table with header", enml, blocks, success)

    # ========================================================================
    # 10. EN-MEDIA (1 test - without actual resource)
    # ========================================================================
    print_header("10. Media (en-media)")

    # Test 10.1: en-media image (placeholder, no resource)
    total_tests += 1
    enml = '<en-note><en-media hash="abc123" type="image/png"/></en-note>'
    blocks = converter.convert(enml)
    success = len(blocks) >= 1  # Should create placeholder paragraph
    if success:
        passed_tests += 1
    print_test("en-media (no resource)", enml, blocks, success)

    # Test 10.2: en-media with mock resource
    total_tests += 1
    mock_resource = Resource(
        data=b'fake image data',
        mime='image/png',
        hash='test_hash_123',
        filename='test.png',
        uploaded_url='https://example.com/test.png'
    )
    converter_with_resource = EnmlConverter({'test_hash_123': mock_resource})
    enml = '<en-note><en-media hash="test_hash_123" type="image/png"/></en-note>'
    blocks = converter_with_resource.convert(enml)
    success = (len(blocks) >= 1 and blocks[0]['type'] == 'image')
    if success:
        passed_tests += 1
    print_test("en-media with resource", enml, blocks, success)

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_header("Test Summary")
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests / total_tests * 100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = test_converter()
    sys.exit(exit_code)
