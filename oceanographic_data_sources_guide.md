# Oceanographic and Ecological Data Sources for White Shark Habitat Modeling
## Comprehensive Access Guide with Python Implementation

---

## 1. OCEARCH Shark Tracker - Carcharodon carcharias Tracks

### Overview
OCEARCH provides real-time tracking data for white sharks (Carcharodon carcharias) and other shark species through satellite telemetry using the Argos/CLS satellite system.

### Data Access Methods

#### Official Access
- **Web Interface**: https://www.ocearch.org/tracker/
- **Mobile Apps**: Available on iOS and Android
- **Data Policy**: https://www.ocearch.org/data-sharing/

#### API Access (Unofficial/Reverse-Engineered)
While OCEARCH does not provide official API documentation, developers have created wrappers:
- GitHub repositories exist that access OCEARCH data programmatically
- Example: https://github.com/sbaum1994/sharks (wrapper for OCEARCH API)
- **Important**: OCEARCH's data sharing policy requires explicit permission for any use beyond their official tracker

#### Authentication/Registration
- **Official Use**: Contact tracker@ocearch.org for research/educational data access
- **Registration Required**: Yes, for formal data sharing agreements
- Must agree to data usage terms

#### Data Format
- JSON endpoints (undocumented)
- Real-time ping locations with timestamps
- Individual shark profiles with species, size, sex

#### Python Implementation

```python
# Note: This is based on reverse-engineered endpoints
# Official permission required for research use
import requests
import pandas as pd

# Example endpoint structure (unofficial)
# Contact OCEARCH for official access
base_url = "https://www.ocearch.org/tracker/api/"

# For official research access:
# 1. Contact OCEARCH at tracker@ocearch.org
# 2. Request data sharing agreement
# 3. Obtain authorized access to data
```

#### Rate Limits/Restrictions
- Unofficial API endpoints may change without notice
- Data usage without permission is prohibited
- Recommended: Contact OCEARCH for formal data access agreement

---

## 2. GBIF/OBIS - Marine Mammal and Orca Observations

### 2.1 GBIF (Global Biodiversity Information Facility)

#### API Endpoints
- **Base URL**: https://api.gbif.org/
- **Occurrence Search**: https://api.gbif.org/v1/occurrence/search
- **Occurrence Download**: https://api.gbif.org/v1/occurrence/download/request
- **Species API**: https://api.gbif.org/v1/species

#### Authentication
- Most API use does NOT require authentication
- POST, PUT, DELETE requests require HTTP Basic Authentication
- Create account at: https://www.gbif.org/user/profile

#### Data Format
- JSON (API responses)
- ZIP files containing CSV/Darwin Core Archive (downloads)
- Supports paging with limit/offset parameters

#### Python Library: pygbif

**Installation:**
```bash
pip install pygbif
```

**Example Code - Marine Mammal Occurrences:**
```python
from pygbif import occurrences as occ
from pygbif import species

# Search for California sea lion (Zalophus californianus)
# First, get the taxon key
sp = species.name_backbone(name='Zalophus californianus')
taxon_key = sp['usageKey']

# Search for occurrences
results = occ.search(taxonKey=taxon_key, limit=300)

# Download occurrences for multiple species
query = {
    "type": "and",
    "predicates": [
        {
            "type": "in",
            "key": "TAXON_KEY",
            "values": ["2433406", "2433443", "5219426", "2433433"]
            # Zalophus californianus, Mirounga angustirostris,
            # Arctocephalus pusillus, Phoca vitulina
        },
        {
            "type": "equals",
            "key": "HAS_COORDINATE",
            "value": "true"
        }
    ]
}

# Submit download request (requires login)
download_key = occ.download(query, user="username", pwd="password", email="email@example.com")

# Check download status
occ.download_meta(download_key)

# Download the file when ready
occ.download_get(download_key, path="./data/")
```

**Example - Orcinus orca (Killer Whale):**
```python
# Search for Orcinus orca
sp_orca = species.name_backbone(name='Orcinus orca')
orca_occurrences = occ.search(taxonKey=sp_orca['usageKey'], limit=1000)

# Convert to DataFrame
import pandas as pd
orca_df = pd.DataFrame(orca_occurrences['results'])
```

#### Rate Limits
- Frequent queries may be rate limited (HTTP 429 error)
- Set User-Agent header with contact info
- Use download API for large requests (supports up to 100,000 taxonkeys)

---

### 2.2 OBIS (Ocean Biodiversity Information System)

#### API Endpoint
- **Base URL**: https://api.obis.org/
- **Occurrence API**: https://api.obis.org/occurrence
- **Documentation**: https://manual.obis.org/access

#### Authentication
- No authentication required for basic access

#### Data Format
- JSON
- Exports to Pandas DataFrame easily

