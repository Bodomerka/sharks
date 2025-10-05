"""
SMAP Sea Surface Salinity data collector
Збір даних солоності морської поверхні
"""

import earthaccess
import xarray as xr
from pathlib import Path
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMAPCollector:
    """Collector for SMAP sea surface salinity data"""

    def __init__(self, data_dir: str = "./data/raw/smap"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        earthaccess.login()

    def download_salinity(self, date_range: Tuple[str, str], bbox: dict,
                         save: bool = True) -> xr.Dataset:
        logger.info(f"Downloading SMAP Salinity data for {date_range}...")

        short_name = "SMAP_RSS_L3_SSS_SMI_MONTHLY_V4"

        results = earthaccess.search_data(
            short_name=short_name,
            temporal=date_range,
            bounding_box=(bbox['min_lon'], bbox['min_lat'],
                         bbox['max_lon'], bbox['max_lat'])
        )

        logger.info(f"Found {len(results)} granules")

        if save:
            files = earthaccess.download(results, str(self.data_dir))
        else:
            files = earthaccess.open(results)

        ds = xr.open_mfdataset(files, combine='by_coords')
        logger.info(f"Loaded Salinity data: {ds}")
        return ds


def main():
    collector = SMAPCollector()
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    date_range = ("2020-01-01", "2023-12-31")
    salinity_data = collector.download_salinity(date_range, bbox, save=True)


if __name__ == "__main__":
    main()
