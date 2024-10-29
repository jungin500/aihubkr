<center>

# aihubkr

_(비공식) NIPA AIHub (aihub.or.kr) Downloader CLI & GUI 유틸리티_
</center>

---

## Installation
```bash
pip3 install git+https://github.com/jungin500/aihubkr.git@v0.1.0
```

## Usage
### AIHub GUI

```bash
aihubkr-gui
```
### AIHub CLI
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
