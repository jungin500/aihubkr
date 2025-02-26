import csv
import os
import re
import subprocess
import tarfile
from typing import Dict, List, Optional, Tuple

import requests
from tqdm import tqdm


class AIHubDownloader:
    BASE_URL = "https://api.aihub.or.kr"
    BASE_DOWNLOAD_URL = f"{BASE_URL}/down"
    BASE_FILETREE_URL = f"{BASE_URL}/info"
    DATASET_URL = f"{BASE_URL}/info/dataset.do"

    def __init__(self, auth_headers: Dict[str, str]):
        self.auth_headers = auth_headers

    def _process_response(
        self, response: requests.Response
    ) -> Tuple[bool, Optional[str]]:
        """Process the response and determine if it's a success."""
        if response.status_code == 200 or response.status_code == 502:
            content = response.text

            # Remove the first three lines if they match the specified pattern
            lines = content.split("\n")
            if len(lines) >= 3:
                if (
                    "UTF-8" in lines[0]
                    and "output normally" in lines[1]
                    and "modify the character information" in lines[2]
                ):
                    lines = lines[3:]

            # Find and format the notice section
            notice_start = -1
            notice_end = -1
            for i, line in enumerate(lines):
                if re.search(r"={3,}\s*공지\s*사항\s*={3,}", line, re.IGNORECASE):
                    notice_start = i
                elif notice_start != -1 and re.match(r"={3,}", line):
                    notice_end = i
                    break

            if notice_start != -1 and notice_end != -1:
                notice = "\n".join(lines[notice_start + 1: notice_end])
                if notice.strip() == "":
                    lines = lines[:notice_start] + lines[notice_end + 2:]
                else:
                    formatted_notice = f"Notice:\n{notice}\n"
                    lines = (
                        lines[:notice_start]
                        + [formatted_notice]
                        + lines[notice_end + 2:]
                    )

            content = "\n".join(lines)
            return True, content.strip()
        else:
            return False, None

    def get_file_tree(self, dataset_key: str) -> Optional[str]:
        """Fetch file tree structure for a specific dataset."""
        url = f"{self.BASE_FILETREE_URL}/{dataset_key}.do"
        response = requests.get(url)  # No auth headers
        success, content = self._process_response(response)
        if success:
            return content
        else:
            print(f"Failed to fetch file tree. Status code: {response.status_code}")
            return None

    def process_dataset_list(self, content: str) -> List[Tuple[str, str]]:
        """Process the dataset list content."""
        lines = content.split("\n")

        # Remove header and footer lines
        start = next((i for i, line in enumerate(lines) if "=" in line), 0)
        end = next(
            (i for i in range(len(lines) - 1, -1, -1) if "=" in lines[i]), len(lines)
        )

        dataset_lines = lines[start + 1: end]

        datasets = []
        for line in dataset_lines:
            parts = line.split(",", 1)
            if len(parts) == 2:
                datasets.append((parts[0].strip(), parts[1].strip()))

        return datasets

    def export_dataset_list_to_csv(
        self, datasets: List[Tuple[str, str]], filename: str
    ):
        """Export the dataset list to a CSV file."""
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Name"])  # Header
            writer.writerows(datasets)

    def get_dataset_info(self) -> Optional[List[Tuple[str, str]]]:
        """Fetch information about all datasets and return as a list."""
        response = requests.get(self.DATASET_URL)  # No auth headers
        success, content = self._process_response(response)
        if success:
            return self.process_dataset_list(content)
        else:
            print(
                f"Failed to fetch dataset information. Status code: {response.status_code}"
            )
            return None

    def download_and_process_dataset(
        self, dataset_key: str, file_keys: str = "all", output_dir: str = "."
    ) -> bool:
        """Download a dataset, extract it, merge parts, and clean up."""
        download_success = self.download_dataset(dataset_key, file_keys, output_dir)

        if download_success:
            print("Download successful.")
            tar_file = os.path.join(output_dir, "dataset.tar")

            # Extract the tar file
            self._extract_tar(tar_file, output_dir)

            print("Please wait, merging files...")
            # Merge parts in all subdirectories
            self._merge_parts_in_subdirs(output_dir)

            print("Merging completed.")
            # Clean up: remove the original tar file
            os.remove(tar_file)
            return True
        else:
            return False

    def _extract_tar(self, tar_file: str, extract_dir: str):
        """Extract the downloaded tar file."""
        with tarfile.open(tar_file, "r") as tar:
            tar.extractall(path=extract_dir)

    def _merge_parts_in_subdirs(self, root_dir: str):
        """Traverse all subdirectories and merge parts in the last child folders."""
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if any(
                re.search(r".*\.part[0-9]+", filename, re.IGNORECASE)
                for filename in filenames
            ):
                self._merge_parts(dirpath)

    def _merge_parts(self, target_dir: str):
        """Merge all part files in the given directory."""
        # Find all unique prefixes of part files
        part_files = [
            f
            for f in os.listdir(target_dir)
            if re.search(r".*\.part[0-9]+", f, re.IGNORECASE)
        ]
        prefixes = set(f.rsplit(".part", 1)[0] for f in part_files)

        for prefix in prefixes:
            print(f"Merging {prefix} in {target_dir}")

            # Find all part files for this prefix and sort them
            parts = sorted(
                [f for f in part_files if f.startswith(prefix)],
                key=lambda x: int(x.rsplit(".part", 1)[1]),
            )

            # Merge the parts
            with open(os.path.join(target_dir, prefix), "wb") as outfile:
                for part in parts:
                    with open(os.path.join(target_dir, part), "rb") as infile:
                        outfile.write(infile.read())

            # Remove the part files
            for part in parts:
                os.remove(os.path.join(target_dir, part))

    def download_dataset(
        self, dataset_key: str, file_keys: str = "all", output_dir: str = "."
    ) -> bool:
        """
        Download a dataset from AIHub.
        
        Downloads the specified dataset using the requests library and saves it
        as a tar file in the specified output directory.
        
        Args:
            dataset_key (str): The unique identifier for the dataset to download.
            file_keys (str, optional): Specific file keys to download. Defaults to "all"
                                      which downloads the entire dataset.
            output_dir (str, optional): Directory where the dataset will be saved.
                                       Defaults to the current directory.
        
        Returns:
            bool: True if the download was successful, False otherwise.
        """

        # Check for available disk space before downloading

        url = f"{self.BASE_DOWNLOAD_URL}/{dataset_key}.do?fileSn={file_keys}"
        return self._download_with_requests(url, dataset_key, output_dir)

    def _download_with_requests(self, url: str, dataset_key: str, output_dir: str) -> bool:
        """Download using requests with a progress bar."""
        output_file = os.path.join(output_dir, "dataset.tar")
        try:
            with requests.get(url, headers=self.auth_headers, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))

                with open(output_file, "wb") as file, tqdm(
                    desc="Downloading",
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress_bar:
                    for data in response.iter_content(chunk_size=8192):
                        size = file.write(data)
                        progress_bar.update(size)
            print("Download completed.")
            return True
        except requests.RequestException as e:
            if e.response.status_code == 502:
                # Must submit the acceptance form before downloading
                form_url = f"https://aihub.or.kr/aihubdata/data/dwld.do?dataSetSn={dataset_key}"
                print(f"+==============================================================================+")
                print(f"| PrivilegeError: You must accept the terms and conditions before downloading. |")
                print(f"| Please visit the following AIHub URL and accept the terms:                   |")
                print(f"| {'':76s} |")
                print(f"| {form_url:76s} |")
                print(f"+==============================================================================+")

                # Open default browser for this URL
                import webbrowser
                webbrowser.open(form_url)
            return False

    def get_raw_url(self, dataset_key: str, file_keys: str = "all") -> str:
        """
        Get the raw download URL for a dataset.
        
        This method constructs the URL for downloading a dataset directly.
        
        Args:
            dataset_key (str): The unique identifier for the dataset.
            file_keys (str, optional): Specific file keys to include in the URL.
                                      Defaults to "all".
            
        Returns:
            str: The raw download URL.
        """
        return f"{self.BASE_DOWNLOAD_URL}/{dataset_key}.do?fileSn={file_keys}"