#### Python Library: pyobis

**Installation:**
```bash
pip install pyobis
```

**Example Code - Marine Mammal Colonies:**
```python
from pyobis import occurrences
import pandas as pd

# California sea lion
zalophus = occurrences.search(scientificname="Zalophus californianus", size=5000)
zalophus_df = pd.DataFrame(zalophus['results'])

# Northern elephant seal
mirounga = occurrences.search(scientificname="Mirounga angustirostris", size=5000)

# Cape fur seal
arctocephalus = occurrences.search(scientificname="Arctocephalus pusillus", size=5000)

# Harbor seal
phoca = occurrences.search(scientificname="Phoca vitulina", size=5000)

# Orcinus orca
orca = occurrences.search(scientificname="Orcinus orca", size=5000)

# Access coordinates
for record in orca['results']:
    lat = record.get('decimalLatitude')
    lon = record.get('decimalLongitude')
    date = record.get('eventDate')
    print(f"Lat: {lat}, Lon: {lon}, Date: {date}")
```

#### Rate Limits
- Generally permissive, no strict limits for reasonable use

---

## 3. NASA OceanColor - MODIS-Aqua Level 3 SST and Chlorophyll-a

### Overview
MODIS-Aqua provides ocean color data including Sea Surface Temperature (SST) and Chlorophyll-a concentration at 4km resolution.

### Data Access Methods

#### Primary Access: earthaccess Python Library (Recommended 2025)

**Installation:**
```bash
pip install earthaccess
```

**NASA Earthdata Login Required:**
- Create account at: https://urs.earthdata.nasa.gov/
- Free registration required

**Authentication Setup:**
```python
import earthaccess

# Login (creates .netrc file for future use)
earthaccess.login()

# Or provide credentials directly
auth = earthaccess.login(strategy="interactive")
```

**Example - Search and Download MODIS-Aqua Chlorophyll:**
```python
import earthaccess
import xarray as xr

# Login
earthaccess.login()

# Search for MODIS-Aqua Level 3 Chlorophyll data
results = earthaccess.search_data(
    short_name='MODISA_L3m_CHL',
    cloud_hosted=True,
    temporal=('2023-01-01', '2023-12-31'),
    bounding_box=(-125, 30, -115, 40)  # West Coast example
)

# Download files
files = earthaccess.download(results, "./data/modis_chl/")

# Open with xarray
ds = xr.open_mfdataset(files)
```

**Example - MODIS-Aqua SST (11 micron Thermal IR):**
```python
# Dataset IDs for SST:
# Monthly 4km Daytime: MODIS_AQUA_L3_SST_THERMAL_MONTHLY_4KM_DAYTIME_V2019.0
# Monthly 4km Nighttime: MODIS_AQUA_L3_SST_THERMAL_MONTHLY_4KM_NIGHTTIME_V2019.0

# Search by dataset ID
sst_results = earthaccess.search_data(
    doi='10.5067/AQUA/MODIS/L3M/SST/2019',
    temporal=('2023-01-01', '2023-12-31')
)

files = earthaccess.download(sst_results, "./data/modis_sst/")
```

#### Alternative: ERDDAP Access via erddapy

**Installation:**
```bash
pip install erddapy
```

**Example Code:**
```python
from erddapy import ERDDAP
import pandas as pd

# Connect to NOAA CoastWatch ERDDAP
e = ERDDAP(
    server="https://coastwatch.pfeg.noaa.gov/erddap",
    protocol="griddap"
)

# Chlorophyll-a dataset (8-day composite, 4km)
e.dataset_id = "erdMH1chla8day"
e.variables = ["chlorophyll"]
e.constraints = {
    "time>=": "2023-01-01T00:00:00Z",
    "time<=": "2023-12-31T23:59:59Z",
    "latitude>=": 30,
    "latitude<=": 40,
    "longitude>=": -125,
    "longitude<=": -115
}

# Download as netCDF
e.griddap_initialize()
ds = e.to_xarray()

# Or download to file
e.to_netcdf(path="modis_chl.nc")
```

**SST via ERDDAP:**
```python
# Monthly SST dataset
e.dataset_id = "erdMH1sstdmday"  # Monthly daytime SST
e.variables = ["sst"]
# Apply same constraints and download
```

#### OPeNDAP Access

NASA provides OPeNDAP servers for direct remote access:
- **OPeNDAP Hyrax**: https://opendap.earthdata.nasa.gov/

```python
import xarray as xr

# Direct OPeNDAP access (requires authentication)
opendap_url = "https://oceandata.sci.gsfc.nasa.gov/opendap/[path_to_file].nc"
ds = xr.open_dataset(opendap_url)
```

