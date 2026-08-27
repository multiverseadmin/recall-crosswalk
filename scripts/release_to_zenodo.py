#!/usr/bin/env python3
"""
Publish a new version of the cross border crosswalk to Zenodo.

WHY THIS EXISTS
The crosswalk is rebuilt continuously and deposited periodically. A deposit is
what makes it citable: a fixed snapshot with an identifier that never moves.
Doing that by hand means it happens once, is enjoyed, and is never done again.

WHY IT TARGETS THE EXISTING DEPOSIT
Zenodo's own GitHub integration is simpler, but it mints a brand new concept
identifier for the repository, which would leave the site pointing at one
dataset and the releases building another. This talks to the Zenodo API instead,
so every release is a new version of concept 10.5281/zenodo.22087135 and every
citation ever printed keeps resolving.

WHAT IT WILL NOT DO
It will not publish a version that is identical to the last one. A DOI that
says a dataset changed when it did not is worse than no DOI, so if the files
come back byte identical the script stops and says so.

The token comes from the environment and is never printed. It needs the
deposit:write and deposit:actions scopes.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

ZENODO = "https://zenodo.org/api"
CONCEPT_RECORD = "22087136"          # any published version of the concept
API = "https://api.carsmultiverse.com/v1"
OUT_DIR = "data"

FILES = {
    "crosswalk.json": API + "/crosswalk",
    "crosswalk.csv": API + "/crosswalk.csv",
    "openapi.json": "https://carsmultiverse.com/openapi.json",
}

UA = "CarsMultiverse-release/1.0 (+https://carsmultiverse.com/)"


def get(url, token=None, method="GET", data=None, content_type=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", UA)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if content_type:
        req.add_header("Content-Type", content_type)
    if data is not None and not isinstance(data, (bytes, bytearray)):
        data = json.dumps(data).encode()
    with urllib.request.urlopen(req, data=data, timeout=120) as r:
        body = r.read()
    return body


def get_json(url, token=None, method="GET", data=None):
    body = get(url, token, method, data, "application/json" if data is not None else None)
    return json.loads(body) if body else {}


def fetch_dataset():
    """Pull the current files and report whether any of them moved."""
    os.makedirs(OUT_DIR, exist_ok=True)
    digests = {}
    changed = False

    for name, url in FILES.items():
        print("fetching " + name, flush=True)
        body = get(url)
        path = os.path.join(OUT_DIR, name)

        new_digest = hashlib.sha256(body).hexdigest()
        old_digest = None
        if os.path.exists(path):
            with open(path, "rb") as fh:
                old_digest = hashlib.sha256(fh.read()).hexdigest()

        if new_digest != old_digest:
            changed = True
            with open(path, "wb") as fh:
                fh.write(body)

        digests[name] = {"sha256": new_digest, "bytes": len(body)}

    return changed, digests


def crossing_count():
    with open(os.path.join(OUT_DIR, "crosswalk.json"), "rb") as fh:
        return json.load(fh).get("crossing", 0)


def publish(token, version):
    """Create, fill and publish a new version of the existing deposit."""
    latest = get_json(ZENODO + "/records/" + CONCEPT_RECORD, token)
    concept = latest.get("conceptrecid") or latest.get("conceptdoi", "").split(".")[-1]
    print("concept record " + str(concept), flush=True)

    newver = get_json(
        ZENODO + "/deposit/depositions/" + str(latest["id"]) + "/actions/newversion",
        token,
        method="POST",
    )

    draft_url = newver["links"]["latest_draft"]
    draft = get_json(draft_url, token)
    bucket = draft["links"]["bucket"]

    # A new version inherits the previous files. Remove them so the deposit
    # holds this month's data and not a mixture of two months.
    for existing in get_json(draft_url + "/files", token):
        get(draft_url + "/files/" + existing["id"], token, method="DELETE")

    for name in FILES:
        with open(os.path.join(OUT_DIR, name), "rb") as fh:
            payload = fh.read()
        print("uploading " + name + " (" + str(len(payload)) + " bytes)", flush=True)
        get(bucket + "/" + name, token, method="PUT",
            data=payload, content_type="application/octet-stream")

    meta = draft.get("metadata", {})
    meta["version"] = version
    meta["publication_date"] = version
    meta["description"] = (
        meta.get("description", "")
        .split("<!--counts-->")[0]
        + "<!--counts--><p>This version holds "
        + format(crossing_count(), ",")
        + " recalls matched across more than one national register.</p>"
    )

    get_json(draft_url, token, method="PUT", data={"metadata": meta})

    published = get_json(draft_url + "/actions/publish", token, method="POST")
    return published.get("doi", "")


def main():
    token = os.environ.get("ZENODO_TOKEN", "").strip()
    version = os.environ.get("RELEASE_VERSION", "").strip()

    if not version:
        print("RELEASE_VERSION is required", file=sys.stderr)
        return 2

    changed, digests = fetch_dataset()

    with open(os.path.join(OUT_DIR, "checksums.json"), "w") as fh:
        json.dump({"version": version, "files": digests}, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print(json.dumps(digests, indent=2), flush=True)

    if not changed:
        print("The dataset is byte identical to the last release. Nothing to publish.")
        with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as fh:
            fh.write("released=false\n")
        return 0

    if not token:
        print("Data changed and was committed, but ZENODO_TOKEN is not set, "
              "so no deposit was made.", file=sys.stderr)
        with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as fh:
            fh.write("released=false\n")
        return 0

    try:
        doi = publish(token, version)
    except urllib.error.HTTPError as err:
        print("Zenodo refused the release: " + str(err.code) + " " + err.reason,
              file=sys.stderr)
        print(err.read().decode("utf8", "replace")[:800], file=sys.stderr)
        return 1

    print("published " + doi)
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as fh:
        fh.write("released=true\n")
        fh.write("doi=" + doi + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
