<center>
  
# aihubkr
  
</center>

<p align="center"><img width="480" alt="image" src="https://github.com/user-attachments/assets/f694dc2d-12fc-4d32-af47-ca1f448c5e56"> <img width="480" alt="image" src="https://github.com/user-attachments/assets/6251aeaa-6e7b-4687-a236-8af08f6b9d93"></p>

<p align="center"><i>(비공식) NIPA AIHub (aihub.or.kr) Downloader CLI & GUI 유틸리티</i></p>

---

## Installation
```bash
pip3 install git+https://github.com/jungin500/aihubkr.git@main
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