#### Data Format and Resolution
- **Format**: netCDF-4, HDF4
- **Chlorophyll-a Resolution**: 4km, 9km (global)
- **SST Resolution**: 4km
- **Temporal**: Daily, 8-day composite, Monthly
- **Coverage**: Global

#### Rate Limits
- No explicit rate limits with authenticated access
- NASA Earthdata Login required for most downloads
- Cloud-hosted data recommended for large-scale analysis

---

## 4. Copernicus Marine (CMEMS) - Sea Surface Height Anomaly

### Overview
Copernicus Marine Environment Monitoring Service provides altimetry-derived sea level data including Sea Level Anomaly (SLA) and Absolute Dynamic Topography (ADT).

### Product Information
- **Product ID**: SEALEVEL_GLO_PHY_L4_MY_008_047
- **Full Name**: Global Ocean Gridded L4 Sea Surface Heights and Derived Variables Reprocessed (1993-ongoing)
- **Resolution**: 0.25° x 0.25°
- **Temporal**: Daily
- **Variables**: Sea Level Anomaly (sla), Absolute Dynamic Topography (adt), geostrophic velocities

### Data Access

#### Registration Required
- Create account at: https://data.marine.copernicus.eu/
- Free registration
- No volume or bandwidth quotas

#### Python Library: copernicusmarine

**Installation:**
```bash
# Recommended: conda/mamba
conda install -c conda-forge copernicusmarine

# Or pip
pip install copernicusmarine
```

**Authentication:**
```bash
# Login command (interactive)
copernicusmarine login
```

**Example - Download Sea Level Anomaly Subset:**
```python
import copernicusmarine

# Subset and download SLA data
copernicusmarine.subset(
    dataset_id="cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D",
    variables=["sla", "adt"],  # Sea Level Anomaly and Absolute Dynamic Topography
    minimum_longitude=-130,
    maximum_longitude=-110,
    minimum_latitude=25,
    maximum_latitude=45,
    start_datetime="2023-01-01T00:00:00",
    end_datetime="2023-12-31T23:59:59",
    output_filename="sea_level_anomaly_2023.nc",
    output_directory="./data/cmems/"
)
```

**Open Dataset Remotely (without downloading):**
```python
import copernicusmarine
import xarray as xr

# Open dataset directly (streams data)
ds = copernicusmarine.open_dataset(
    dataset_id="cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D",
    minimum_longitude=-130,
    maximum_longitude=-110,
    minimum_latitude=25,
    maximum_latitude=45,
    start_datetime="2023-01-01",
    end_datetime="2023-12-31"
)

# Work with xarray dataset
sla = ds['sla']
```

#### Data Format
- NetCDF-4
- Zarr (for cloud-optimized access)

#### Rate Limits
- No rate limits or quotas
- Free access with registration

#### Documentation
- https://help.marine.copernicus.eu/
- https://toolbox-docs.marine.copernicus.eu/

---

## 5. NASA PO.DAAC - SMAP Level 3 Sea Surface Salinity

### Overview
Soil Moisture Active Passive (SMAP) mission provides Sea Surface Salinity (SSS) measurements at approximately 40-70km resolution.

### Product Information

#### Available Datasets
1. **RSS SMAP** (Remote Sensing Systems):
   - Monthly: `SMAP_RSS_L3_SSS_SMI_MONTHLY_V4`
   - 8-Day: `SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V4`
   - Resolution: 0.25° (~25km)

2. **JPL SMAP** (Jet Propulsion Laboratory):
   - Monthly: `SMAP_JPL_L3_SSS_CAP_MONTHLY_V5`
   - 8-Day: `SMAP_JPL_L3_SSS_CAP_8DAY-RUNNINGMEAN_V5`
   - Resolution: 0.25°

### Data Access

#### Method 1: podaac-data-subscriber (Command Line + Python)

**Installation:**
```bash
pip install podaac-data-subscriber
```

**NASA Earthdata Authentication:**
- Required: https://urs.earthdata.nasa.gov/
- Setup .netrc file:

```bash
# Linux/Mac: ~/.netrc
# Windows: ~/_netrc
machine urs.earthdata.nasa.gov
login YOUR_USERNAME
password YOUR_PASSWORD
```

**Download Command:**
```bash
# Download SMAP RSS monthly SSS data
podaac-data-downloader -c SMAP_RSS_L3_SSS_SMI_MONTHLY_V4 \
  -d ./data/smap_sss \
  -sd 2023-01-01T00:00:00Z \
  -ed 2023-12-31T23:59:59Z \
  -b="-130,25,-110,45"  # bounding box: min_lon,min_lat,max_lon,max_lat
```

#### Method 2: earthaccess Python Library

