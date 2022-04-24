import json
import requests
import geopandas
import urllib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode

from app.models import DatasetMetadata, DatasetGeospatial
from app.documentation import APP_DOCUMENTATION

app = FastAPI(**APP_DOCUMENTATION)

ARCGIS_HUB_DOMAIN = "https://hub.arcgis.com"
ITEM_PATH = "https://www.arcgis.com/sharing/rest/content/items/"

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
    """All available routes."""
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list


@app.get("/datasets/", response_model=list[DatasetMetadata], tags=["dataset_list"])
async def dataset_list(q: str, request: Request):
    """Searches ArcGIS HUB opendata catologs and returns the best match with query parameter **q**."""

    REQUESTED_FIELDS: list[str] = [  # dataset fields requested from ArcGIS hub
        "id",
        "itemId",
        "name",
        "snippet",
        "description",
        "fields",
        "thumbnail",
        "structuredLicense",
        "tags",
        "recordCount",
        "slug",
    ]
    FILTERS = {  # get only geospatial datasets
        "openData": "true",
        "type": "any(feature layer)",
        # TODO: SLUG is not missing
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
    for o in hub_data.get("data"):  # parse every dataset metadata
        dataset = o["attributes"]
        # refers dataset endpoint
        dataset["data"] = request.url_for("dataset", dataset_id=dataset["id"])

        # documentation of dataset
        dataset["url"] = f"{ARCGIS_HUB_DOMAIN}/datasets/{dataset.get('slug')}"

        # refers image of dataset
        dataset[
            "thumbnail"
        ] = f"{ITEM_PATH}/{dataset['itemId']}/info/{dataset['thumbnail']}"

        # redundant fields
        del dataset["errors"]
        del dataset["itemId"]

        datasets.append(dataset)
    return datasets


@app.get("/datasets/{dataset_id}", response_model=DatasetGeospatial, tags=["dataset"])
async def dataset(dataset_id: str):
    """Based on ArcGIS HUB dataset ID (**dataset_id**) get and parse it's Geovisto-ready data."""

    DATASET_URL = f"{ARCGIS_HUB_DOMAIN}/datasets/{dataset_id}.geojson"
    try:
        gdf = geopandas.read_file(DATASET_URL)  # load source geojson
    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=e.code, detail=f"Unable to access {DATASET_URL}"
        ) from e

    gdf = gdf.fillna(00)  # remove problematic NAs
    source_centroids = gdf.centroid
    source_geometry = json.loads(gdf.to_json())["features"]

    parsed_centroids = []
    parsed_properties = []
    for idx, row in gdf.iterrows():  # for every geospatial item

        # get it's geojson geometry
        feature = source_geometry[idx]
        feature["id"] = idx
        del feature["properties"]
        source_geometry[idx] = feature

        # get it's geometry centroid
        c_obj = {
            "id": idx,
            "lat": round(source_centroids[idx].x, 2),
            "long": round(source_centroids[idx].y, 2),
        }
        parsed_centroids.append(c_obj)

        # get it's descriptive data
        p_obj = {"id": idx, **row.drop(["geometry"]).to_dict()}
        parsed_properties.append(p_obj)

    # return object containing dataset geometries, centroids and properties all together
    return {
        "data": parsed_properties,
        "geometry": source_geometry,
        "centroids": parsed_centroids,
    }
