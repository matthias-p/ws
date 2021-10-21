import hashlib
import io
from typing import List
from pathlib import Path

import requests

MAGIC_NUMBERS = [
    b"\xff\xd8\xff",  # jpg
    b"\x89\x50\x4e",  # png but only first 3 byte
]


def _check_magic_number(line):
    return line in MAGIC_NUMBERS


def _check_path(path: Path):
    path = path.resolve()
    if not path.exists():
        print("Path doesn't exist - creating dir")
        path.mkdir(parents=True, exist_ok=True)

    if path.is_file():
        print("Path is a file - using parent as path")
        path = path.parent

    return path


def download_urls(download_path: Path, url_list: List[str]):
    download_path = _check_path(download_path)
    for link in url_list:
        try:
            r = requests.get(link)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            continue

        bytes_file = io.BytesIO(r.content)

        if not _check_magic_number(bytes_file.read(3)):
            continue

        img_t = link.rsplit(".", 1)[-1][:3]  # only get 3 chars
        md5 = hashlib.md5(bytes_file.getvalue()).hexdigest()
        # use hash as name so duplicates are overwritten

        with open(download_path / f"{md5}.{img_t}", "wb") as img_file:
            img_file.write(bytes_file.getvalue())
