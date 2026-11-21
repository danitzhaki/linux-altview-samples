#!/usr/bin/env python3
# Copyright 2026 Dan Itzhaki
"""Download, verify and decompress the memory images of this repository.

The images are attached to the GitHub release as .elf.xz files. This script downloads each one,
checks the sha256 of the compressed file, decompresses it next to its ground-truth manifests
(the same layout as the repository: vm-<kver>/dumps/<image>.elf) and checks the sha256 of the
decompressed image against images.tsv. Python 3.8+ standard library only (no xz binary needed).

    python3 fetch.py                     # all 16 images (about 35 GB once decompressed)
    python3 fetch.py --only 6.6.162-default --only 7.2.12-containers
    python3 fetch.py --list
"""

import argparse
import hashlib
import lzma
import os
import sys
import urllib.request

RELEASE = "https://github.com/danitzhaki/linux-altview-samples/releases/download/v1.0/"
HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 1 << 22


def load_table():
    rows = []
    with open(os.path.join(HERE, "images.tsv"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            asset, path, xz_sha, xz_size, elf_sha = line.rstrip("\n").split("\t")
            rows.append((asset, path, xz_sha, int(xz_size), elf_sha))
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(CHUNK):
            h.update(b)
    return h.hexdigest()


def download(url, dst, size):
    tmp = dst + ".part"
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as g:
        done = 0
        while b := r.read(CHUNK):
            g.write(b)
            done += len(b)
            print(f"\r  {done >> 20} / {size >> 20} MiB", end="", flush=True)
    print()
    os.replace(tmp, dst)


def decompress(src, dst):
    h = hashlib.sha256()
    tmp = dst + ".part"
    with lzma.open(src, "rb") as f, open(tmp, "wb") as g:
        while b := f.read(CHUNK):
            h.update(b)
            g.write(b)
    os.replace(tmp, dst)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", action="append", default=[], help="substring of the image name; repeatable")
    p.add_argument("--dest", default=HERE, help="root of the vm-*/ tree (default: this repository)")
    p.add_argument("--keep-xz", action="store_true", help="keep the downloaded .xz files")
    p.add_argument("--list", action="store_true", help="list the images and exit")
    a = p.parse_args()

    rows = [r for r in load_table() if not a.only or any(s in r[1] for s in a.only)]
    if a.list or not rows:
        for asset, path, _, size, _ in rows:
            print(f"{size >> 20:6d} MiB  {path}")
        return 0 if rows else 1

    failed = 0
    for asset, path, xz_sha, size, elf_sha in rows:
        elf = os.path.join(a.dest, path)
        os.makedirs(os.path.dirname(elf), exist_ok=True)
        if os.path.exists(elf) and sha256_file(elf) == elf_sha:
            print(f"OK (present)  {path}")
            continue
        xz = elf + ".xz"
        print(f"fetch  {asset}")
        if not (os.path.exists(xz) and sha256_file(xz) == xz_sha):
            download(RELEASE + asset, xz, size)
            if sha256_file(xz) != xz_sha:
                print(f"FAIL   {asset}: sha256 of the download does not match")
                failed += 1
                continue
        got = decompress(xz, elf)
        if got != elf_sha:
            print(f"FAIL   {path}: sha256 {got} != {elf_sha}")
            failed += 1
            continue
        if not a.keep_xz:
            os.remove(xz)
        print(f"OK     {path}  {elf_sha}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
