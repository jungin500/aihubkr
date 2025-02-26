<center>
  
# aihubkr
  
</center>

<p align="center"><img width="480" alt="image" src="https://github.com/user-attachments/assets/f694dc2d-12fc-4d32-af47-ca1f448c5e56"> <img width="480" alt="image" src="https://github.com/user-attachments/assets/6251aeaa-6e7b-4687-a236-8af08f6b9d93"></p>

<p align="center"><i>(Unofficial) NIPA AIHub (aihub.or.kr) Downloader CLI & GUI Utility</i></p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_KR.md">한국어</a>
</p>

---

## Overview
AIHub Downloader is a utility for downloading datasets from AIHub Korea (aihub.or.kr). It provides both command-line (CLI) and graphical (GUI) interfaces for easy access to AIHub datasets.

## Installation
```bash
pip3 install git+https://github.com/jungin500/aihubkr.git@main
```

## Usage
### AIHub GUI
The GUI interface provides an easy-to-use way to browse, search, and download datasets from AIHub.

```bash
aihubkr-gui
```

### AIHub CLI
The CLI interface provides a powerful command-line tool for scripting and automation.

```bash
usage: aihubkr-dl [-h] [-datasetkey DATASETKEY] [-filekey FILEKEY] [-output OUTPUT] {login,logout,download,list}

AIHub Dataset Downloader CLI

positional arguments:
  {login,logout,download,list}
                        Mode of operation

options:
  -h, --help            show this help message and exit
  -datasetkey DATASETKEY
                        Dataset key
  -filekey FILEKEY      File key(s) to download. 'all' to download all files.
  -output OUTPUT        Output directory
```

#### Examples

1. List all available datasets:
```bash
aihubkr-dl list
```

2. List files in a specific dataset:
```bash
aihubkr-dl list -datasetkey YOUR_DATASET_KEY
```

3. Download a specific dataset:
```bash
aihubkr-dl download -datasetkey YOUR_DATASET_KEY -filekey all -output /path/to/output
```

4. Login to AIHub:
```bash
aihubkr-dl login
```

5. Logout from AIHub:
```bash
aihubkr-dl logout
```

## Features
- Browse and search AIHub datasets
- View file listings within datasets
- Download selected datasets or specific files
- Automatic file extraction and merging
- Credential management for AIHub authentication
- Both GUI and CLI interfaces

## Requirements
- Python 3.8 or higher
- Required packages: requests, tqdm, PyQt6, natsort, prettytable

## License
Apache License

## Contributing
Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.