```python
import earthaccess
import xarray as xr

# Login
earthaccess.login()

# Search for SMAP SSS data
results = earthaccess.search_data(
    short_name='SMAP_RSS_L3_SSS_SMI_MONTHLY_V4',
    temporal=('2023-01-01', '2023-12-31'),
    bounding_box=(-130, 25, -110, 45)
)

# Download
files = earthaccess.download(results, "./data/smap_sss/")

# Open with xarray
ds = xr.open_mfdataset(files, combine='by_coords')
sss = ds['sss_smap']
```

#### Method 3: Direct OPeNDAP Access

```python
import xarray as xr

# OPeNDAP URL from PO.DAAC
opendap_url = "https://opendap.earthdata.nasa.gov/providers/POCLOUD/collections/[collection]/granules/[granule].nc"

# Requires authentication via .netrc
ds = xr.open_dataset(opendap_url)
```

#### Data Format and Resolution
- **Format**: netCDF-4, HDF5
- **Resolution**: 0.25° (~25km for RSS v4, 60km for JPL v5)
- **Temporal**: Daily, 8-day running mean, Monthly
- **Coverage**: Global (ice-free oceans)
- **Variables**: sea_surface_salinity, sss_smap

#### Rate Limits
- No explicit limits with NASA Earthdata authentication
- Recommended for bulk downloads: podaac-data-subscriber

---

## 6. NOAA NCEI - World Ocean Atlas 2018 Dissolved Oxygen

### Overview
World Ocean Atlas 2018 (WOA18) provides climatological fields of in situ dissolved oxygen, temperature, salinity, and nutrients.

### Product Information
- **Resolution**: 1° and 0.25° grids
- **Depth Levels**: Standard depth levels (0-5500m)
- **Temporal**: Annual, seasonal, monthly climatologies
- **Variables**: Dissolved Oxygen (O2), Apparent Oxygen Utilization (AOU), Oxygen Saturation

### Data Access Methods

#### Method 1: Direct Download from NOAA NCEI

**Web Interface:**
- https://www.ncei.noaa.gov/access/world-ocean-atlas-2018/
- https://www.ncei.noaa.gov/access/world-ocean-atlas-2018/bin/woa18oxnu.pl

**Data Formats:**
- NetCDF (.nc)
- CSV
- ASCII
- ArcGIS compatible

**Download URLs:**
```
Base: https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/
Oxygen: https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/oxygen/netcdf/
```

#### Method 2: THREDDS/OPeNDAP Access

**THREDDS Catalog:**
- https://www.ncei.noaa.gov/thredds-ocean/catalog.html

```python
import xarray as xr

# OPeNDAP access to WOA18 oxygen data
# Example URL structure (check THREDDS catalog for exact paths)
base_url = "https://www.ncei.noaa.gov/thredds-ocean/dodsC/woa18/"
file_path = "oxygen/netcdf/all/1.00/woa18_all_o00_01.nc"
opendap_url = base_url + file_path

# Open with xarray
# Note: Add '#fillmismatch' to URL if encountering _FillValue errors
ds = xr.open_dataset(opendap_url + "#fillmismatch")

# Access dissolved oxygen
o2 = ds['o_an']  # Oxygen annual mean
```

#### Method 3: Python Package - woa

There's an unofficial Python package for reading WOA data:
- GitHub: https://github.com/Lopezurrutia/woa

```bash
pip install git+https://github.com/Lopezurrutia/woa.git
```

#### Example - Download and Process WOA18 Oxygen

```python
import xarray as xr
import numpy as np
import requests

# Download specific file
url = "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/oxygen/netcdf/all/1.00/woa18_all_o00_01.nc"
response = requests.get(url)

with open('./data/woa18_oxygen_annual.nc', 'wb') as f:
    f.write(response.content)

# Load with xarray
ds = xr.open_dataset('./data/woa18_oxygen_annual.nc')

# Variables:
# o_an: Annual mean dissolved oxygen (ml/l or μmol/kg)
# o_sd: Standard deviation
# o_mn: Number of observations

# Extract surface oxygen for specific region
o2_surface = ds['o_an'].sel(depth=0, method='nearest')
o2_region = o2_surface.sel(
    lat=slice(25, 45),
    lon=slice(-130, -110)
)
```

#### Data Format
- **Format**: NetCDF-4
- **Variables**:
  - `o_an`: Dissolved oxygen climatology
  - `o_sd`: Standard deviation
  - `o_mn`, `o_dd`, `o_se`, `o_oa`: Statistical fields
- **Units**: ml/l or μmol/kg (check metadata)

#### Rate Limits
- No authentication required
- No rate limits for direct downloads
- THREDDS/OPeNDAP: reasonable use

---

## 7. GEBCO - GEBCO_2023 Bathymetry Grid

### Overview
General Bathymetric Chart of the Oceans (GEBCO) provides global bathymetric grids.

