# title           :config.py
# description     :Configuration file containing global constants of Geovisto data-provider module backend server.
# author          :Petr Knetl (456302@mail.muni.cz)
# licence         :MIT

# folder where are parsed datasets stored (file cache path)
STORAGE_FOLDER = "data"

# period in weeks after which will cache manager remove all dataset older than that
CACHE_WEEKS_TO_LIVE = 4

# DOMAIN of ArcGIS Hub server
ARCGIS_HUB_DOMAIN = "https://hub.arcgis.com"

# Path prefix to remote dataset metadata storage
ITEM_PATH = "https://www.arcgis.com/sharing/rest/content/items/"
