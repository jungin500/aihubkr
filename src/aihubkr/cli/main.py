#!/usr/bin/env python3
#
# AIHub CLI Main Module
# Command-line interface for AIHub dataset operations
#
# - Provides download, list, and help functionality
# - Uses API key authentication instead of username/password
# - Modern subcommand interface for better user experience
#
# @author Jung-In An <ji5489@gmail.com>
# @with Claude Sonnet 4 (Cutoff 2025/06/16)

import argparse
import os
import re
import sys
import tarfile
from typing import Any, Dict

from ..core.auth import AIHubAuth
from ..core.config import AIHubConfig
from ..core.downloader import AIHubDownloader, DownloadStatus
from ..core.filelist_parser import AIHubResponseParser, sizeof_fmt
from prettytable import PrettyTable


def parse_arguments() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="AIHub Dataset Downloader CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                                    # List all available datasets
  %(prog)s files DATASET_KEY                       # List files in a dataset
  %(prog)s download DATASET_KEY                    # Download all files in a dataset
  %(prog)s download DATASET_KEY --file-key 1,2,3   # Download specific files
  %(prog)s help                                    # Show API usage information
        """
    )

    # Global options
    parser.add_argument(
        "--api-key",
        help="AIHub API key (can also use AIHUB_APIKEY environment variable)"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for downloads (default: current directory)"
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List all available datasets",
        description="List all available datasets and export to CSV"
    )

    # Files command
    files_parser = subparsers.add_parser(
        "files",
        help="List files in a specific dataset",
        description="Show file tree structure and sizes for a dataset"
    )
    files_parser.add_argument(
        "dataset_key",
        help="Dataset key to list files for"
    )

    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download a dataset",
        description="Download dataset files with progress tracking"
    )
    download_parser.add_argument(
        "dataset_key",
        help="Dataset key to download"
    )
    download_parser.add_argument(
        "--file-key",
        default="all",
        help="File key(s) to download, comma-separated (default: all files)"
    )
    download_parser.add_argument(
        "--check-space",
        action="store_true",
        help="Check available disk space before downloading"
    )

    # Help command
    help_parser = subparsers.add_parser(
        "help",
        help="Show API usage information",
        description="Display AIHub API usage information"
    )

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return vars(parser.parse_args())


def print_usage() -> None:
    """Print usage information from AIHub API."""
    import requests

    manual_url = "https://api.aihub.or.kr/info/api.do"
    try:
        manual = requests.get(manual_url).text
        print("AIHub API Usage Information:")
        print("=" * 50)

        # Extract and display usage information
        # This is a simplified version - you can enhance parsing as needed
        print(manual)
    except Exception as e:
        print(f"Failed to fetch usage information: {e}")
        print("Please visit https://api.aihub.or.kr/info/api.do for detailed usage information.")


def list_datasets(downloader: AIHubDownloader) -> None:
    """List all available datasets."""
    print("Fetching dataset list...")
    datasets = downloader.get_dataset_info()
    if datasets:
        table = PrettyTable(
            field_names=["Dataset Key", "Dataset Name"],
            align="l",
        )

        for dataset_id, dataset_name in datasets:
            table.add_row([dataset_id, dataset_name])

        print(table)

        # Export to CSV
        csv_filename = "aihub_datasets.csv"
        downloader.export_dataset_list_to_csv(datasets, csv_filename)
        print(f"Dataset list exported to {csv_filename}")
    else:
        print("Failed to fetch dataset information.")


def list_file_tree(downloader: AIHubDownloader, dataset_key: str) -> None:
    """List file tree structure for a specific dataset."""
    print(f"Fetching file tree for dataset: {dataset_key}")
    file_tree = downloader.get_file_tree(dataset_key)
    if not file_tree:
        print("Failed to fetch file tree.")
        return

    # Parse file tree
    parser = AIHubResponseParser()
    tree, paths = parser.parse_tree_output(file_tree)
    if not paths:
        print("No files found.")
        return

    table = PrettyTable(
        field_names=["File Key", "File Path", "File Size"],
        align="l",
    )
    total_file_size = 0
    for idx, (path, is_file, file_key, file_info) in enumerate(paths):
        if is_file:
            (file_display_size, file_min_size, file_max_size) = file_info
            table.add_row(
                [file_key, path, sizeof_fmt(file_display_size, ignore_float=True)],
                divider=idx == len(paths) - 1)
            total_file_size += file_display_size
        else:
            table.add_row(["-", path, "-"], divider=idx == len(paths) - 1)

    table.add_row(["", "Total File Size", sizeof_fmt(total_file_size)])

    print(table)


def download_dataset(
    downloader: AIHubDownloader, dataset_key: str, file_keys: str, output_dir: str = "."
) -> None:
    """Download a dataset."""
    print(f"Downloading dataset: {dataset_key}")
    print(f"File keys: {file_keys}")
    print(f"Output directory: {output_dir}")

    # Check for available disk space before downloading
    file_tree = downloader.get_file_tree(dataset_key)
    if not file_tree:
        print(f"Failed to fetch file tree for dataset {dataset_key}")
        return

    parser = AIHubResponseParser()
    tree, paths = parser.parse_tree_output(file_tree)
    if not paths:
        print(f"No files found for dataset {dataset_key}")
        return

    file_paths = [item for item in paths if item[1]]
    file_db = {}

    min_total_size = 0
    max_total_size = 0
    for row, (path, _, file_key, (file_display_size, file_min_size, file_max_size)) in enumerate(file_paths):
        file_db[file_key] = (path, file_display_size, file_min_size, file_max_size)

    for filekey in file_keys.split(","):
        if filekey == "all":
            min_total_size = sum([file_db[key][2] for key in file_db])
            max_total_size = sum([file_db[key][3] for key in file_db])
            break
        if filekey not in file_db:
            print(f"File key {filekey} not found.")
            return
        min_total_size += file_db[filekey][2]
        max_total_size += file_db[filekey][3]

    # Check for available disk space
    fstat = os.statvfs(output_dir)
    available_space = fstat.f_frsize * fstat.f_bavail

    print(f"Estimated download size: {sizeof_fmt(min_total_size)} ~ {sizeof_fmt(max_total_size)}")
    print(f"Free disk space: {sizeof_fmt(available_space)}")

    if max_total_size > available_space:
        print("Insufficient disk space.")
        return

    # Use the new download method with size checking
    download_status = downloader.download_dataset_with_size_check(
        dataset_key, file_keys, output_dir, max_total_size
    )

    if download_status == DownloadStatus.SUCCESS:
        # Continue with processing if download was successful
        tar_file = os.path.join(output_dir, "download.tar")

        # Extract the tar file
        with tarfile.open(tar_file, "r") as tar:
            tar.extractall(path=output_dir)

        print("Merging file parts...")
        # Merge parts in all subdirectories
        for dirpath, dirnames, filenames in os.walk(output_dir):
            if any(re.search(r".*\.part[0-9]+", filename, re.IGNORECASE) for filename in filenames):
                # Find all unique prefixes of part files
                part_files = [f for f in filenames if re.search(r".*\.part[0-9]+", f, re.IGNORECASE)]
                prefixes = set(f.rsplit(".part", 1)[0] for f in part_files)

                for prefix in prefixes:
                    print(f"Merging {prefix} in {dirpath}")
                    parts = sorted([f for f in part_files if f.startswith(prefix)],
                                   key=lambda x: int(x.rsplit(".part", 1)[1]))

                    with open(os.path.join(dirpath, prefix), "wb") as outfile:
                        for part in parts:
                            with open(os.path.join(dirpath, part), "rb") as infile:
                                outfile.write(infile.read())

                    # Remove the part files
                    for part in parts:
                        os.remove(os.path.join(dirpath, part))

        print("Merging completed.")
        # Clean up: remove the original tar file
        os.remove(tar_file)
        status = DownloadStatus.SUCCESS
    else:
        status = download_status

    print(status.get_message())

    if status == DownloadStatus.PRIVILEGE_ERROR:
        print("Please visit the AIHub website and accept the terms before downloading.")
    elif status == DownloadStatus.AUTHENTICATION_ERROR:
        print("Please check your API key and try again.")
    elif status == DownloadStatus.FILE_NOT_FOUND:
        print("Please check the dataset key and file keys.")
    elif status == DownloadStatus.NETWORK_ERROR:
        print("Please check your internet connection and try again.")
    elif status == DownloadStatus.INSUFFICIENT_DISK_SPACE:
        print("Please free up space and try again.")


def prompt_api_key() -> str:
    """Prompt user for API key."""
    from getpass import getpass

    while True:
        api_key = getpass(prompt="Enter your AIHub API key: ").strip()
        if not api_key:
            print("API key cannot be empty.")
            continue
        return api_key


def main() -> None:
    args = parse_arguments()

    # Handle help command
    if args["command"] == "help":
        print_usage()
        return

    # Get API key
    api_key = args.get("api_key")
    if not api_key:
        # Try to get from environment variable
        api_key = os.environ.get("AIHUB_APIKEY")

    if not api_key:
        # Try to load from saved credentials
        auth = AIHubAuth()
        api_key = auth.load_credentials()

    if not api_key:
        # Prompt user for API key
        api_key = prompt_api_key()
        auth = AIHubAuth(api_key)
        auth.save_credential()
    else:
        auth = AIHubAuth(api_key)

    # Validate API key
    if not auth.validate_api_key():
        print("Invalid API key. Please check your API key and try again.")
        return

    # Get authentication headers
    auth_headers = auth.get_auth_headers()
    if not auth_headers:
        print("Failed to get authentication headers.")
        return

    # Create downloader with authentication
    downloader = AIHubDownloader(auth_headers)

    # Handle different commands
    if args["command"] == "list":
        list_datasets(downloader)
    elif args["command"] == "files":
        list_file_tree(downloader, args["dataset_key"])
    elif args["command"] == "download":
        file_keys = args.get("file_key", "all")
        output_dir = args.get("output_dir", ".")
        download_dataset(downloader, args["dataset_key"], file_keys, output_dir)
    else:
        print("Invalid command. Use --help for usage information.")


if __name__ == "__main__":
    main()
