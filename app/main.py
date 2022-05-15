# title           :main.py
# description     :Core file of Geovisto data provider plugin backend api.
# author          :Petr Knetl (456302@mail.muni.cz)
# licence         :MIT

import json
import requests
import geopandas
import urllib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode

from app.models import DatasetMetadata, DatasetGeospatial
from app.documentation import APP_DOCUMENTATION
from app.config import ARCGIS_HUB_DOMAIN, ITEM_PATH
from app import file_cache


app = FastAPI(**APP_DOCUMENTATION)

# add “Access-Control-Allow-Origin: *” header for localhost testing purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
    max_age=3600,
)


@app.get("/")
def available_routes():
    """Lists of all available routes server API."""
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list


@app.get("/datasets/", response_model=list[DatasetMetadata], tags=["dataset_list"])
async def dataset_list(q: str, request: Request):
    """Searches ArcGIS HUB opendata catologs and returns the best match with query parameter **q**."""

    REQUESTED_FIELDS: list[str] = [  # dataset fields requested from ArcGIS hub
        "id",
        "itemId",
        "name",
        "fields",
        "thumbnail",
        "structuredLicense",
        "tags",
        "recordCount",
        "searchDescription",
        "source",
        "owner",
    ]
    FILTERS = {  # get only geospatial datasets
        "openData": "true",
        "type": "any(feature layer)",
        "recordCount": "gt(0)",
    }
    QUERY_PARAMS = {
        "q": q,
        "page[size]": 50,
        "fields[datasets]": ",".join(REQUESTED_FIELDS),
        **{f"filter[{f_key}]": f_val for f_key, f_val in FILTERS.items()},
    }

    query_url: str = f"{ARCGIS_HUB_DOMAIN}/api/v3/datasets/?{urlencode(QUERY_PARAMS)}"
    response = requests.get(query_url)
    hub_data = response.json()

    if not response.ok:  # convey ArcGIS error message to the user
        raise HTTPException(status_code=response.status_code, detail=hub_data)

    datasets = []
    for o in hub_data.get("data"):  # parse each dataset
        dataset = o["attributes"]
        # refers dataset endpoint
        dataset["data"] = request.url_for("dataset", dataset_id=dataset["id"])

        # documentation of dataset
        dataset["url"] = f"{ARCGIS_HUB_DOMAIN}/datasets/{dataset['id']}/about"

        # format publisher of dataset
        dataset["publisher"] = (
            f"{dataset['source']} | {dataset['owner']}"
            if dataset.get("source")
            else dataset["owner"]
        )

        # refers image of dataset
        dataset[
            "thumbnail"
        ] = f"{ITEM_PATH}/{dataset['itemId']}/info/{dataset['thumbnail']}"

        # rename description attribute
        dataset["description"] = dataset.get("searchDescription")

        # remove redundant fields
        del dataset["errors"]
        del dataset["itemId"]
        del dataset["owner"]
        del dataset["source"]

        datasets.append(dataset)
    return datasets


@app.get("/datasets/{dataset_id}/", response_model=DatasetGeospatial, tags=["dataset"])
async def dataset(dataset_id: str):
    """Based on ArcGIS HUB dataset ID (**dataset_id**) get and parse it's Geovisto-ready data."""

    # try to get dataset from the file cache
    try:
        return file_cache.read_dataset_from_file(dataset_id)
    except FileNotFoundError:
        pass

    # file not found in cache, get it from ArcGIS Hub
    DATASET_URL = f"{ARCGIS_HUB_DOMAIN}/datasets/{dataset_id}.geojson"
    try:
        gdf = geopandas.read_file(DATASET_URL)  # load source geojson
    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=e.code, detail=f"Unable to access {DATASET_URL}"
        ) from e

    source_centroids = gdf.to_crs("+proj=cea").centroid.to_crs(gdf.crs)
    source_geometry = json.loads(gdf.to_json())["features"]

    parsed_centroids = []
    parsed_properties = []

    try:
        name_col = [c for c in list(gdf.columns) if is_name_col(c)][0]
    except IndexError:
        name_col = None
    for idx, row in gdf.iterrows():  # for every geospatial item
        row = row.fillna("UNDEFINED")
        if source_centroids[idx] is None or source_geometry[idx] is None:
            continue

        # get it's geojson geometry
        feature = source_geometry[idx]
        feature["id"] = str(idx)
        feature["name"] = row[name_col] if name_col else f"Polygon {idx}"
        del feature["properties"]
        source_geometry[idx] = feature

        # get it's formatted geometry centroid
        c_obj = {
            "type": "Feature",
            "id": str(idx),
            "properties": {"name": row[name_col] if name_col else f"Centroid {idx}"},
            "geometry": {
                "type": "Point",
                "coordinates": [source_centroids[idx].y, source_centroids[idx].x],
            },
        }
        parsed_centroids.append(c_obj)

        # get it's descriptive data
        p_obj = {"id": str(idx), **row.drop(["geometry"]).to_dict()}
        parsed_properties.append(p_obj)

    # create result object containing dataset geometries, centroids and properties all together
    parsed_dataset: DatasetGeospatial = {
        "data": parsed_properties,
        "geometry": {"type": "FeatureCollection", "features": source_geometry},
        "centroids": {"type": "FeatureCollection", "features": parsed_centroids},
    }

    # save to file cache for reuse
    file_cache.write_dataset_to_file(parsed_dataset, dataset_id)

    # return response
    return parsed_dataset


def is_name_col(col_name):
    for s in ["name", "nazev", "název"]:
        if s in col_name.lower():
            return True
    return False
