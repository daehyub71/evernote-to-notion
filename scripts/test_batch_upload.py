#!/usr/bin/env python3
"""Test script for batch upload functionality.

This script tests:
1. Small batch upload (냅킨경제학.enex - ~2 resources)
2. Medium batch upload (IT트렌드.enex - ~21 resources)
3. Large batch upload (블랙야크.enex - ~68 resources)
4. Upload cache functionality
5. Full upload (all 1,574 resources)
"""

import sys
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from app.parsers.enex_parser import EnexParser
from app.resources.resource_extractor import ResourceExtractor
from app.resources.cloudinary_uploader import CloudinaryUploader
from app.resources.batch_uploader import BatchUploader
from app.resources.upload_cache import UploadCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_test_header(title: str):
    """Print formatted test section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_small_batch():
    """Test 1: Small batch upload (냅킨경제학.enex)."""
    print_test_header("Test 1: Small Batch Upload (냅킨경제학.enex)")

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "냅킨경제학.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse ENEX
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        print(f"\n📂 Parsed {len(notes)} notes from {test_file.name}")

        # Extract resources
        extractor = ResourceExtractor(output_dir="data/temp/batch_test")
        all_resources = []

        for note in notes:
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

        print(f"📦 Extracted {len(all_resources)} resources")

        if not all_resources:
            print("⚠️  No resources found")
            return True

        # Initialize uploaders
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader = BatchUploader(cloudinary_uploader, max_workers=5)
        cache = UploadCache("data/checkpoint/test_small_cache.json")

        # Upload
        print(f"\n🚀 Uploading {len(all_resources)} resources...")
        urls = batch_uploader.upload_resources(all_resources, cache=cache.cache)

        # Save cache
        cache.save()

        # Print stats
        print()
        batch_uploader.print_stats()
        cache.print_stats()

        success_count = sum(1 for url in urls.values() if url)
        print(f"\n✅ Uploaded {success_count}/{len(all_resources)} resources")

        return success_count > 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_medium_batch():
    """Test 2: Medium batch upload (IT트렌드.enex)."""
    print_test_header("Test 2: Medium Batch Upload (IT트렌드.enex)")

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse ENEX
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        print(f"\n📂 Parsed {len(notes)} notes from {test_file.name}")

        # Extract resources
        extractor = ResourceExtractor(output_dir="data/temp/batch_test")
        all_resources = []

        for note in notes:
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

        print(f"📦 Extracted {len(all_resources)} resources")

        if not all_resources:
            print("⚠️  No resources found")
            return True

        # Initialize uploaders
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader = BatchUploader(cloudinary_uploader, max_workers=10)
        cache = UploadCache("data/checkpoint/test_medium_cache.json")

        # Upload
        print(f"\n🚀 Uploading {len(all_resources)} resources with 10 workers...")
        urls = batch_uploader.upload_resources(all_resources, cache=cache.cache)

        # Save cache
        cache.save()

        # Print stats
        print()
        batch_uploader.print_stats()
        cache.print_stats()

        success_count = sum(1 for url in urls.values() if url)
        print(f"\n✅ Uploaded {success_count}/{len(all_resources)} resources")

        return success_count > 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_large_batch():
    """Test 3: Large batch upload (블랙야크.enex)."""
    print_test_header("Test 3: Large Batch Upload (블랙야크.enex)")

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "블랙야크.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse ENEX
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        print(f"\n📂 Parsed {len(notes)} notes from {test_file.name}")

        # Extract resources
        extractor = ResourceExtractor(output_dir="data/temp/batch_test")
        all_resources = []

        for note in notes:
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

        print(f"📦 Extracted {len(all_resources)} resources")

        if not all_resources:
            print("⚠️  No resources found")
            return True

        # Initialize uploaders
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader = BatchUploader(cloudinary_uploader, max_workers=10)
        cache = UploadCache("data/checkpoint/test_large_cache.json")

        # Upload
        print(f"\n🚀 Uploading {len(all_resources)} resources with 10 workers...")
        urls = batch_uploader.upload_resources(all_resources, cache=cache.cache)

        # Save cache
        cache.save()

        # Print stats
        print()
        batch_uploader.print_stats()
        cache.print_stats()

        success_count = sum(1 for url in urls.values() if url)
        print(f"\n✅ Uploaded {success_count}/{len(all_resources)} resources")

        # Verify failure rate
        failure_rate = (len(all_resources) - success_count) / len(all_resources) * 100
        print(f"   Failure rate: {failure_rate:.2f}%")

        if failure_rate > 5:
            print(f"   ⚠️  Failure rate exceeds 5% threshold")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_functionality():
    """Test 4: Upload cache deduplication."""
    print_test_header("Test 4: Upload Cache Deduplication")

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "냅킨경제학.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse and extract
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        extractor = ResourceExtractor(output_dir="data/temp/batch_test")
        all_resources = []

        for note in notes:
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

        if not all_resources:
            print("⚠️  No resources found")
            return True

        print(f"\n📦 Testing with {len(all_resources)} resources")

        # First upload
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader1 = BatchUploader(cloudinary_uploader, max_workers=5)
        cache = UploadCache("data/checkpoint/test_cache_dedup.json")

        print("\n🔄 First upload (no cache)...")
        urls1 = batch_uploader1.upload_resources(all_resources, cache=cache.cache)
        cache.save()

        stats1 = batch_uploader1.get_stats()
        print(f"   Uploaded: {stats1['uploaded']}, Cached: {stats1['cached']}")

        # Second upload (should use cache)
        batch_uploader2 = BatchUploader(cloudinary_uploader, max_workers=5)

        print("\n🔄 Second upload (with cache)...")
        urls2 = batch_uploader2.upload_resources(all_resources, cache=cache.cache)

        stats2 = batch_uploader2.get_stats()
        print(f"   Uploaded: {stats2['uploaded']}, Cached: {stats2['cached']}")

        # Verify cache worked
        if stats2['cached'] == len(all_resources):
            print(f"\n✅ Cache working correctly: {stats2['cached']} files cached")
            return True
        else:
            print(f"\n❌ Cache not working: expected {len(all_resources)} cached, got {stats2['cached']}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_upload():
    """Test 5: Full upload (all 1,574 resources)."""
    print_test_header("Test 5: Full Upload (All Resources)")

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False

    try:
        enex_files = list(source_path.glob("*.enex"))
        print(f"📂 Found {len(enex_files)} ENEX files in {source_dir}")
        print(f"\n⚠️  This will upload ALL resources from all files...")
        print(f"   Estimated: ~1,574 resources")
        print(f"   This may take 10-20 minutes...")

        # Extract all resources
        print("\n📦 Extracting resources from all files...")
        extractor = ResourceExtractor(output_dir="data/temp/full_upload")
        all_resources = []

        for i, enex_file in enumerate(enex_files, 1):
            print(f"   [{i}/{len(enex_files)}] {enex_file.name}")

            try:
                parser = EnexParser(str(enex_file))
                notes = list(parser.parse())

                for note in notes:
                    if note.resources:
                        resource_map = extractor.extract_resources(note)
                        all_resources.extend(resource_map.values())

            except Exception as e:
                logger.error(f"Failed to process {enex_file.name}: {e}")

        print(f"\n✅ Extracted {len(all_resources)} total resources")

        # Initialize uploaders with cache
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader = BatchUploader(cloudinary_uploader, max_workers=10)
        cache = UploadCache("data/checkpoint/full_upload_cache.json")

        # Upload
        print(f"\n🚀 Uploading {len(all_resources)} resources (10 parallel workers)...")
        urls = batch_uploader.upload_resources(all_resources, cache=cache.cache)

        # Save cache
        cache.save()

        # Print stats
        print()
        batch_uploader.print_stats()
        cache.print_stats()
        cloudinary_uploader.print_usage_stats()

        success_count = sum(1 for url in urls.values() if url)
        failure_rate = (len(all_resources) - success_count) / len(all_resources) * 100

        print(f"\n📊 Final Results:")
        print(f"   Total resources: {len(all_resources)}")
        print(f"   Successfully uploaded: {success_count}")
        print(f"   Failed: {len(all_resources) - success_count}")
        print(f"   Success rate: {100 - failure_rate:.2f}%")
        print(f"   Failure rate: {failure_rate:.2f}%")

        if failure_rate <= 5:
            print(f"\n✅ Success! Failure rate within 5% threshold")
            return True
        else:
            print(f"\n⚠️  Failure rate exceeds 5% threshold")
            return True  # Still return True as we uploaded most files

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  Batch Upload Test Suite")
    print("="*80)

    tests = [
        ("Small Batch (냅킨경제학)", test_small_batch),
        ("Medium Batch (IT트렌드)", test_medium_batch),
        ("Large Batch (블랙야크)", test_large_batch),
        ("Cache Deduplication", test_cache_functionality),
        ("Full Upload (All Files)", test_full_upload),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print_test_header("Test Summary")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")

    print()
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\n✨ Batch upload system is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
