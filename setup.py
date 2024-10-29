from setuptools import find_packages, setup


def get_version() -> str:
    rel_path = "src/aihubkr/__init__.py"
    with open(rel_path, "r") as fp:
        for line in fp.read().splitlines():
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


install_requires = [
    "requests",
    "tqdm",
    "natsort",
]

extras = {}

extras["cli"] = [
    "prettytable",
]

extras["gui"] = [
    "PyQt6",
]

extras["all"] = extras["cli"] + extras["gui"]

extras["dev"] = extras["all"]

setup(
    name="aihubkr",
    version=get_version(),
    author="LimeOrangePie",
    author_email="ji5489@gmail.com",
    description="(비공식) NIPA AIHub (aihub.or.kr) Downloader CLI & GUI 유틸리티",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="aihub AI허브 model-hub machine-learning models natural-language-processing deep-learning pytorch pretrained-models",
    license="Apache",
    url="https://github.com/jungin500/aihubkr",
    package_dir={"": "src"},
    packages=find_packages("src"),
    extras_require=extras,
    entry_points={
        "console_scripts": ["aihubkr-gui=aihubkr.gui.main:main", "aihubkr-dl=aihubkr.cli.main:main"],
    },
    python_requires=">=3.8.0",
    install_requires=install_requires,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    include_package_data=True,
)
