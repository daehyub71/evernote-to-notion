#!/usr/bin/env python3
"""Test script for Cloudinary upload functionality.

This script tests:
1. Cloudinary connection and authentication
2. Single file upload
3. Batch upload
4. Resource map upload
5. Account usage statistics
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.parsers.enex_parser import EnexParser
from app.resources.resource_extractor import ResourceExtractor
from app.resources.cloudinary_uploader import CloudinaryUploader

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


def test_connection():
    """Test 1: Verify Cloudinary connection and credentials."""
    print_test_header("Test 1: Cloudinary Connection")

    try:
        uploader = CloudinaryUploader()
        print(f"✅ Connected to Cloudinary cloud: {uploader.cloud_name}")

        # Test usage API
        usage = uploader.get_usage_stats()
        if usage:
            print(f"✅ API working - Storage used: {usage['storage_used_mb']:.2f} MB")
            uploader.print_usage_stats()
            return True
        else:
            print("⚠️  Connected but couldn't retrieve usage stats")
            return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Did you set Cloudinary credentials in .env?")
        print("   CLOUDINARY_CLOUD_NAME=your_cloud_name")
        print("   CLOUDINARY_API_KEY=your_api_key")
        print("   CLOUDINARY_API_SECRET=your_api_secret")
        return False


def test_single_file_upload():
    """Test 2: Upload a single test image."""
    print_test_header("Test 2: Single File Upload")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Extract a test resource
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        # Find first note with images
        test_resource = None
        for note in notes:
            if note.resources:
                for resource in note.resources:
                    if resource.mime and resource.mime.startswith('image/'):
                        test_resource = resource
                        break
                if test_resource:
                    break

        if not test_resource:
            print("❌ No image resources found in test file")
            return False

        # Extract resource to temp directory
        extractor = ResourceExtractor(output_dir="data/temp/cloudinary_test")
        resource_map = {}
        for note in notes:
            if note.resources:
                rm = extractor.extract_resources(note)
                resource_map.update(rm)
                if test_resource.hash in rm:
                    break

        test_path = resource_map[test_resource.hash].local_path

        print(f"\n📄 Test file: {Path(test_path).name}")
        print(f"   MIME type: {test_resource.mime}")
        print(f"   Size: {len(test_resource.data):,} bytes")

        # Upload to Cloudinary
        uploader = CloudinaryUploader()
        url = uploader.upload_file(
            test_path,
            mime_type=test_resource.mime,
            tags=['test', 'single-upload']
        )

        if url:
            print(f"\n✅ Upload successful!")
            print(f"   URL: {url}")
            print(f"\n🌐 Open in browser to verify:")
            print(f"   {url}")
            return True
        else:
            print(f"❌ Upload failed")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_upload():
    """Test 3: Upload multiple files in batch."""
    print_test_header("Test 3: Batch Upload")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Extract resources from test file
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        extractor = ResourceExtractor(output_dir="data/temp/cloudinary_test")
        all_resources = []

        for note in notes:
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

        if not all_resources:
            print("❌ No resources found")
            return False

        # Limit to first 5 resources for test
        test_resources = all_resources[:5]
        file_paths = [r.local_path for r in test_resources]
        mime_types = {r.local_path: r.mime for r in test_resources}

        print(f"\n📦 Uploading {len(test_resources)} files:")
        for r in test_resources:
            print(f"   - {Path(r.local_path).name} ({r.mime})")

        # Upload batch
        uploader = CloudinaryUploader()

        def progress_callback(current, total, file_path, url):
            status = "✅" if url else "❌"
            print(f"   [{current}/{total}] {status} {Path(file_path).name}")

        urls = uploader.upload_batch(
            file_paths,
            mime_types=mime_types,
            progress_callback=progress_callback
        )

        # Print statistics
        print()
        uploader.print_stats()

        success_count = sum(1 for url in urls.values() if url)
        print(f"\n✅ Uploaded {success_count}/{len(test_resources)} files")

        return success_count > 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resource_map_upload():
    """Test 4: Upload from ResourceExtractor output."""
    print_test_header("Test 4: Resource Map Upload")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "맛집.enex"  # Small file for quick test

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse and extract resources
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        if not notes:
            print("❌ No notes found in test file")
            return False

        # Find note with resources
        note_with_resources = None
        for note in notes:
            if note.resources:
                note_with_resources = note
                break

        if not note_with_resources:
            print("⚠️  No notes with resources found, using first note")
            note_with_resources = notes[0]

        print(f"\n📝 Note: {note_with_resources.title}")
        print(f"   Resources: {len(note_with_resources.resources)}")

        # Extract resources
        extractor = ResourceExtractor(output_dir="data/temp/cloudinary_test")
        resource_map = extractor.extract_resources(note_with_resources)

        if not resource_map:
            print("⚠️  No resources to upload")
            return True

        # Upload to Cloudinary
        uploader = CloudinaryUploader()

        def progress_callback(current, total, hash_val, url):
            status = "✅" if url else "❌"
            print(f"   [{current}/{total}] {status} {hash_val[:16]}...")

        print(f"\n🚀 Uploading {len(resource_map)} resources:")
        urls = uploader.upload_resource_map(
            resource_map,
            progress_callback=progress_callback
        )

        # Print statistics
        print()
        uploader.print_stats()

        success_count = sum(1 for url in urls.values() if url)
        print(f"\n✅ Uploaded {success_count}/{len(resource_map)} resources")

        # Show sample URLs
        if urls:
            print("\n📋 Sample URLs:")
            for i, (hash_val, url) in enumerate(list(urls.items())[:3], 1):
                if url:
                    print(f"   {i}. {url}")

        return success_count > 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_mime_types():
    """Test 5: Upload different MIME types."""
    print_test_header("Test 5: Upload All MIME Types")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Extract all resources
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        extractor = ResourceExtractor(output_dir="data/temp/cloudinary_test")

        # Collect resources by MIME type
        resources_by_mime = {}

        for note in notes:
            if not note.resources:
                continue

            resource_map = extractor.extract_resources(note)

            for resource in resource_map.values():
                mime = resource.mime or 'unknown'
                if mime not in resources_by_mime:
                    resources_by_mime[mime] = []
                resources_by_mime[mime].append(resource)

        print(f"\n📊 Found {len(resources_by_mime)} different MIME types:")
        for mime, resources in resources_by_mime.items():
            print(f"   - {mime}: {len(resources)} files")

        # Upload one sample from each MIME type
        uploader = CloudinaryUploader()
        print(f"\n🚀 Uploading samples from each MIME type:")

        for mime, resources in resources_by_mime.items():
            sample = resources[0]
            print(f"\n   📄 {mime}")
            print(f"      File: {Path(sample.local_path).name}")

            url = uploader.upload_file(
                sample.local_path,
                mime_type=mime,
                tags=['test', 'mime-type-test', mime.replace('/', '-')]
            )

            if url:
                print(f"      ✅ {url}")
            else:
                print(f"      ❌ Upload failed")

        # Print statistics
        print()
        uploader.print_stats()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  Cloudinary Upload Test Suite")
    print("="*80)

    tests = [
        ("Connection", test_connection),
        ("Single File Upload", test_single_file_upload),
        ("Batch Upload", test_batch_upload),
        ("Resource Map Upload", test_resource_map_upload),
        ("All MIME Types", test_all_mime_types),
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
        print("\n✨ Cloudinary integration is working!")
        print("   You can now upload all 1,574 resources to Cloudinary.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
