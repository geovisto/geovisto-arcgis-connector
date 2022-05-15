# title           :models.py
# description     :API inputs and outputs type definitions.
# author          :Petr Knetl (456302@mail.muni.cz)
# licence         :MIT

from typing import Any, Optional
from pydantic import BaseModel, HttpUrl
from geojson_pydantic import Feature
from geojson_pydantic.types import BBox


class Field(BaseModel):
    """Dataset column description."""

    sqlType: Optional[str] = None
    nullable: Optional[bool] = None
    editable: Optional[bool] = None
    length: Optional[int] = None
    defaultValue: Any
    domain: Any
    name: str
    alias: str
    type: str


class StructuredLicence(BaseModel):
    """Copyright licence of dataset."""

    type: str
    name: Optional[str]
    abbr: Optional[str]
    url: Optional[HttpUrl]


class DatasetMetadata(BaseModel):
    """Description of ArcGIS Hub dataset."""

    id: str
    name: str
    publisher: str
    description: Optional[str]
    fields: list[Field]
    thumbnail: HttpUrl
    structuredLicense: dict
    tags: list[str] = []
    recordCount: Optional[int]
    url: str
    data: str


class GeovistoFeature(Feature):
    """GeoJSON Feature"""

    properties: Optional[dict] = None
    id: int
    bbox: Optional[BBox] = None


class FeatureCollection(BaseModel):
    type: str
    features: list[object]


class DatasetGeospatial(BaseModel):
    """Compound of all dataset parsed data for Geovisto."""

    data: list[dict]
    geometry: FeatureCollection
    centroids: FeatureCollection
