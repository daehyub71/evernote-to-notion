#!/usr/bin/env python3
"""Test script for resource extraction and handling.

This script tests:
1. Resource extraction from ENEX files
2. Image optimization and validation
3. Document validation
4. Statistics and reporting
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.parsers.enex_parser import EnexParser
from app.resources.resource_extractor import ResourceExtractor
from app.resources.image_handler import ImageHandler
from app.resources.document_handler import DocumentHandler

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


def test_single_file_extraction():
    """Test 1: Extract resources from a single ENEX file."""
    print_test_header("Test 1: Single File Resource Extraction")

    # Get ENEX source directory from env
    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse ENEX file
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        print(f"📂 Parsed {len(notes)} notes from {test_file.name}")

        # Extract resources
        extractor = ResourceExtractor(output_dir="data/temp/test1")
        total_resources = 0

        for note in notes:
            if note.resources:
                print(f"\n📝 Note: {note.title}")
                print(f"   Resources: {len(note.resources)}")

                resource_map = extractor.extract_resources(note)
                total_resources += len(resource_map)

                # Show first 3 resources
                for i, (hash_val, resource) in enumerate(list(resource_map.items())[:3], 1):
                    print(f"   [{i}] {resource.filename or 'unnamed'} ({resource.mime})")
                    print(f"       Hash: {hash_val[:16]}...")
                    print(f"       Size: {len(resource.data):,} bytes")
                    print(f"       Saved: {resource.local_path}")

        # Print statistics
        print()
        extractor.print_stats()

        print(f"\n✅ Successfully extracted {total_resources} resources")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_processing():
    """Test 2: Image optimization and validation."""
    print_test_header("Test 2: Image Processing")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse and extract
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        extractor = ResourceExtractor(output_dir="data/temp/test2")
        handler = ImageHandler()

        images_processed = 0

        for note in notes:
            if not note.resources:
                continue

            resource_map = extractor.extract_resources(note)

            for resource in resource_map.values():
                if not resource.mime or not resource.mime.startswith('image/'):
                    continue

                print(f"\n🖼️  Processing image: {resource.filename or 'unnamed'}")
                print(f"   MIME: {resource.mime}")

                # Get image info
                info = handler.get_image_info(resource.local_path)
                if info:
                    print(f"   Size: {info['width']}x{info['height']}")
                    print(f"   Format: {info['format']}")
                    print(f"   File size: {info['file_size']:,} bytes")

                    # Check if needs optimization
                    if info['needs_resize']:
                        print(f"   ⚠️  Image too large, optimizing...")
                        optimized = handler.optimize(resource.local_path, max_size=1500)
                        new_info = handler.get_image_info(optimized)
                        print(f"   ✅ Optimized to {new_info['width']}x{new_info['height']}")

                # Validate image
                is_valid = handler.validate_image(resource.local_path)
                print(f"   Valid: {'✅' if is_valid else '❌'}")

                images_processed += 1

                if images_processed >= 5:  # Limit to first 5 images
                    break

            if images_processed >= 5:
                break

        print(f"\n✅ Processed {images_processed} images")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_validation():
    """Test 3: Document validation."""
    print_test_header("Test 3: Document Validation")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_file = Path(source_dir) / "IT트렌드.enex"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    try:
        # Parse and extract
        parser = EnexParser(str(test_file))
        notes = list(parser.parse())

        extractor = ResourceExtractor(output_dir="data/temp/test3")
        doc_handler = DocumentHandler()

        documents_found = 0
        pdfs_found = 0

        for note in notes:
            if not note.resources:
                continue

            resource_map = extractor.extract_resources(note)

            for resource in resource_map.values():
                # Check for documents
                if resource.mime and ('pdf' in resource.mime.lower() or
                                     'document' in resource.mime.lower() or
                                     'msword' in resource.mime.lower()):

                    print(f"\n📄 Document: {resource.filename or 'unnamed'}")
                    print(f"   MIME: {resource.mime}")

                    # Get document info
                    info = doc_handler.get_document_info(resource.local_path)
                    if info:
                        print(f"   Extension: {info['extension']}")
                        print(f"   File size: {info['file_size_mb']:.2f} MB")
                        print(f"   Detected MIME: {info['detected_mime']}")

                        if info['is_pdf']:
                            print(f"   ✅ Valid PDF")
                            pdfs_found += 1
                        elif info['is_office']:
                            print(f"   ✅ Valid Office document")

                    documents_found += 1

        print(f"\n✅ Found {documents_found} documents ({pdfs_found} PDFs)")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_extraction():
    """Test 4: Batch extraction from multiple files."""
    print_test_header("Test 4: Batch Extraction from Multiple Files")

    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    test_dir = Path(source_dir)

    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False

    try:
        enex_files = list(test_dir.glob("*.enex"))
        print(f"📂 Found {len(enex_files)} ENEX files")

        extractor = ResourceExtractor(output_dir="data/temp/test4")
        total_notes = 0
        total_resources = 0

        for enex_file in enex_files[:3]:  # Limit to first 3 files
            print(f"\n📄 Processing: {enex_file.name}")

            parser = EnexParser(str(enex_file))
            notes = list(parser.parse())

            print(f"   Notes: {len(notes)}")

            for note in notes:
                if note.resources:
                    resource_map = extractor.extract_resources(note)
                    total_resources += len(resource_map)

            total_notes += len(notes)

        # Print statistics
        print()
        extractor.print_stats()

        print(f"\n✅ Processed {total_notes} notes with {total_resources} resources")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_extraction():
    """Test 5: Full extraction from all ENEX files."""
    print_test_header("Test 5: Full Extraction (All 1,574 Resources)")

    # Get ENEX source directory from env
    import os
    from dotenv import load_dotenv
    load_dotenv()

    source_dir = os.getenv('ENEX_SOURCE_DIR', str(project_root / 'data' / 'test'))
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"❌ Source directory not found: {source_dir}")
        print("   Set ENEX_SOURCE_DIR in .env file")
        return False

    try:
        enex_files = list(source_path.glob("*.enex"))
        print(f"📂 Found {len(enex_files)} ENEX files in {source_dir}")
        print(f"\n⚠️  This will extract ALL resources from {len(enex_files)} files...")

        extractor = ResourceExtractor(output_dir="data/temp/full_extraction")
        total_notes = 0
        total_files = 0

        print("\n🔄 Extracting resources...")

        for i, enex_file in enumerate(enex_files, 1):
            print(f"[{i}/{len(enex_files)}] {enex_file.name}")

            try:
                parser = EnexParser(str(enex_file))
                notes = list(parser.parse())

                for note in notes:
                    if note.resources:
                        extractor.extract_resources(note)

                total_notes += len(notes)
                total_files += 1

            except Exception as e:
                logger.error(f"Failed to process {enex_file.name}: {e}")

        # Print statistics
        print()
        extractor.print_stats()

        print(f"\n✅ Processed {total_files} files, {total_notes} notes")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  Resource Extraction Test Suite")
    print("="*80)

    tests = [
        ("Single File Extraction", test_single_file_extraction),
        ("Image Processing", test_image_processing),
        ("Document Validation", test_document_validation),
        ("Batch Extraction", test_batch_extraction),
        ("Full Extraction", test_full_extraction),
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
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
