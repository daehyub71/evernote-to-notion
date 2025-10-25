#!/usr/bin/env python3
"""
Test ENML converter with real ENEX files.

Tests conversion on actual notes from ENEX files.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.parsers.enex_parser import EnexParser
from app.parsers.enml_converter import EnmlConverter


def test_real_enex():
    """Test converter on real ENEX files."""
    enex_dir = Path("/Users/sunchulkim/evernote")

    # Test on a small file first
    test_files = [
        "IT트렌드.enex",
        "금융정보.enex",
        "시작하세요.enex"
    ]

    for filename in test_files:
        file_path = enex_dir / filename
        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        print(f"\n{'=' * 80}")
        print(f"Testing: {filename}")
        print('=' * 80)

        # Parse ENEX
        parser = EnexParser(file_path)
        notes = list(parser.parse())

        print(f"Found {len(notes)} notes")

        # Test first 3 notes
        for i, note in enumerate(notes[:3], 1):
            print(f"\n--- Note {i}: {note.title} ---")

            # Build resource map
            resource_map = {r.hash: r for r in note.resources}

            # Convert ENML
            converter = EnmlConverter(resource_map)

            try:
                blocks = converter.convert(note.content)
                print(f"✅ Converted to {len(blocks)} blocks")

                # Show first 2 blocks
                for j, block in enumerate(blocks[:2], 1):
                    block_type = block['type']
                    print(f"  Block {j}: {block_type}")

                    if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
                        rich_text = block[block_type].get('rich_text', [])
                        if rich_text:
                            text_preview = rich_text[0]['text']['content'][:100]
                            print(f"    Text: {text_preview}...")

                    elif block_type == 'image':
                        print(f"    [Image block - resource linked]")

                    elif block_type in ['bulleted_list_item', 'numbered_list_item']:
                        rich_text = block[block_type].get('rich_text', [])
                        if rich_text:
                            text_preview = rich_text[0]['text']['content'][:100]
                            print(f"    Item: {text_preview}...")

                if len(blocks) > 2:
                    print(f"  ... and {len(blocks) - 2} more blocks")

                # Count block types
                block_types = {}
                for block in blocks:
                    block_type = block['type']
                    block_types[block_type] = block_types.get(block_type, 0) + 1

                print(f"\n  Block type distribution:")
                for block_type, count in sorted(block_types.items(), key=lambda x: -x[1]):
                    print(f"    {block_type}: {count}")

            except Exception as e:
                print(f"❌ Conversion failed: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n{'=' * 80}")
    print("Real ENEX testing complete!")
    print('=' * 80)


if __name__ == '__main__':
    test_real_enex()