### Product Information
- **Resolution**: 15 arc-seconds (~450m at equator)
- **Coverage**: Global
- **Format**: NetCDF (2D array)
- **File Size**: ~7.5 GB (global grid)
- **Values**: Elevation in meters (negative for depths, positive for land)

### Data Access

#### Download from GEBCO Website

**Main Download Page:**
- https://download.gebco.net/

**Direct Download Options:**
1. **Full Global Grid**: GEBCO_2023 Grid (netCDF)
2. **Regional Subsets**: Use web interface to select region
3. **Sub-ice Topography**: GEBCO_2023 Sub Ice Grid

**Formats Available:**
- netCDF (recommended)
- GeoTIFF
- Esri ASCII
- Data GeoPackage

#### Download via Python

```python
import requests
import xarray as xr

# Direct download URL (check GEBCO website for current links)
# Note: For large downloads, GEBCO requires email for download link

# Example: Download regional subset
# Use GEBCO web interface to generate custom download URL

# For scripted downloads of the full grid:
url = "https://www.bodc.ac.uk/data/open_download/gebco/gebco_2023/zip/"

# Large file - consider using wget or curl for resumable download
import subprocess
subprocess.run(['wget', '-c', url, '-O', './data/GEBCO_2023.zip'])
```

#### Load GEBCO Data with xarray

```python
import xarray as xr
import numpy as np

# Load GEBCO netCDF file
ds = xr.open_dataset('./data/GEBCO_2023.nc')

# The main variable is 'elevation'
bathymetry = ds['elevation']

# Subset for region of interest
bathy_subset = bathymetry.sel(
    lat=slice(25, 45),
    lon=slice(-130, -110)
)

# Convert to depth (positive values)
depth = -bathy_subset.where(bathy_subset < 0, 0)
```

#### Alternative: PyGMT

PyGMT provides automatic download and caching of GEBCO data:

```bash
pip install pygmt
```

```python
import pygmt

# Load GEBCO grid (auto-downloads and caches)
grid = pygmt.datasets.load_earth_relief(
    resolution="15s",  # 15 arc-second resolution
    region=[-130, -110, 25, 45]  # West Coast example
)

# Returns xarray.DataArray
depth = -grid.where(grid < 0, 0)
```

#### Authentication/Registration
- **No authentication required**
- For very large downloads, may need to provide email address
- Terms of use agreement required

#### Citation
GEBCO Compilation Group (2023) GEBCO 2023 Grid (doi:10.5285/f98b053b-0cbc-6c23-e053-6c86abc0af7b)

---

## 8. Global Fishing Watch - Fishing Effort Data

### Overview
Global Fishing Watch provides apparent fishing effort data based on AIS vessel tracking, including gear-specific fishing activity.

### Product Information
- **Coverage**: Global oceans
- **Resolution**: 0.01° - 0.1° grids (varies by product)
- **Temporal**: Daily to monthly
- **Gear Types**: Includes longline, purse seines, trawlers, etc.

### Data Access

#### Registration Required
- Create account at: https://globalfishingwatch.org/
- Request API token from: GFW API Portal
- Free for non-commercial use

#### Python Package: gfw-api-python-client

**Installation:**
```bash
pip install gfw-api-python-client
```

**Authentication:**
```python
import gfwapiclient as gfw

# Initialize client with API token
gfw_client = gfw.Client(
    access_token="YOUR_GFW_API_ACCESS_TOKEN"
)
```

**Example - Query Fishing Effort by Gear Type:**

```python
import gfwapiclient as gfw
import pandas as pd
from datetime import datetime

# Initialize client
client = gfw.Client(access_token="YOUR_TOKEN")

# Query fishing effort for longline and purse seine vessels
# Using 4Wings API (gridded fishing effort)

# Define query parameters
params = {
    'datasets': ['public-global-fishing-effort:latest'],
    'date-range': '2023-01-01,2023-12-31',
    'region': {
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-130, 25],
                [-110, 25],
                [-110, 45],
                [-130, 45],
                [-130, 25]
            ]]
        }
    },
    'filters': [
        'geartype in ("tuna_purse_seines","drifting_longlines")'
    ],
    'temporal-resolution': 'monthly',
    'spatial-resolution': 0.1  # degrees
}

# Get fishing effort data
effort_data = client.get_4wings_data(**params)

# Convert to pandas DataFrame
df = pd.DataFrame(effort_data)
```

**Example - Search for Specific Vessels:**

```python
# Query vessels API
vessels = client.get_vessels(
    query='flag:"USA" AND geartype:("purse_seines" OR "drifting_longlines")',
    limit=100
)

# Get vessel events (fishing events, encounters, etc.)
vessel_id = vessels['entries'][0]['id']
events = client.get_events(
    vessel_id=vessel_id,
    start_date='2023-01-01',
    end_date='2023-12-31',
    event_types=['fishing']
)
```

