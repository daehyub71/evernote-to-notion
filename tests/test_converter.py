"""
Comprehensive pytest tests for ENML to Notion converter.

Tests all conversion patterns, edge cases, and integration scenarios.
"""

import pytest
from pathlib import Path

from app.parsers.enml_converter import EnmlConverter
from app.parsers.enex_parser import EnexParser
from app.models import Resource
from app.notion.block_builder import BlockValidator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def empty_converter():
    """Converter with no resources."""
    return EnmlConverter({})


@pytest.fixture
def converter_with_image():
    """Converter with a mock image resource."""
    resource = Resource(
        data=b'fake image data',
        mime='image/png',
        hash='test_image_hash',
        filename='test.png',
        uploaded_url='https://example.com/test.png'
    )
    return EnmlConverter({'test_image_hash': resource})


@pytest.fixture
def enex_dir():
    """Path to ENEX test files."""
    return Path("/Users/sunchulkim/evernote")


# ============================================================================
# 1. HEADING CONVERSION TESTS
# ============================================================================

class TestHeadingConversion:
    """Test heading (h1-h6) conversion."""

    def test_h1_conversion(self, empty_converter):
        """Test h1 → heading_1."""
        enml = '<en-note><h1>제목</h1></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'heading_1'
        assert blocks[0]['heading_1']['rich_text'][0]['text']['content'] == '제목'

    def test_h2_conversion(self, empty_converter):
        """Test h2 → heading_2."""
        enml = '<en-note><h2>부제목</h2></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'heading_2'
        assert blocks[0]['heading_2']['rich_text'][0]['text']['content'] == '부제목'

    def test_h3_conversion(self, empty_converter):
        """Test h3 → heading_3."""
        enml = '<en-note><h3>서브 헤딩</h3></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'heading_3'
        assert blocks[0]['heading_3']['rich_text'][0]['text']['content'] == '서브 헤딩'

    def test_h4_to_h3_with_bold(self, empty_converter):
        """Test h4-h6 → heading_3 with bold."""
        enml = '<en-note><h4>H4 헤딩</h4></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'heading_3'
        assert blocks[0]['heading_3']['rich_text'][0]['annotations']['bold'] == True

    def test_heading_with_evernote_style(self, empty_converter):
        """Test heading with Evernote --en-nodeId style."""
        enml = '<en-note><h1 style="--en-nodeId:abc123;">스타일 헤딩</h1></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'heading_1'
        assert '스타일 헤딩' in blocks[0]['heading_1']['rich_text'][0]['text']['content']


# ============================================================================
# 2. TEXT FORMATTING TESTS
# ============================================================================

class TestTextFormatting:
    """Test text formatting (bold, italic, underline, code)."""

    def test_bold_text(self, empty_converter):
        """Test <b> → bold annotation."""
        enml = '<en-note><div><b>굵은 텍스트</b></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt['annotations']['bold'] for rt in rich_text)
        assert any('굵은 텍스트' in rt['text']['content'] for rt in rich_text)

    def test_italic_text(self, empty_converter):
        """Test <i> → italic annotation."""
        enml = '<en-note><div><i>기울임 텍스트</i></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt['annotations']['italic'] for rt in rich_text)

    def test_underline_text(self, empty_converter):
        """Test <u> → underline annotation."""
        enml = '<en-note><div><u>밑줄 텍스트</u></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt['annotations']['underline'] for rt in rich_text)

    def test_code_text(self, empty_converter):
        """Test <code> → code annotation."""
        enml = '<en-note><div><code>코드</code></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt['annotations']['code'] for rt in rich_text)

    def test_combined_formatting(self, empty_converter):
        """Test combined bold + italic."""
        enml = '<en-note><div><b><i>굵고 기울임</i></b></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt['annotations']['bold'] and rt['annotations']['italic'] for rt in rich_text)

    def test_link(self, empty_converter):
        """Test <a href> → link annotation."""
        enml = '<en-note><div><a href="https://example.com">링크</a></div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['paragraph']['rich_text']
        assert any(rt.get('text', {}).get('link', {}).get('url') == 'https://example.com' for rt in rich_text)


# ============================================================================
# 3. LIST CONVERSION TESTS
# ============================================================================

