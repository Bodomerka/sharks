"""
GEBCO Bathymetry data collector
Збір даних батиметрії (рельєф дна)
"""

import pygmt
import xarray as xr
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GEBCOCollector:
    """Collector for GEBCO bathymetry data"""

    def __init__(self, data_dir: str = "./data/raw/gebco"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_bathymetry(self, bbox: dict, resolution: str = "15s",
                           save: bool = True) -> xr.DataArray:
        logger.info("Downloading GEBCO bathymetry data...")
        logger.info(f"Region: {bbox}, Resolution: {resolution}")

        # Використати pygmt для автоматичного завантаження
        grid = pygmt.datasets.load_earth_relief(
            resolution=resolution,
            region=[bbox['min_lon'], bbox['max_lon'],
                   bbox['min_lat'], bbox['max_lat']]
        )

        logger.info(f"Loaded bathymetry grid: {grid}")

        if save:
            output_file = self.data_dir / f"gebco_bathymetry_{resolution}.nc"
            grid.to_netcdf(output_file)
            logger.info(f"Saved to {output_file}")

        return grid


def main():
    collector = GEBCOCollector()
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    bathy_data = collector.download_bathymetry(bbox, resolution="15s", save=True)


if __name__ == "__main__":
    main()
