#!/usr/bin/env python3
"""
ENML (Evernote Markup Language) analysis script.

Analyzes ENEX files to extract ENML tags, patterns, and samples.
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.enex_parser import EnexParser


def extract_enml_tags(enex_file: str) -> Counter:
    """
    Extract all ENML/HTML tags from notes in an ENEX file.

    Args:
        enex_file: Path to ENEX file

    Returns:
        Counter of tag names
    """
    parser = EnexParser(enex_file)
    tag_counter = Counter()

    for note in parser.parse():
        # Find all opening tags
        tags = re.findall(r'<(\w+(?:-\w+)?)', note.content)
        tag_counter.update(tags)

    return tag_counter


def extract_tag_samples(enex_file: str, max_samples: int = 3) -> dict:
    """
    Extract sample ENML content for each tag type.

    Args:
        enex_file: Path to ENEX file
        max_samples: Maximum samples per tag

    Returns:
        Dictionary of tag -> list of sample strings
    """
    parser = EnexParser(enex_file)
    tag_samples = defaultdict(list)

    for note in parser.parse():
        # Extract complete tag patterns (opening + content + closing)
        content = note.content

        # Find all tags with their content
        # Pattern: <tag ...>content</tag> or <tag ... />
        patterns = [
            (r'(<en-media[^>]*/>)', 'en-media'),
            (r'(<en-todo[^>]*>)', 'en-todo'),
            (r'(<br\s*/?> )', 'br'),
            (r'(<h1[^>]*>.*?</h1>)', 'h1'),
            (r'(<h2[^>]*>.*?</h2>)', 'h2'),
            (r'(<h3[^>]*>.*?</h3>)', 'h3'),
            (r'(<ul[^>]*>.*?</ul>)', 'ul'),
            (r'(<ol[^>]*>.*?</ol>)', 'ol'),
            (r'(<li[^>]*>.*?</li>)', 'li'),
            (r'(<a[^>]*>.*?</a>)', 'a'),
            (r'(<b[^>]*>.*?</b>)', 'b'),
            (r'(<i[^>]*>.*?</i>)', 'i'),
            (r'(<u[^>]*>.*?</u>)', 'u'),
            (r'(<span[^>]*>.*?</span>)', 'span'),
            (r'(<div[^>]*>.*?</div>)', 'div'),
            (r'(<table[^>]*>.*?</table>)', 'table'),
        ]

        for pattern, tag_name in patterns:
            if len(tag_samples[tag_name]) < max_samples:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches[:max_samples - len(tag_samples[tag_name])]:
                    # Truncate long samples
                    sample = match[:200] + '...' if len(match) > 200 else match
                    if sample not in tag_samples[tag_name]:
                        tag_samples[tag_name].append(sample)

    return dict(tag_samples)


def find_special_cases(enex_file: str) -> dict:
    """
    Find special ENML cases (entities, nested tags, styles).

    Args:
        enex_file: Path to ENEX file

    Returns:
        Dictionary of special case types -> examples
    """
    parser = EnexParser(enex_file)
    special_cases = {
        'html_entities': set(),
        'nested_tags': [],
        'style_attributes': [],
        'en_media_types': Counter(),
    }

    entity_pattern = r'&\w+;'
    style_pattern = r'style="[^"]*"'

    for note in parser.parse():
        content = note.content

        # HTML entities
        entities = re.findall(entity_pattern, content)
        special_cases['html_entities'].update(entities)

        # Style attributes
        styles = re.findall(style_pattern, content)
        special_cases['style_attributes'].extend(styles[:5])  # Max 5 samples

        # en-media types
        media_tags = re.findall(r'<en-media[^>]*type="([^"]*)"', content)
        special_cases['en_media_types'].update(media_tags)

        # Nested tags (simplified detection)
        if '<div' in content and '<span' in content:
            # Find a sample of nested structure
            nested = re.findall(r'<div[^>]*>.*?<span[^>]*>.*?</span>.*?</div>', content, re.DOTALL)
            if nested and len(special_cases['nested_tags']) < 3:
                sample = nested[0][:200] + '...' if len(nested[0]) > 200 else nested[0]
                special_cases['nested_tags'].append(sample)

    # Convert sets to lists for JSON serialization
    special_cases['html_entities'] = list(special_cases['html_entities'])
    special_cases['en_media_types'] = dict(special_cases['en_media_types'])

    return special_cases


def analyze_all_files(source_dir: str, output_file: str = None):
    """
    Analyze all ENEX files and generate comprehensive report.

    Args:
        source_dir: Directory containing ENEX files
        output_file: Optional output file for results
    """
    source_path = Path(source_dir)
    enex_files = sorted(source_path.glob('*.enex'))

    print(f"\n{'='*80}")
    print(f"ENML Analysis - {len(enex_files)} files")
    print('='*80)

    # Aggregate results
    all_tags = Counter()
    all_samples = defaultdict(list)
    all_special = {
        'html_entities': set(),
        'nested_tags': [],
        'style_attributes': [],
        'en_media_types': Counter(),
    }

    for enex_file in enex_files[:5]:  # Analyze first 5 files for speed
        print(f"\nAnalyzing: {enex_file.name}")

        # Extract tags
        tags = extract_enml_tags(str(enex_file))
        all_tags.update(tags)

        # Extract samples
        samples = extract_tag_samples(str(enex_file), max_samples=2)
        for tag, sample_list in samples.items():
            all_samples[tag].extend(sample_list[:2])

        # Find special cases
        special = find_special_cases(str(enex_file))
        all_special['html_entities'].update(special['html_entities'])
        all_special['nested_tags'].extend(special['nested_tags'][:2])
        all_special['style_attributes'].extend(special['style_attributes'][:2])
        all_special['en_media_types'].update(special['en_media_types'])

    # Print results
    print(f"\n{'─'*80}")
    print("Tag Frequency Analysis")
    print('─'*80)
    print(f"{'Tag':<20} | {'Count':>10}")
    print('─'*80)

    for tag, count in all_tags.most_common(30):
        print(f"{tag:<20} | {count:>10}")

    print(f"\n{'─'*80}")
    print("Special Cases")
    print('─'*80)

    print(f"\nHTML Entities ({len(all_special['html_entities'])} unique):")
    for entity in sorted(all_special['html_entities'])[:20]:
        print(f"  {entity}")

    print(f"\nen-media MIME Types:")
    for mime, count in Counter(all_special['en_media_types']).most_common():
        print(f"  {mime}: {count}")

    print(f"\nStyle Attributes (samples):")
    for style in all_special['style_attributes'][:5]:
        print(f"  {style}")

    # Save to file if requested
    if output_file:
        results = {
            'tags': dict(all_tags),
            'samples': dict(all_samples),
            'special_cases': {
                'html_entities': list(all_special['html_entities']),
                'nested_tags': all_special['nested_tags'],
                'style_attributes': all_special['style_attributes'],
                'en_media_types': dict(all_special['en_media_types']),
            }
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Results saved to: {output_file}")

    # Summary
    print(f"\n{'='*80}")
    print("Summary:")
    print(f"  Unique tags: {len(all_tags)}")
    print(f"  HTML entities: {len(all_special['html_entities'])}")
    print(f"  MIME types in en-media: {len(all_special['en_media_types'])}")
    print('='*80)


def analyze_single_file(file_path: str, verbose: bool = False):
    """Analyze a single ENEX file."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {Path(file_path).name}")
    print('='*80)

    # Extract tags
    tags = extract_enml_tags(file_path)
    print(f"\n{'Tag':<20} | {'Count':>10}")
    print('─'*35)
    for tag, count in tags.most_common(20):
        print(f"{tag:<20} | {count:>10}")

    if verbose:
        # Extract samples
        print(f"\n{'─'*80}")
        print("Tag Samples:")
        print('─'*80)

        samples = extract_tag_samples(file_path, max_samples=2)
        for tag, sample_list in sorted(samples.items()):
            if sample_list:
                print(f"\n<{tag}>:")
                for i, sample in enumerate(sample_list, 1):
                    print(f"  {i}. {sample}")

        # Special cases
        print(f"\n{'─'*80}")
        print("Special Cases:")
        print('─'*80)

        special = find_special_cases(file_path)
        print(f"\nHTML Entities: {special['html_entities']}")
        print(f"\nen-media types: {special['en_media_types']}")


def main():
    parser = argparse.ArgumentParser(description='Analyze ENML content in ENEX files')
    parser.add_argument('--file', help='Analyze a single ENEX file')
    parser.add_argument('--all', action='store_true', help='Analyze all ENEX files')
    parser.add_argument('--dir', default='/Users/sunchulkim/evernote',
                       help='Directory containing ENEX files')
    parser.add_argument('-o', '--output', help='Output JSON file for results')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.dir) / args.file if not Path(args.file).is_absolute() else Path(args.file)
        analyze_single_file(str(file_path), verbose=args.verbose)
    elif args.all:
        analyze_all_files(args.dir, output_file=args.output)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
