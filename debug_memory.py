#!/usr/bin/env python3

import sys
import tempfile
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")

from memory.memory import ArchiveMemory


def debug_archive_memory():
    print("=== Debugging ArchiveMemory ===")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        archive_file = tmp_path / f"test_archive_{uuid.uuid4()}.json"

        print(f"Temporary archive file: {archive_file}")
        print(f"File exists before creation: {archive_file.exists()}")

        # Create ArchiveMemory like in the fixture
        archive = ArchiveMemory(
            archive_file=archive_file, load_existing=False, ignore_existing_file=True
        )

        print(f"Archive file after creation: {archive.archive_file}")
        print(f"File exists after creation: {archive_file.exists()}")
        print(f"Archive size: {archive.size()}")
        print(f"Archive entries count: {len(archive._entries)}")

        # Try with default parameters
        print("\n=== Testing default ArchiveMemory() ===")
        default_archive = ArchiveMemory()
        print(f"Default archive file: {default_archive.archive_file}")
        print(f"Default file exists: {default_archive.archive_file.exists()}")
        print(f"Default archive size: {default_archive.size()}")


if __name__ == "__main__":
    debug_archive_memory()
