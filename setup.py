from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent


def pyinstaller_args() -> list[str]:
    args = [
        "--onefile",
        "--windowed",
        "--name",
        "open-smartfarm-doctor",
        "--add-data",
        "models;models",
        "--add-data",
        "data;data",
        "--add-data",
        "i18n;i18n",
    ]
    mosquitto_binary = ROOT / "bin" / "mosquitto" / "mosquitto.exe"
    if mosquitto_binary.exists():
        args.extend(["--add-binary", "bin\\mosquitto\\mosquitto.exe;bin\\mosquitto"])
    return args


setup(
    name="open-smartfarm-doctor",
    version="0.1.0",
    description="Public multicrop smartfarm assistant program derived from BerryDoctor",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "firmware", "docs")),
    include_package_data=True,
    python_requires=">=3.11",
)
