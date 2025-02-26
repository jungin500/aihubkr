import argparse
import os
import sys
from typing import Any, Dict

from aihubkr.core.auth import AIHubAuth
from aihubkr.core.config import AIHubConfig
from aihubkr.core.downloader import AIHubDownloader
from aihubkr.core.filelist_parser import AIHubResponseParser, sizeof_fmt
from prettytable import PrettyTable


def parse_arguments() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="AIHub Dataset Downloader CLI")
    parser.add_argument(
        "mode", choices=["login", "logout", "download", "list"], help="Mode of operation"
    )
    parser.add_argument("-datasetkey", help="Dataset key")
    parser.add_argument("-filekey", help="File key(s) to download. 'all' to download all files.")
    parser.add_argument("-output", help="Output directory")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return vars(parser.parse_args())


def list_datasets(downloader: AIHubDownloader) -> None:
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
        print(f"Dataset list is exported to {csv_filename}.")
    else:
        print("Failed to fetch dataset information.")


def list_file_tree(downloader: AIHubDownloader, dataset_key: str) -> None:
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
    downloader: AIHubDownloader, dataset_key: str, file_keys: str, output_dir: str
) -> None:
    print(f"Downloading dataset {dataset_key}, file key(s): {file_keys}")
    print(" --> dataset.tar ...")
    success = downloader.download_and_process_dataset(dataset_key, file_keys, output_dir)
    if success:
        print("Download completed successfully.")
    else:
        print("Download failed.")


def prompt_login() -> Dict[str, str]:
    from getpass import getpass

    while True:
        print("Enter your AIHub ID:", end=" ")
        aihub_id = input().strip()
        aihub_pw = getpass(prompt="Enter your AIHub password: ").strip()

        if not aihub_id or not aihub_pw:
            print("AIHub ID and password cannot be empty.")
            continue

        return {"id": aihub_id, "pass": aihub_pw}


def main() -> None:
    args = parse_arguments()

    # Create downloader without authentication for listing operations
    downloader = AIHubDownloader({})

    if args["mode"] == "login":
        auth = AIHubAuth(None, None)
        credential = auth.load_credentials()
        if credential is None:
            intermediate_credential = prompt_login()
            auth.aihub_id = intermediate_credential.get("id")
            auth.aihub_pw = intermediate_credential.get("pass")
        else:
            print("Authenticating with existing credentials...")

        auth_headers = auth.authenticate()
        if auth_headers is None:
            print("Authentication failed.")
            return

        auth.save_credential()
        print("Login Succeded")
    elif args["mode"] == "logout":
        auth = AIHubAuth(None, None)
        auth.clear_credential()
        print(f"Removing login credentials in {AIHubConfig.CONFIG_PATH}")
    elif args["mode"] == "list":
        if args["datasetkey"]:
            list_file_tree(downloader, args["datasetkey"])
        else:
            list_datasets(downloader)
    elif args["mode"] == "download":
        if not args["datasetkey"] or not args["filekey"]:
            print("Dataset key and file key are required for download mode.")
            return
        if not args["output"]:
            print("Output directory is required for download mode.")
            return

        # Authenticate only for download operations
        auth = AIHubAuth(None, None)
        credential = auth.load_credentials()
        if credential is None:
            intermediate_credential = prompt_login()
            auth.aihub_id = intermediate_credential.get("id")
            auth.aihub_pw = intermediate_credential.get("pass")

        auth_headers = auth.authenticate()
        if auth_headers is None:
            print("Authentication failed.")
            return

        if credential is None:
            # Prompt user
            print(f"Do you want AIHubDownloader to save credential to '{AIHubConfig.CONFIG_PATH}'? (y/n)", end=" ")
            if input().lower().strip() == 'y':
                auth.save_credential()

        # Check for list for disk space check
        file_tree = downloader.get_file_tree(args["datasetkey"])
        if not file_tree:
            print(f"Failed to fetch file tree for datasetkey {args['datasetkey']}.")
            return

        parser = AIHubResponseParser()
        tree, paths = parser.parse_tree_output(file_tree)
        if not paths:
            print(f"No files found on server for datasetkey {args['datasetkey']}.")
            print("Tip: It can also be a bug for parsing dataset list. ")
            return

        file_paths = [item for item in paths if item[1]]
        file_db = {}

        min_total_size = 0
        max_total_size = 0
        for row, (path, _, file_key, (file_display_size, file_min_size, file_max_size)) in enumerate(file_paths):
            file_db[file_key] = (path, file_display_size, file_min_size, file_max_size)

        for filekey in args["filekey"].split(","):
            if filekey == "all":
                min_total_size = sum([file_db[key][2] for key in file_db])
                max_total_size = sum([file_db[key][3] for key in file_db])
                break
            if filekey not in file_db:
                print(f"File key {filekey} not found.")
                return
            min_total_size += file_db[filekey][2]
            max_total_size += file_db[filekey][3]

        # Check for availabe disk space on args.output directory
        fstat = os.statvfs(args["output"])
        available_space = fstat.f_frsize * fstat.f_bavail

        print(
            f"Estimated download size: {sizeof_fmt(min_total_size)} ~ {sizeof_fmt(max_total_size)}"
        )

        print(
            f"Free disk space: {sizeof_fmt(available_space)}"
        )

        if max_total_size > available_space:
            print("Insufficient disk space.")
            return

        # Create a new downloader with authentication headers
        downloader = AIHubDownloader(auth_headers)
        download_dataset(downloader, args["datasetkey"], args["filekey"], args["output"])
    else:
        print("Invalid mode. Use -help for usage information.")


if __name__ == "__main__":
    main()