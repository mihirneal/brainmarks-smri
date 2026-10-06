"""List or verify the files of a pinned DataverseNL dataset version, via the Dataverse native API.

    dataverse_files.py curl-config <doi> <version> <dir>   # curl -K config for files missing/incomplete in <dir>
    dataverse_files.py verify <doi> <version> <dir> <manifest.sha256>

Each file is fetched by its datafile id (`/api/access/datafile/<id>`), which serves the
original bytes, and saved at `<directoryLabel>/<filename>` as in the dataset's file tree.

verify checks every file against the SHA-1 that Dataverse stores for it, and flags missing
and extra files.
"""

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SERVER = "https://dataverse.nl"


def version_files(doi, version):
    query = urllib.parse.urlencode({"persistentId": doi})
    url = f"{SERVER}/api/datasets/:persistentId/versions/{version}/files?{query}"
    with urllib.request.urlopen(url, timeout=300) as r:
        files = json.load(r)["data"]
    assert not any(f["restricted"] for f in files), "restricted files need an API token"
    return files


def relpath(f):
    directory = f.get("directoryLabel")
    return f"{directory}/{f['label']}" if directory else f["label"]


def curl_config(files, root):
    for f in files:
        out = root / relpath(f)
        if out.exists() and out.stat().st_size == f["dataFile"]["filesize"]:
            continue
        print(f'url = "{SERVER}/api/access/datafile/{f["dataFile"]["id"]}"\noutput = "{out}"')


def verify(files, root, manifest):
    listed = set()
    for line in Path(manifest).read_text().splitlines():
        listed.add(line.split("  ", 1)[1].removeprefix("source/"))
    bad = 0
    for f in files:
        name, checksum = relpath(f), f["dataFile"]["checksum"]
        assert checksum["type"] == "SHA-1"
        if name not in listed:
            print("missing:", name)
            bad += 1
            continue
        listed.remove(name)
        if hashlib.sha1((root / name).read_bytes()).hexdigest() != checksum["value"]:
            print("checksum mismatch:", name)
            bad += 1
    for name in sorted(listed):
        print("extra:", name)
        bad += 1
    print(f"verify: {len(files)} files in version, {bad} problems", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    cmd, doi, version, root = sys.argv[1:5]
    files = version_files(doi, version)
    if cmd == "curl-config":
        curl_config(files, Path(root))
    else:
        sys.exit(verify(files, Path(root), sys.argv[5]))