#### Alternative: Download Pre-processed Data

GFW also provides downloadable datasets:
- https://globalfishingwatch.org/data-download/

Available formats:
- CSV
- Shapefile
- GeoJSON

#### Data Format
- **API Response**: JSON
- **Downloadable**: CSV, GeoJSON, Shapefile
- **Variables**:
  - Fishing hours
  - Vessel count
  - Gear type
  - Flag state
  - Grid cell location

#### Rate Limits
- API rate limits apply (check documentation)
- Recommend batching requests for large areas/time periods

#### Documentation
- https://globalfishingwatch.org/our-apis/documentation
- https://globalfishingwatch.github.io/gfw-api-python-client/

---

## 9. World Shipping Lanes Vector Data

### Overview
Shipping lane data from multiple sources showing major maritime traffic routes and regulations.

### Data Sources

#### 9.1 NOAA ENC Direct to GIS

**Overview:**
NOAA's Electronic Navigational Charts (ENC) Direct to GIS provides shipping lanes, traffic separation schemes, and maritime regulations.

**Data Access:**
- **ArcGIS Feature Server**:
  - https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/FeatureServer/0
- **Map Server**:
  - https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/MapServer/0

**Features Include:**
- Traffic lanes
- Traffic separation zones
- Precautionary areas
- Shipping safety fairways

**Data Format:**
- Shapefile (.shp)
- Geodatabase (.gdb)
- GeoJSON
- ArcGIS Feature Service

**Python Access - Using requests/geopandas:**

```python
import geopandas as gpd
import requests
import json

# Query ArcGIS REST API
base_url = "https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/FeatureServer/0"

# Get all features (may need pagination)
query_url = f"{base_url}/query"
params = {
    'where': '1=1',  # Get all features
    'outFields': '*',
    'f': 'geojson',
    'geometryType': 'esriGeometryEnvelope',
    'geometry': '-130,25,-110,45',  # bbox: minX,minY,maxX,maxY
    'inSR': '4326',
    'spatialRel': 'esriSpatialRelIntersects'
}

response = requests.get(query_url, params=params)
shipping_lanes_geojson = response.json()

# Load into GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(shipping_lanes_geojson['features'])
gdf.crs = 'EPSG:4326'

# Save to file
gdf.to_file('./data/shipping_lanes.shp')
```

**Alternative - Direct Shapefile Download:**
Visit https://encdirect.noaa.gov/ and use the web interface to download shapefiles.

#### 9.2 OpenStreetMap (OSM) Shipping Lanes

**Overview:**
OpenStreetMap contains shipping lane data tagged with maritime navigation tags.

**Tags Used:**
- `seamark:type=separation_boundary`
- `seamark:type=separation_zone`
- `seamark:type=traffic_lane`

**Python Access - Using OSMnx/Overpass API:**

```python
import osmnx as ox
import geopandas as gpd

# Install osmium or use Overpass API directly
# pip install osmnx

# Define bounding box
bbox = (45, 25, -110, -130)  # north, south, east, west

# Query OSM for shipping lanes using Overpass API
from OSMPythonTools.overpass import Overpass, overpassQueryBuilder

overpass = Overpass()

# Build query for shipping lanes
query = overpassQueryBuilder(
    bbox=bbox,
    elementType=['way', 'relation'],
    selector=[
        '"seamark:type"="separation_zone"',
        '"seamark:type"="traffic_lane"'
    ],
    out='body'
)

result = overpass.query(query)

# Convert to GeoDataFrame
# (requires additional processing of OSM result)
```

**Alternative - Use Geofabrik Downloads:**
Download OSM data extracts from https://download.geofabrik.de/

#### 9.3 Marine Traffic Routes (GitHub)

**Repository:**
- https://github.com/newzealandpaul/Shipping-Lanes

```bash
git clone https://github.com/newzealandpaul/Shipping-Lanes.git
```

Load shapefile:
```python
import geopandas as gpd

shipping = gpd.read_file('./Shipping-Lanes/shipping_lanes.shp')
```

#### 9.4 NOAA Voluntary Observing Ship (VOS) Routes

**Overview:**
NOAA Science on a Sphere provides shipping route density data based on actual vessel observations.

**Access:**
- https://sos.noaa.gov/catalog/datasets/shipping-routes-with-labels-one-year/

**Data Format:**
- Raster density grids
- KML/KMZ for visualization

#### Authentication/Registration
- **NOAA ENC Direct**: No authentication required
- **OSM**: No authentication required
- **GitHub repositories**: No authentication required

#### Recommended Approach for Python