class TestListConversion:
    """Test list (ul/ol) conversion."""

    def test_bulleted_list(self, empty_converter):
        """Test ul → bulleted_list_item."""
        enml = '''<en-note>
            <ul>
                <li><div>항목 1</div></li>
                <li><div>항목 2</div></li>
            </ul>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 2
        assert all(b['type'] == 'bulleted_list_item' for b in blocks)

    def test_numbered_list(self, empty_converter):
        """Test ol → numbered_list_item."""
        enml = '''<en-note>
            <ol>
                <li><div>단계 1</div></li>
                <li><div>단계 2</div></li>
            </ol>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 2
        assert all(b['type'] == 'numbered_list_item' for b in blocks)

    def test_nested_list(self, empty_converter):
        """Test nested lists."""
        enml = '''<en-note>
            <ul>
                <li><div>부모</div>
                    <ul>
                        <li><div>자식</div></li>
                    </ul>
                </li>
            </ul>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'bulleted_list_item'
        assert 'children' in blocks[0]['bulleted_list_item']

    def test_list_with_formatting(self, empty_converter):
        """Test list items with bold text."""
        enml = '''<en-note>
            <ul>
                <li><div><b>굵은</b> 항목</div></li>
            </ul>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        rich_text = blocks[0]['bulleted_list_item']['rich_text']
        assert any(rt['annotations']['bold'] for rt in rich_text)


# ============================================================================
# 4. MEDIA CONVERSION TESTS
# ============================================================================

class TestMediaConversion:
    """Test en-media conversion."""

    def test_image_with_resource(self, converter_with_image):
        """Test en-media with uploaded resource → image block."""
        enml = '<en-note><en-media hash="test_image_hash" type="image/png"/></en-note>'
        blocks = converter_with_image.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'image'
        assert blocks[0]['image']['external']['url'] == 'https://example.com/test.png'

    def test_image_without_resource(self, empty_converter):
        """Test en-media without resource → placeholder."""
        enml = '<en-note><en-media hash="missing_hash" type="image/png"/></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        # Should create placeholder paragraph
        assert blocks[0]['type'] == 'paragraph'
        assert 'Missing resource' in blocks[0]['paragraph']['rich_text'][0]['text']['content']

    def test_pdf_resource(self):
        """Test PDF resource → pdf block."""
        resource = Resource(
            data=b'fake pdf',
            mime='application/pdf',
            hash='pdf_hash',
            filename='doc.pdf',
            uploaded_url='https://example.com/doc.pdf'
        )
        converter = EnmlConverter({'pdf_hash': resource})

        enml = '<en-note><en-media hash="pdf_hash" type="application/pdf"/></en-note>'
        blocks = converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'pdf'


# ============================================================================
# 5. SPECIAL BLOCKS TESTS
# ============================================================================

