<center>
  
# aihubkr
  
</center>

<p align="center"><img width="480" alt="image" src="https://github.com/user-attachments/assets/f694dc2d-12fc-4d32-af47-ca1f448c5e56"> <img width="480" alt="image" src="https://github.com/user-attachments/assets/6251aeaa-6e7b-4687-a236-8af08f6b9d93"></p>

<p align="center"><i>(비공식) NIPA AIHub (aihub.or.kr) 다운로더 CLI & GUI 유틸리티</i></p>

---

## 설치 방법
```bash
pip3 install git+https://github.com/jungin500/aihubkr.git@main
```

## 사용 방법
### AIHub GUI
```bash
aihubkr-gui
```
### AIHub CLI
```bash
usage: aihubkr-dl [-h] [-datasetkey DATASETKEY] [-filekey FILEKEY] [-output OUTPUT] {login,logout,download,list}

AIHub 데이터셋 다운로더 CLI

positional arguments:
  {login,logout,download,list}
                        작업 모드

options:
  -h, --help            도움말 표시
  -datasetkey DATASETKEY
                        데이터셋 키
  -filekey FILEKEY      다운로드할 파일 키. 모든 파일을 다운로드하려면 'all'을 사용하세요.
  -output OUTPUT        출력 디렉토리
```

## 기능
- AIHub 데이터셋 목록 조회
- 데이터셋 내 파일 목록 조회
- 선택한 데이터셋 또는 파일 다운로드
- GUI 및 CLI 인터페이스 지원
- 자동 파일 병합 및 압축 해제

## 요구 사항
- Python 3.8 이상
- 필수 패키지: requests, tqdm, PyQt6, natsort, prettytable

## 라이선스
Apache 라이선스

## 기여 방법
이슈 및 풀 리퀘스트는 언제나 환영합니다. 큰 변경사항은 먼저 이슈를 통해 논의해주세요.