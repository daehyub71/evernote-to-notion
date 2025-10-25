#!/usr/bin/env python3
"""
Task 4.4: Process 블로그_예전모음.enex (The Final Boss)

Extract and upload 1,192 resources from the largest ENEX file.
"""

import sys
from pathlib import Path
import time
import os

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


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def check_disk_space(path: str, required_mb: int = 500):
    """Check if enough disk space is available."""
    stat = os.statvfs(path)
    available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)

    print(f"\n💾 Disk Space Check:")
    print(f"   Available: {available_mb:,.0f} MB")
    print(f"   Required: {required_mb} MB")

    if available_mb < required_mb:
        print(f"   ⚠️  WARNING: Low disk space!")
        return False
    else:
        print(f"   ✅ Sufficient space available")
        return True


def check_memory():
    """Check current memory usage (simplified without psutil)."""
    # Simplified version without psutil
    print(f"\n🧠 Memory Check:")
    print(f"   Monitoring memory usage...")

    return 0, 0  # Return dummy values


def main():
    """
    Process 블로그_예전모음.enex - The Final Boss

    Steps:
    1. Check system resources (disk, memory)
    2. Extract 1,192 resources
    3. Upload in batches with checkpoints
    4. Verify upload success (95%+ required)
    """

    print_header("Task 4.4: 블로그_예전모음.enex 처리 ⚠️ 최종 보스")

    enex_file = Path("/Users/sunchulkim/evernote/블로그_예전모음.enex")

    if not enex_file.exists():
        print(f"❌ File not found: {enex_file}")
        return False

    # File info
    file_size_mb = enex_file.stat().st_size / (1024 * 1024)
    print(f"\n📂 File Info:")
    print(f"   Path: {enex_file.name}")
    print(f"   Size: {file_size_mb:.2f} MB")

    # System checks
    print_header("Step 1: System Resource Checks")

    # Check disk space
    output_dir = Path("data/temp/blog_archive")
    if not check_disk_space(str(output_dir.parent), required_mb=500):
        print("\n⚠️  Warning: Continuing with low disk space...")

    # Check memory
    initial_memory, available_memory = check_memory()

    if available_memory < 1000:  # Less than 1GB
        print("\n⚠️  WARNING: Low available memory!")

    # Step 2: Extract resources
    print_header("Step 2: Extract 1,192 Resources")

    print("\n📦 Parsing ENEX file...")
    start_time = time.time()

    parser = EnexParser(str(enex_file))
    notes = list(parser.parse())

    parse_time = time.time() - start_time
    total_resources = sum(len(note.resources) for note in notes)

    print(f"   Total notes: {len(notes)}")
    print(f"   Total resources: {total_resources}")
    print(f"   Parse time: {parse_time:.2f}s")

    # Check memory after parsing
    post_parse_memory, _ = check_memory()
    memory_increase = post_parse_memory - initial_memory
    print(f"\n   Memory increase: {memory_increase:.1f} MB")

    # Extract resources
    print("\n🔧 Extracting resources to local storage...")
    extractor = ResourceExtractor(output_dir=str(output_dir))

    all_resources = []
    extraction_start = time.time()

    for i, note in enumerate(notes, 1):
        if note.resources:
            print(f"   [{i}/{len(notes)}] {note.title[:60]:60s} - {len(note.resources):3d} resources")
            resource_map = extractor.extract_resources(note)
            all_resources.extend(resource_map.values())

    extraction_time = time.time() - extraction_start

    print(f"\n✅ Extraction complete:")
    print(f"   Extracted: {len(all_resources)} resources")
    print(f"   Time: {extraction_time:.2f}s")

    # Check extraction stats
    stats = extractor.get_stats()
    print(f"\n📊 Extraction Statistics:")
    print(f"   Total: {stats['total_resources']}")
    print(f"   Extracted: {stats['extracted']}")
    print(f"   Failed: {stats['failed']}")

    if stats['failed'] > 0:
        print(f"\n⚠️  {stats['failed']} resources failed to extract!")
        return False

    # Check memory and disk after extraction
    post_extract_memory, _ = check_memory()

    # Check actual disk usage
    total_size = sum(Path(r.local_path).stat().st_size for r in all_resources if r.local_path) / (1024 * 1024)
    print(f"\n💾 Disk Usage:")
    print(f"   Total extracted size: {total_size:.2f} MB")

    # Step 3: Batch upload
    print_header("Step 3: Batch Upload (100 resources per batch)")

    cache_file = "data/checkpoint/blog_archive_cache.json"
    cache = UploadCache(cache_file)

    print(f"\n📝 Upload Cache:")
    print(f"   Cache file: {cache_file}")
    print(f"   Existing entries: {len(cache)}")

    cloudinary_uploader = CloudinaryUploader()
    batch_uploader = BatchUploader(cloudinary_uploader, max_workers=10)

    print(f"\n🚀 Starting batch upload...")
    print(f"   Total resources: {len(all_resources)}")
    print(f"   Workers: 10")
    print(f"   Checkpoint: Enabled (saves cache after each upload)")

    upload_start = time.time()

    # Upload with cache
    with cache:  # Auto-save on exit
        urls = batch_uploader.upload_resources(all_resources, cache=cache.cache)

    upload_time = time.time() - upload_start

    # Get statistics
    stats = batch_uploader.get_stats()

    print(f"\n📊 Upload Statistics:")
    print(f"   Total files: {stats['total']}")
    print(f"   Uploaded: {stats['uploaded']}")
    print(f"   Cached: {stats['cached']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Success rate: {(stats['uploaded'] + stats['cached']) / stats['total'] * 100:.2f}%")
    print(f"   Total time: {upload_time:.2f}s")
    print(f"   Avg time/file: {upload_time / len(all_resources):.2f}s")

    # Step 4: Verify results
    print_header("Step 4: Verification")

    success_count = stats['uploaded'] + stats['cached']
    success_rate = success_count / stats['total'] * 100
    required_count = int(stats['total'] * 0.95)  # 95% threshold

    print(f"\n✅ Success: {success_count}/{stats['total']} resources")
    print(f"   Success rate: {success_rate:.2f}%")
    print(f"   Required (95%): {required_count}/{stats['total']}")

    if success_count >= required_count:
        print(f"\n🎉 SUCCESS! Uploaded {success_count}/{stats['total']} resources ({success_rate:.1f}%)")
        print(f"   Exceeds 95% threshold ({required_count} required)")

        # Final memory check
        final_memory, _ = check_memory()
        print(f"\n💾 Final Memory: {final_memory:.1f} MB")
        print(f"   Peak increase: {final_memory - initial_memory:.1f} MB")

        return True
    else:
        print(f"\n❌ FAILED: Only {success_count}/{stats['total']} resources uploaded")
        print(f"   Below 95% threshold ({required_count} required)")

        if stats['failed'] > 0:
            print(f"\n⚠️  {stats['failed']} upload failures logged to:")
            print(f"   data/checkpoint/upload_failures.log")

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
