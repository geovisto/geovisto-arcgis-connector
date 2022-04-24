# Geovisto ArcGIS Connector

Web service for obtaining data from [ArcGIS HUB](https://gist.github.com/hamhands/b6d1f0f514678b88cdc01070bf006263#get-apiv3explaindatasets) open data catalogs. All the served data are parsed specifically for [Geovisto library](https://github.com/geovisto/geovisto-map).

## Installation

1. install Python 3.9
2. run `pip install -r requirements.txt` to get the Python dependencies. (In case of error install underlying libraries, the command commented in file [requirements.txt](requirements.txt))
3. to run the app execute `python -m uvicorn app.main:app --reload`

## API documentation

- the documentation in the OpenAPI notation can be foud in file [openapi.json](openapi.json).
- for interactive documentation launch the app and visit [http://localhost:8000/docs](http://localhost:8000/docs).