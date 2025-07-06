#!/usr/bin/env python3
#
# AIHub File List Parser Tests
# Unit tests for file tree parsing functionality
#
# - Tests tree structure parsing from AIHub API responses
# - Validates file size and key extraction
# - Tests path resolution and node operations
# - Mocks tree output for controlled testing
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.aihubkr.core.filelist_parser import AIHubResponseParser, sizeof_fmt


class TestAIHubResponseParser:
    """Test cases for AIHub response parser module."""

    def test_sizeof_fmt_basic(self):
        """Test basic size formatting."""
        assert sizeof_fmt(1024) == "1.0KiB"
        assert sizeof_fmt(1024 * 1024) == "1.0MiB"
        assert sizeof_fmt(1024 * 1024 * 1024) == "1.0GiB"
        assert sizeof_fmt(500) == "500.0B"

    def test_sizeof_fmt_ignore_float(self):
        """Test size formatting with ignore_float option."""
        assert sizeof_fmt(1024, ignore_float=True) == "1KiB"
        assert sizeof_fmt(1024 * 1024, ignore_float=True) == "1MiB"
        assert sizeof_fmt(500, ignore_float=True) == "500B"

    def test_sizeof_fmt_large_numbers(self):
        """Test size formatting with large numbers."""
        assert sizeof_fmt(1024 * 1024 * 1024 * 1024) == "1.0TiB"
        assert sizeof_fmt(1024 * 1024 * 1024 * 1024 * 1024) == "1.0PiB"

    def test_parse_tree_output_simple(self):
        """Test parsing simple tree output."""
        tree_output = """dataset_001
├── README.txt | 1.5KB | 1
└── data.txt | 2.3MB | 2"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None
        assert len(paths) == 3  # Root + 2 files

        # Check root
        assert str(tree.path) == "dataset_001"
        assert tree.file_key is None

        # Check files
        file_paths = [path for path, is_file, _, _ in paths if is_file]
        assert len(file_paths) == 2
        assert "README.txt" in file_paths[0]
        assert "data.txt" in file_paths[1]

    def test_parse_tree_output_with_directories(self):
        """Test parsing tree output with directory structure."""
        tree_output = """dataset_001
├── README.txt | 1.5KB | 1
├── data/
│   ├── train/
│   │   ├── file1.txt | 2.3MB | 2
│   │   └── file2.txt | 1.8MB | 3
│   └── test/
│       └── test.txt | 500KB | 4
└── metadata.json | 15KB | 5"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Count files and directories
        files = [path for path, is_file, _, _ in paths if is_file]
        directories = [path for path, is_file, _, _ in paths if not is_file]

        assert len(files) == 5  # 5 files
        assert len(directories) == 4  # dataset_001 (root) + data, train, test directories

        # Check file keys
        file_keys = [key for _, is_file, key, _ in paths if is_file and key is not None]
        assert file_keys == ["1", "2", "3", "4", "5"]

    def test_parse_tree_output_with_file_sizes(self):
        """Test parsing tree output with file size information."""
        tree_output = """dataset_001
├── small.txt | 1KB | 1
├── medium.txt | 1.5MB | 2
└── large.txt | 2.3GB | 3"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Check file size information
        for path, is_file, file_key, file_info in paths:
            if is_file and file_info is not None:
                display_size, min_size, max_size = file_info
                assert display_size > 0
                assert min_size > 0
                assert max_size > 0
                assert min_size <= display_size <= max_size

    def test_parse_tree_output_empty(self):
        """Test parsing empty tree output."""
        tree_output = ""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is None
        assert paths is None

    def test_parse_tree_output_single_file(self):
        """Test parsing tree output with single file."""
        tree_output = """dataset_001