```python
import geopandas as gpd
import requests

def download_noaa_shipping_lanes(bbox, output_file):
    """
    Download shipping lanes from NOAA ENC Direct

    Parameters:
    bbox: tuple (min_lon, min_lat, max_lon, max_lat)
    output_file: str, path to save shapefile
    """
    base_url = "https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/FeatureServer/0/query"

    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'geometry': f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outSR': '4326'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    gdf = gpd.GeoDataFrame.from_features(data['features'])
    gdf.crs = 'EPSG:4326'

    gdf.to_file(output_file)
    return gdf

# Usage
bbox = (-130, 25, -110, 45)
lanes = download_noaa_shipping_lanes(bbox, './data/shipping_lanes.shp')
```

---

## Summary Table: Data Sources Quick Reference

| Data Source | Authentication | Python Package | Resolution | Format |
|------------|---------------|----------------|------------|---------|
| OCEARCH | Permission required | Custom requests | Point data | JSON |
| GBIF | Free account (downloads) | pygbif | Occurrence points | JSON/CSV |
| OBIS | None | pyobis | Occurrence points | JSON |
| MODIS-Aqua SST/Chl | NASA Earthdata | earthaccess, erddapy | 4km | netCDF/HDF |
| CMEMS Sea Level | Free account | copernicusmarine | 0.25° | netCDF/Zarr |
| SMAP Salinity | NASA Earthdata | earthaccess, podaac-data-subscriber | 0.25° | netCDF/HDF5 |
| WOA18 O2 | None | xarray | 1° or 0.25° | netCDF |
| GEBCO Bathymetry | None | xarray, pygmt | 15 arc-sec | netCDF/GeoTIFF |
| Global Fishing Watch | Free API token | gfw-api-python-client | 0.01-0.1° | JSON/CSV |
| Shipping Lanes | None | geopandas, requests | Vector | GeoJSON/Shapefile |

---

## Complete Python Environment Setup

### Recommended Installation

```bash
# Create conda environment
conda create -n shark_habitat python=3.10 -y
conda activate shark_habitat

# Core scientific packages
conda install -c conda-forge xarray netcdf4 pandas numpy matplotlib -y

# Geospatial packages
conda install -c conda-forge geopandas cartopy rasterio -y

# Data access packages
pip install pygbif pyobis earthaccess erddapy
pip install copernicusmarine podaac-data-subscriber
pip install gfw-api-python-client
pip install pygmt

# Optional but useful
conda install -c conda-forge jupyterlab hvplot datashader -y
```

### Complete Example Workflow

```python
"""
White Shark Habitat Modeling - Data Collection Script
Complete workflow for downloading all required data sources
"""

import earthaccess
import xarray as xr
import geopandas as gpd
import pandas as pd
from pygbif import occurrences as gbif_occ
from pyobis import occurrences as obis_occ
import copernicusmarine
import requests
from datetime import datetime

# Configuration
REGION = {
    'min_lon': -130,
    'max_lon': -110,
    'min_lat': 25,
    'max_lat': 45
}
TIME_RANGE = ('2020-01-01', '2023-12-31')
DATA_DIR = './data/'

# 1. Download MODIS-Aqua SST and Chlorophyll
print("Downloading MODIS-Aqua data...")
earthaccess.login()

# SST
sst_results = earthaccess.search_data(
    short_name='MODIS_AQUA_L3_SST_THERMAL_MONTHLY_4KM_DAYTIME_V2019.0',
    temporal=TIME_RANGE,
    bounding_box=(REGION['min_lon'], REGION['min_lat'],
                  REGION['max_lon'], REGION['max_lat'])
)
sst_files = earthaccess.download(sst_results, f"{DATA_DIR}/modis_sst/")

# Chlorophyll
chl_results = earthaccess.search_data(
    short_name='MODISA_L3m_CHL',
    temporal=TIME_RANGE
)
chl_files = earthaccess.download(chl_results[:50], f"{DATA_DIR}/modis_chl/")

# 2. Download SMAP Sea Surface Salinity
print("Downloading SMAP salinity...")
smap_results = earthaccess.search_data(
    short_name='SMAP_RSS_L3_SSS_SMI_MONTHLY_V4',
    temporal=TIME_RANGE,
    bounding_box=(REGION['min_lon'], REGION['min_lat'],
                  REGION['max_lon'], REGION['max_lat'])
)
smap_files = earthaccess.download(smap_results, f"{DATA_DIR}/smap_sss/")

# 3. Download Copernicus Sea Level Anomaly
print("Downloading sea level anomaly...")
copernicusmarine.subset(
    dataset_id="cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D",
    variables=["sla", "adt"],
    minimum_longitude=REGION['min_lon'],
    maximum_longitude=REGION['max_lon'],
    minimum_latitude=REGION['min_lat'],
    maximum_latitude=REGION['max_lat'],
    start_datetime=TIME_RANGE[0],
    end_datetime=TIME_RANGE[1],
    output_filename="sea_level_anomaly.nc",
    output_directory=f"{DATA_DIR}/cmems/"
)

# 4. Download World Ocean Atlas 2018 Dissolved Oxygen
print("Downloading WOA18 oxygen...")
woa_url = "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/oxygen/netcdf/all/1.00/woa18_all_o00_01.nc"
response = requests.get(woa_url)
with open(f'{DATA_DIR}/woa18_oxygen.nc', 'wb') as f:
    f.write(response.content)

# 5. Download GEBCO Bathymetry
print("Downloading bathymetry...")
import pygmt
bathy = pygmt.datasets.load_earth_relief(
    resolution="15s",
    region=[REGION['min_lon'], REGION['max_lon'],
            REGION['min_lat'], REGION['max_lat']]
)
bathy.to_netcdf(f'{DATA_DIR}/gebco_bathymetry.nc')

# 6. Download Marine Mammal Occurrences (OBIS)
print("Downloading marine mammal observations...")
species_list = [
    "Zalophus californianus",
    "Mirounga angustirostris",
    "Arctocephalus pusillus",
    "Phoca vitulina",
    "Orcinus orca"
]

mammal_data = []
for species in species_list:
    result = obis_occ.search(scientificname=species, size=10000)
    if result['results']:
        df = pd.DataFrame(result['results'])
        df['species'] = species
        mammal_data.append(df)

mammal_df = pd.concat(mammal_data, ignore_index=True)
mammal_df.to_csv(f'{DATA_DIR}/marine_mammal_occurrences.csv', index=False)

# 7. Download Shipping Lanes
print("Downloading shipping lanes...")
def download_shipping_lanes(bbox, output_file):
    base_url = "https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/FeatureServer/0/query"
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'geometry': f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326'
    }
    response = requests.get(base_url, params=params)
    gdf = gpd.GeoDataFrame.from_features(response.json()['features'])
    gdf.crs = 'EPSG:4326'
    gdf.to_file(output_file)
    return gdf

bbox = (REGION['min_lon'], REGION['min_lat'], REGION['max_lon'], REGION['max_lat'])
shipping = download_shipping_lanes(bbox, f'{DATA_DIR}/shipping_lanes.shp')

# 8. Note: For OCEARCH and Global Fishing Watch
# Require specific permissions/API tokens - contact providers directly

print("Data download complete!")
print(f"All data saved to {DATA_DIR}")
```

