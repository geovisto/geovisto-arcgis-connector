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
    description: str
    snippet: Optional[str] = None
    fields: list[Field]
    thumbnail: HttpUrl
    structuredLicense: dict
    tags: list[str] = []
    recordCount: int
    slug: Optional[str] = None
    url: HttpUrl
    data: HttpUrl


class GeovistoFeature(Feature):
    """GeoJSON Feature"""

    properties: Optional[dict] = None
    id: int
    bbox: Optional[BBox] = None


class Centroid(BaseModel):
    """Defines central point of Feature object."""

    id: int
    lat: float
    long: float


class DatasetGeospatial(BaseModel):
    """Compound of all dataset parsed data for Geovisto."""

    data: list[dict]
    geometry: list[GeovistoFeature]
    centroids: list[Centroid]