└── single.txt | 1KB | 1"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None
        assert len(paths) == 2  # Root + 1 file

        # Check file
        file_paths = [path for path, is_file, _, _ in paths if is_file]
        assert len(file_paths) == 1
        assert "single.txt" in file_paths[0]

    def test_parse_tree_output_malformed(self):
        """Test parsing malformed tree output."""
        tree_output = """dataset_001
├── file1.txt | invalid | 1
└── file2.txt | 1KB | invalid"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        # Should handle malformed input gracefully
        assert tree is not None
        assert paths is not None

        # Files with invalid size/key should be skipped
        valid_files = [path for path, is_file, key, _ in paths if is_file and key is not None]
        assert len(valid_files) == 0

    def test_node_full_path(self):
        """Test node full path resolution."""
        parser = AIHubResponseParser()

        # Create a simple tree structure
        root = parser.Node(path=Path("dataset_001"))
        data_dir = parser.Node(path=Path("data"), parent=root)
        file_node = parser.Node(path=Path("file.txt"), parent=data_dir)

        # Test full path resolution
        assert str(root.full_path()) == "dataset_001"
        assert str(data_dir.full_path()) == "dataset_001/data"
        assert str(file_node.full_path()) == "dataset_001/data/file.txt"

    def test_node_to_dict(self):
        """Test node dictionary conversion."""
        parser = AIHubResponseParser()

        # Create a node with file information
        node = parser.Node(
            path=Path("test.txt"),
            file_key="1",
            file_display_size=1024
        )

        # Test dictionary conversion
        result = node.to_dict()
        assert "[1] test.txt (1.0KiB)" in result

    def test_node_to_dict_directory(self):
        """Test node dictionary conversion for directory."""
        parser = AIHubResponseParser()

        # Create a directory node
        node = parser.Node(path=Path("data"))
        child = parser.Node(path=Path("file.txt"), parent=node)
        node.children.append(child)

        # Test dictionary conversion
        result = node.to_dict()
        assert "data" in result
        assert isinstance(result["data"], list)

    def test_parse_tree_output_complex_structure(self):
        """Test parsing complex tree structure."""
        tree_output = """dataset_001
├── README.txt | 1.5KB | 1
├── config/
│   ├── settings.json | 2KB | 2
│   └── defaults.yaml | 1KB | 3
├── data/
│   ├── raw/
│   │   ├── input1.csv | 5MB | 4
│   │   └── input2.csv | 3MB | 5
│   ├── processed/
│   │   └── output.csv | 10MB | 6
│   └── backup/
│       └── archive.zip | 50MB | 7
└── docs/
    ├── manual.pdf | 2MB | 8
    └── examples/
        ├── example1.py | 5KB | 9
        └── example2.py | 3KB | 10"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Count files and directories
        files = [path for path, is_file, _, _ in paths if is_file]
        directories = [path for path, is_file, _, _ in paths if not is_file]

        assert len(files) == 10  # 10 files
        assert len(directories) == 8  # 8 directories (dataset_001 + config, data, raw, processed, backup, docs, examples)

        # Check total file size
        total_size = sum(
            file_info[0] for _, is_file, _, file_info in paths
            if is_file and file_info is not None
        )
        assert total_size > 0

        # Check file keys are sequential
        file_keys = [key for _, is_file, key, _ in paths if is_file and key is not None]
        expected_keys = [str(i) for i in range(1, 11)]
        assert file_keys == expected_keys

    def test_parse_tree_output_with_special_characters(self):
        """Test parsing tree output with special characters in filenames."""
        tree_output = """dataset_001
├── file with spaces.txt | 1KB | 1
├── file-with-dashes.txt | 2KB | 2
├── file_with_underscores.txt | 3KB | 3
└── file.with.dots.txt | 4KB | 4"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Check that special characters are preserved
        file_paths = [path for path, is_file, _, _ in paths if is_file]
        assert any("file with spaces" in path for path in file_paths)
        assert any("file-with-dashes" in path for path in file_paths)
        assert any("file_with_underscores" in path for path in file_paths)
        assert any("file.with.dots" in path for path in file_paths)


class TestAIHubResponseParserEdgeCases:
    """Test edge cases for AIHub response parser."""

    def test_parse_tree_output_deep_nesting(self):
        """Test parsing tree output with deep nesting."""
        tree_output = """dataset_001
└── level1/
    └── level2/
        └── level3/
            └── level4/
                └── level5/
                    └── deep_file.txt | 1KB | 1"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Check deep nesting is handled
        files = [path for path, is_file, _, _ in paths if is_file]
        assert len(files) == 1
        assert "deep_file.txt" in files[0]
        assert "level5" in files[0]

    def test_parse_tree_output_large_file_sizes(self):
        """Test parsing tree output with large file sizes."""
        tree_output = """dataset_001
├── small.txt | 1B | 1
├── medium.txt | 1KB | 2
├── large.txt | 1MB | 3
├── huge.txt | 1GB | 4
└── massive.txt | 1TB | 5"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Check size parsing for different units
        for path, is_file, _, file_info in paths:
            if is_file and file_info is not None:
                display_size, min_size, max_size = file_info
                assert display_size > 0
                assert min_size >= 0  # min_size can be 0 for very small files
                assert max_size > 0

    def test_parse_tree_output_mixed_content(self):
        """Test parsing tree output with mixed file and directory content."""
        tree_output = """dataset_001