---

## Additional Resources

### NASA Earthdata
- Search Interface: https://search.earthdata.nasa.gov/
- earthaccess Docs: https://earthaccess.readthedocs.io/

### Copernicus Marine
- Data Store: https://data.marine.copernicus.eu/
- Toolbox Docs: https://toolbox-docs.marine.copernicus.eu/

### GBIF
- Data Portal: https://www.gbif.org/
- API Docs: https://techdocs.gbif.org/en/openapi/
- pygbif Docs: https://pygbif.readthedocs.io/

### OBIS
- Data Portal: https://obis.org/
- Manual: https://manual.obis.org/
- pyobis Docs: https://iobis.github.io/pyobis/

### Global Fishing Watch
- Portal: https://globalfishingwatch.org/
- API Docs: https://globalfishingwatch.org/our-apis/documentation

---

## Citation Information

When using these data sources, please cite appropriately:

**MODIS-Aqua**: NASA Goddard Space Flight Center, Ocean Ecology Laboratory, Ocean Biology Processing Group. (Year). Moderate-resolution Imaging Spectroradiometer (MODIS) Aqua {Product} Data. NASA OB.DAAC, Greenbelt, MD, USA.

**SMAP**: Remote Sensing Systems. (Year). SMAP Ocean Surface Salinities Level 3 Running {temporal} Mean. Ver. {version}. PO.DAAC, CA, USA.

**Copernicus Marine**: E.U. Copernicus Marine Service Information; Global Ocean Gridded L4 Sea Surface Heights And Derived Variables Reprocessed (1993-ongoing) (SEALEVEL_GLO_PHY_L4_MY_008_047)

**WOA18**: Garcia, H.E., et al. (2018). World Ocean Atlas 2018. NOAA National Centers for Environmental Information.

**GEBCO**: GEBCO Compilation Group (2023) GEBCO 2023 Grid. DOI:10.5285/f98b053b-0cbc-6c23-e053-6c86abc0af7b

**GBIF**: GBIF.org (Date). GBIF Occurrence Download https://doi.org/{DOI}

**OBIS**: Ocean Biodiversity Information System. Intergovernmental Oceanographic Commission of UNESCO. www.obis.org

**Global Fishing Watch**: Global Fishing Watch (Year). {Dataset name}. Downloaded from https://globalfishingwatch.org

---

*Document compiled: 2025-10-05*
*For white shark (Carcharodon carcharias) habitat modeling project*
