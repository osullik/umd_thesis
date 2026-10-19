import argparse
import datetime
import gzip
import hashlib
import json
import os
import shutil
import urllib.parse
import urllib.request

import networkx as nx


def sha256(path:str)->str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url:str, path:str)->None:
    print(f"DOWNLOADING {url}")
    with urllib.request.urlopen(url) as response, open(path + ".part", "wb") as f:
        shutil.copyfileobj(response, f)
    os.replace(path + ".part", path)


def decompress(path:str)->str:
    if not path.endswith(".gz"):
        return path
    extracted = path.removesuffix(".gz")
    with gzip.open(path, "rb") as source, open(extracted, "wb") as target:
        shutil.copyfileobj(source, target)
    return extracted


def dataset_urls(dataset:dict)->list:
    return [(role, dataset[f"{role}_url"]) for role in ("graph", "ground_truth") if dataset[f"{role}_url"] is not None]


def is_current(dataset:dict, directory:str, record:dict)->bool:
    if record is None or [f["url"] for f in record["files"]] != [url for _, url in dataset_urls(dataset)]:
        return False
    for f in record["files"]:
        raw = os.path.join(directory, f["raw_file"])
        if not os.path.exists(raw) or not os.path.exists(os.path.join(directory, f["file"])) or sha256(raw) != f["sha256"]:
            return False
    return True


def fetch(dataset:dict, directory:str)->dict:
    os.makedirs(directory, exist_ok=True)
    files = []
    for role, url in dataset_urls(dataset):
        raw_file = os.path.basename(urllib.parse.urlparse(url).path)
        raw_path = os.path.join(directory, raw_file)
        download(url, raw_path)
        files.append({"role":role,
                      "url":url,
                      "raw_file":raw_file,
                      "file":os.path.basename(decompress(raw_path)),
                      "sha256":sha256(raw_path)})

    graph_file = next(f["file"] for f in files if f["role"] == "graph")
    print(f"LOADING {graph_file}")
    G = nx.read_edgelist(path=os.path.join(directory, graph_file), comments="#")

    return {"directory":dataset["directory"],
            "downloaded":datetime.date.today().isoformat(),
            "vertices":G.number_of_nodes(),
            "edges":G.number_of_edges(),
            "files":files}


def write_manifest(manifest:dict, path:str)->None:
    with open(path + ".part", "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(path + ".part", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets-list", type=str, default=os.path.join(".","snap_datasets.json"), help="JSON list of datasets to download")
    ap.add_argument("--datasets-dir", type=str, default=os.path.join(".","datasets"), help="Directory that receives one folder per dataset")
    ap.add_argument("--manifest", type=str, default=os.path.join(".","datasets","manifest.json"), help="Manifest of URLs, hashes and graph sizes")
    flags = ap.parse_args()

    with open(flags.datasets_list, "r") as f:
        datasets = json.load(f)

    manifest = {}
    if os.path.exists(flags.manifest):
        with open(flags.manifest, "r") as f:
            manifest = json.load(f)

    for dataset in datasets:
        directory = os.path.join(flags.datasets_dir, dataset["directory"])
        if is_current(dataset, directory, manifest.get(dataset["name"])):
            print(f"{dataset['name']} already present with matching hash - skipping")
            continue
        manifest[dataset["name"]] = fetch(dataset, directory)
        write_manifest(manifest, flags.manifest)
        print(f"{dataset['name']}: {manifest[dataset['name']]['vertices']} vertices, {manifest[dataset['name']]['edges']} edges")