├── file1.txt | 1KB | 1
├── empty_dir/
├── file2.txt | 2KB | 2
├── dir_with_files/
│   ├── nested_file.txt | 3KB | 3
│   └── another_nested.txt | 4KB | 4
└── file3.txt | 5KB | 5"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Count files and directories
        files = [path for path, is_file, _, _ in paths if is_file]
        directories = [path for path, is_file, _, _ in paths if not is_file]

        assert len(files) == 5  # 5 files
        assert len(directories) == 3  # 3 directories (dataset_001 + empty_dir, dir_with_files)

        # Check empty directory is handled
        empty_dirs = [path for path, is_file, _, _ in paths if not is_file and "empty_dir" in path]
        assert len(empty_dirs) == 1


class TestAIHubResponseParserIntegration:
    """Integration tests for AIHub response parser."""

    def test_parser_with_real_aihub_format(self):
        """Test parser with realistic AIHub API response format."""
        # This simulates a real AIHub API response
        tree_output = """UTF-8
output normally
modify the character information
dataset_001
├── README.txt | 1.5KB | 1
├── data/
│   ├── train/
│   │   ├── file1.txt | 2.3MB | 2
│   │   └── file2.txt | 1.8MB | 3
│   └── test/
│       └── test.txt | 500KB | 4
└── metadata.json | 15KB | 5"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Verify the structure
        assert str(tree.path) == "dataset_001"

        # Check all files are present
        file_paths = [path for path, is_file, _, _ in paths if is_file]
        expected_files = [
            "README.txt",
            "file1.txt",
            "file2.txt",
            "test.txt",
            "metadata.json"
        ]

        for expected_file in expected_files:
            assert any(expected_file in path for path in file_paths)

        # Check file keys
        file_keys = [key for _, is_file, key, _ in paths if is_file and key is not None]
        assert file_keys == ["1", "2", "3", "4", "5"]

    def test_parser_performance(self):
        """Test parser performance with large tree structure."""
        # Generate a large tree structure
        tree_lines = ["large_dataset"]

        # Add 100 files in a nested structure
        for i in range(100):
            level = i % 5 + 1
            indent = "    " * level
            tree_lines.append(f"{indent}└── file_{i:03d}.txt | 1KB | {i+1}")

        tree_output = "\n".join(tree_lines)

        parser = AIHubResponseParser()

        # Time the parsing
        import time
        start_time = time.time()
        tree, paths = parser.parse_tree_output(tree_output)
        end_time = time.time()

        parsing_time = end_time - start_time

        assert tree is not None
        assert paths is not None
        assert len(paths) == 101  # Root + 100 files

        # Parsing should be fast (less than 1 second)
        assert parsing_time < 1.0, f"Parsing took too long: {parsing_time:.3f}s"

        print(f"Parsed {len(paths)} nodes in {parsing_time:.3f} seconds")

    def test_gui_display_issue_fix(self):
        """Test that tree characters are not included in file paths for GUI display."""
        # This test specifically addresses the GUI issue where filenames had "└──" prefix
        tree_output = """dataset_001
├── README.txt | 1.5KB | 1
├── data/
│   ├── train/
│   │   ├── file1.txt | 2.3MB | 2
│   │   └── file2.txt | 1.8MB | 3
│   └── test/
│       └── test.txt | 500KB | 4
└── metadata.json | 15KB | 5"""

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(tree_output)

        assert tree is not None
        assert paths is not None

        # Check that file paths don't contain tree characters
        file_paths = [path for path, is_file, _, _ in paths if is_file]

        expected_paths = [
            "dataset_001/README.txt",
            "dataset_001/file1.txt",
            "dataset_001/file2.txt",
            "dataset_001/test.txt",
            "dataset_001/metadata.json"
        ]

        assert len(file_paths) == len(expected_paths)

        for path in file_paths:
            # Verify no tree characters are present
            assert "├" not in path, f"Tree character '├' found in path: {path}"
            assert "└" not in path, f"Tree character '└' found in path: {path}"
            assert "─" not in path, f"Tree character '─' found in path: {path}"
            assert "│" not in path, f"Tree character '│' found in path: {path}"

            # Verify the path is clean and matches expected format
            assert path in expected_paths, f"Unexpected path: {path}"

        print("✅ GUI display issue fixed: All file paths are clean without tree characters")