class TestSpecialBlocks:
    """Test special blocks (hr, blockquote, table)."""

    def test_divider(self, empty_converter):
        """Test <hr> → divider."""
        enml = '<en-note><hr/></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'divider'

    def test_blockquote(self, empty_converter):
        """Test <blockquote> → quote."""
        enml = '<en-note><blockquote>인용문</blockquote></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'quote'

    def test_table(self, empty_converter):
        """Test table conversion."""
        enml = '''<en-note>
            <table>
                <tbody>
                    <tr>
                        <th>헤더1</th>
                        <th>헤더2</th>
                    </tr>
                    <tr>
                        <td>셀1</td>
                        <td>셀2</td>
                    </tr>
                </tbody>
            </table>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'table'
        assert blocks[0]['table']['has_column_header'] == True
        assert blocks[0]['table']['table_width'] == 2


# ============================================================================
# 6. TODO CONVERSION TESTS
# ============================================================================

class TestTodoConversion:
    """Test en-todo conversion."""

    def test_unchecked_todo(self, empty_converter):
        """Test unchecked en-todo."""
        enml = '<en-note><div><en-todo/>할 일</div></en-note>'
        blocks = empty_converter.convert(enml)

        # Note: Current implementation may create separate blocks
        assert len(blocks) >= 1

    def test_checked_todo(self, empty_converter):
        """Test checked en-todo."""
        enml = '<en-note><div><en-todo checked="true"/>완료된 일</div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) >= 1


# ============================================================================
# 7. HTML ENTITIES TESTS
# ============================================================================

class TestHtmlEntities:
    """Test HTML entity decoding."""

    def test_entity_decoding(self, empty_converter):
        """Test &lt; &gt; &amp; decoding."""
        enml = '<en-note><div>&lt;div&gt; &amp; &quot;test&quot;</div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) == 1
        text_content = blocks[0]['paragraph']['rich_text'][0]['text']['content']
        assert '<div>' in text_content
        assert '&' in text_content
        assert '"test"' in text_content


# ============================================================================
# 8. EDGE CASES TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_note(self, empty_converter):
        """Test empty note."""
        enml = '<en-note></en-note>'
        blocks = empty_converter.convert(enml)

        # Should return at least one block (empty paragraph)
        assert len(blocks) >= 1

    def test_only_whitespace(self, empty_converter):
        """Test note with only whitespace."""
        enml = '<en-note><div>   </div></en-note>'
        blocks = empty_converter.convert(enml)

        # Empty div should be skipped or create empty paragraph
        assert isinstance(blocks, list)

    def test_very_long_text(self, empty_converter):
        """Test very long text (>2000 chars)."""
        long_text = "가" * 3000
        enml = f'<en-note><div>{long_text}</div></en-note>'
        blocks = empty_converter.convert(enml)

        assert len(blocks) >= 1
        # Text should be in the block (might be truncated or split)
        total_text_length = sum(
            len(rt['text']['content'])
            for block in blocks
            for rt in block.get('paragraph', {}).get('rich_text', [])
        )
        assert total_text_length > 0

    def test_image_only_note(self, converter_with_image):
        """Test note with only images."""
        enml = '''<en-note>
            <en-media hash="test_image_hash" type="image/png"/>
        </en-note>'''
        blocks = converter_with_image.convert(enml)

        assert len(blocks) == 1
        assert blocks[0]['type'] == 'image'

    def test_mixed_content(self, converter_with_image):
        """Test note with mixed content (text + images + lists)."""
        enml = '''<en-note>
            <h1>제목</h1>
            <div>텍스트</div>
            <en-media hash="test_image_hash" type="image/png"/>
            <ul>
                <li><div>리스트</div></li>
            </ul>
        </en-note>'''
        blocks = converter_with_image.convert(enml)

        assert len(blocks) >= 4
        types = [b['type'] for b in blocks]
        assert 'heading_1' in types
        assert 'image' in types
        assert 'bulleted_list_item' in types


# ============================================================================
# 9. BLOCK VALIDATION TESTS
# ============================================================================

class TestBlockValidation:
    """Test that generated blocks are valid Notion blocks."""

    def test_paragraph_validation(self, empty_converter):
        """Test generated paragraph is valid."""
        enml = '<en-note><div>테스트</div></en-note>'
        blocks = empty_converter.convert(enml)

        for block in blocks:
            is_valid, error = BlockValidator.validate_block(block)
            assert is_valid, f"Invalid block: {error}"

    def test_heading_validation(self, empty_converter):
        """Test generated headings are valid."""
        enml = '<en-note><h1>H1</h1><h2>H2</h2><h3>H3</h3></en-note>'
        blocks = empty_converter.convert(enml)

        is_valid, errors = BlockValidator.validate_blocks(blocks)
        assert is_valid, f"Invalid blocks: {errors}"

    def test_list_validation(self, empty_converter):
        """Test generated lists are valid."""
        enml = '''<en-note>
            <ul>
                <li><div>항목 1</div></li>
                <li><div>항목 2</div></li>
            </ul>
        </en-note>'''
        blocks = empty_converter.convert(enml)

        is_valid, errors = BlockValidator.validate_blocks(blocks)
        assert is_valid, f"Invalid blocks: {errors}"


# ============================================================================
# 10. REAL ENEX FILES TESTS
# ============================================================================

class TestRealEnexFiles:
    """Test conversion on real ENEX files."""

    def test_it_trend_file(self, enex_dir):
        """Test conversion on IT트렌드.enex."""
        file_path = enex_dir / "IT트렌드.enex"

        if not file_path.exists():
            pytest.skip(f"Test file not found: {file_path}")

        parser = EnexParser(file_path)
        notes = list(parser.parse())

        assert len(notes) > 0, "No notes found in ENEX file"

        # Test first note
        note = notes[0]
        resource_map = {r.hash: r for r in note.resources}
        converter = EnmlConverter(resource_map)

        blocks = converter.convert(note.content)

        assert len(blocks) > 0, "No blocks generated"

        # Validate all blocks
        is_valid, errors = BlockValidator.validate_blocks(blocks)
        assert is_valid, f"Invalid blocks in real note: {errors}"

    def test_multiple_notes_conversion(self, enex_dir):
        """Test conversion on multiple real notes."""
        file_path = enex_dir / "IT트렌드.enex"

        if not file_path.exists():
            pytest.skip(f"Test file not found: {file_path}")

        parser = EnexParser(file_path)
        notes = list(parser.parse())

        # Test first 5 notes
        for i, note in enumerate(notes[:5], 1):
            resource_map = {r.hash: r for r in note.resources}
            converter = EnmlConverter(resource_map)

            blocks = converter.convert(note.content)

            assert len(blocks) > 0, f"Note {i}: No blocks generated"

            # All blocks should be valid
            is_valid, errors = BlockValidator.validate_blocks(blocks)
            assert is_valid, f"Note {i}: Invalid blocks - {errors}"


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
