#!/usr/bin/env python3
"""Isolated test for upload cache deduplication."""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app.parsers.enex_parser import EnexParser
from app.resources.resource_extractor import ResourceExtractor
from app.resources.cloudinary_uploader import CloudinaryUploader
from app.resources.batch_uploader import BatchUploader
from app.resources.upload_cache import UploadCache


def main():
    print("="*80)
    print("  Isolated Cache Deduplication Test")
    print("="*80)

    # Use small test file
    test_file = Path("/Users/sunchulkim/evernote/냅킨경제학.enex")

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    # Parse and extract resources
    parser = EnexParser(str(test_file))
    notes = list(parser.parse())

    extractor = ResourceExtractor(output_dir="data/temp/cache_test")
    all_resources = []

    for note in notes:
        if note.resources:
            resource_map = extractor.extract_resources(note)
            all_resources.extend(resource_map.values())

    print(f"\n📦 Extracted {len(all_resources)} resources")

    if not all_resources:
        print("⚠️  No resources found")
        return False

    # Clear cache file
    cache_file = Path("data/checkpoint/test_cache_isolated.json")
    if cache_file.exists():
        cache_file.unlink()
        print(f"🗑️  Cleared old cache file")

    # Initialize uploader and cache
    cloudinary_uploader = CloudinaryUploader()
    cache = UploadCache(str(cache_file))

    print(f"\n✅ Initial cache state: {len(cache)} entries")

    # FIRST UPLOAD
    print("\n" + "="*80)
    print("  FIRST UPLOAD (should upload to Cloudinary)")
    print("="*80)

    batch_uploader1 = BatchUploader(cloudinary_uploader, max_workers=5)
    urls1 = batch_uploader1.upload_resources(all_resources, cache=cache.cache)

    print(f"\n📊 First upload stats:")
    stats1 = batch_uploader1.get_stats()
    print(f"   Uploaded: {stats1['uploaded']}")
    print(f"   Cached: {stats1['cached']}")
    print(f"   Failed: {stats1['failed']}")

    print(f"\n💾 Cache state before save: {len(cache.cache)} entries")
    print(f"   Sample entries: {list(cache.cache.keys())[:3] if cache.cache else 'None'}")

    # Save cache
    cache.save()
    print(f"✅ Cache saved to {cache_file}")

    # Verify cache file
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    print(f"\n📁 Cache file verification:")
    print(f"   Total entries in file: {cache_data['metadata']['total_entries']}")
    print(f"   Entries dict size: {len(cache_data['entries'])}")

    # SECOND UPLOAD
    print("\n" + "="*80)
    print("  SECOND UPLOAD (should use cache)")
    print("="*80)

    # Reload cache from file
    cache2 = UploadCache(str(cache_file))
    print(f"🔄 Reloaded cache: {len(cache2)} entries")

    batch_uploader2 = BatchUploader(cloudinary_uploader, max_workers=5)
    urls2 = batch_uploader2.upload_resources(all_resources, cache=cache2.cache)

    print(f"\n📊 Second upload stats:")
    stats2 = batch_uploader2.get_stats()
    print(f"   Uploaded: {stats2['uploaded']}")
    print(f"   Cached: {stats2['cached']}")
    print(f"   Failed: {stats2['failed']}")

    # VERIFICATION
    print("\n" + "="*80)
    print("  VERIFICATION")
    print("="*80)

    expected_cached = len(all_resources)
    actual_cached = stats2['cached']

    if actual_cached == expected_cached:
        print(f"✅ SUCCESS: All {actual_cached} files were cached")
        print(f"✅ First upload: {stats1['uploaded']} uploaded, {stats1['cached']} cached")
        print(f"✅ Second upload: {stats2['uploaded']} uploaded, {stats2['cached']} cached")
        return True
    else:
        print(f"❌ FAILURE: Expected {expected_cached} cached, got {actual_cached}")
        print(f"   First upload: {stats1['uploaded']} uploaded, {stats1['cached']} cached")
        print(f"   Second upload: {stats2['uploaded']} uploaded, {stats2['cached']} cached")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
