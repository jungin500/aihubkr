# core/file_utils.py

import os
import shutil
from typing import List
import tarfile


def merge_part_files(directory: str) -> None:
    """
    Merge part files in the given directory.

    Args:
        directory (str): The directory containing part files
    """
    for root, _, files in os.walk(directory):
        part_files = sorted([f for f in files if f.endswith(".part")])
        if not part_files:
            continue

        base_name = os.path.splitext(part_files[0])[0]
        merged_file = os.path.join(root, base_name)

        with open(merged_file, "wb") as outfile:
            for part in part_files:
                part_path = os.path.join(root, part)
                with open(part_path, "rb") as infile:
                    shutil.copyfileobj(infile, outfile)

        # Remove part files after successful merge
        for part in part_files:
            os.remove(os.path.join(root, part))


def extract_tar(tar_file: str, output_dir: str) -> None:
    """
    Extract a tar file to the specified output directory.

    Args:
        tar_file (str): Path to the tar file
        output_dir (str): Directory to extract the contents
    """
    with tarfile.open(tar_file, "r") as tar:
        tar.extractall(path=output_dir)


def clean_up_download(tar_file: str) -> None:
    """
    Remove the downloaded tar file after extraction.

    Args:
        tar_file (str): Path to the tar file
    """
    os.remove(tar_file)


def get_downloaded_files(directory: str) -> List[str]:
    """
    Get a list of fully downloaded files in the directory.

    Args:
        directory (str): The directory to check

    Returns:
        List[str]: List of fully downloaded file names
    """
    return [f for f in os.listdir(directory) if not f.endswith(".part")]
