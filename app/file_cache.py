# title           :file_cache.py
# description     :File cache functionality of Geovisto data-providel module backend.
# author          :Petr Knetl (456302@mail.muni.cz)
# licence         :MIT

import requests
import json
import os
import re
import datetime as dt

from glob import glob

from app.models import DatasetGeospatial
from app.config import STORAGE_FOLDER, CACHE_WEEKS_TO_LIVE, ARCGIS_HUB_DOMAIN


def generate_dataset_file_path(dataset_id: str):
    """Create dataset filename containing dataset ID and timestamp."""
    timestamp = int(dt.datetime.now().timestamp() * 1000)
    return f"{STORAGE_FOLDER}/{dataset_id}-{timestamp}.json"


def write_dataset_to_file(dataset: DatasetGeospatial, dataset_id: str):
    """Saves dataset DatasetGeospatial object to separate file in file storage."""
    path = generate_dataset_file_path(dataset_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as outfile:
        outfile.write(json.dumps(dataset))


def read_dataset_from_file(dataset_id: str):
    """Saves dataset DatasetGeospatial object to separate file in file storage."""
    # get timestamp idicating last modification from ArcGIS Hub
    query_url: str = f"{ARCGIS_HUB_DOMAIN}/api/v3/datasets/{dataset_id}/?fields[datasets]=itemModified"
    response = requests.get(query_url)
    modified_timestamp = int(response.json()["data"]["attributes"]["itemModified"])

    # get dataset files stored in file cache
    dataset_files = glob(f"{STORAGE_FOLDER}/{dataset_id}-*.json")

    # try to find up to date file
    for f_path in dataset_files:
        f_timestamp = int(re.search(r"-(\d+).json", f_path).group(1))
        if (
            f_timestamp > modified_timestamp
        ):  # cached data are newer than data stored in ArcGIS
            with open(f_path, "r") as outfile:
                return json.loads(outfile.read())  # return file content

    # no cache hit --> raise Exception
    raise FileNotFoundError


def sweep_old_cache():
    """Checks file storage and erases all datasests older than CACHE_WEEKS_TO_LIVE constant."""
    erase_time_threshold = (
        dt.datetime.now() - dt.timedelta(weeks=CACHE_WEEKS_TO_LIVE)
    ).timestamp()
    for filename in os.scandir(STORAGE_FOLDER):
        if (
            filename.is_file()
            and os.path.getctime(filename.path) < erase_time_threshold
        ):
            os.remove(filename.path)
