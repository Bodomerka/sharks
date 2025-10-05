"""
Shipping Lanes data collector
Збір даних про морські шляхи судноплавства
"""

import requests
import geopandas as gpd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShippingLanesCollector:
    """Collector for shipping lanes data from NOAA"""

    def __init__(self, data_dir: str = "./data/raw/shipping"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://encdirect.noaa.gov/arcgis/rest/services/NavigationChartData/MarineTransportation/FeatureServer/0/query"

    def download_shipping_lanes(self, bbox: dict, save: bool = True) -> gpd.GeoDataFrame:
        logger.info("Downloading shipping lanes from NOAA...")

        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'geometry': f'{bbox["min_lon"]},{bbox["min_lat"]},{bbox["max_lon"]},{bbox["max_lat"]}',
            'geometryType': 'esriGeometryEnvelope',
            'spatialRel': 'esriSpatialRelIntersects',
            'inSR': '4326',
            'outSR': '4326'
        }

        response = requests.get(self.base_url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        if 'features' not in data or not data['features']:
            logger.warning("No shipping lanes found in this region")
            return gpd.GeoDataFrame()

        gdf = gpd.GeoDataFrame.from_features(data['features'])
        gdf.crs = 'EPSG:4326'

        logger.info(f"Downloaded {len(gdf)} shipping lane features")

        if save:
            output_file = self.data_dir / "shipping_lanes.gpkg"
            gdf.to_file(output_file, driver="GPKG")
            logger.info(f"Saved to {output_file}")

        return gdf


def main():
    collector = ShippingLanesCollector()
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    lanes = collector.download_shipping_lanes(bbox, save=True)


if __name__ == "__main__":
    main()
