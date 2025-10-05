"""
World Ocean Atlas 2018 Dissolved Oxygen collector
Збір кліматологічних даних про розчинений кисень
"""

import requests
import xarray as xr
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WOACollector:
    """Collector for World Ocean Atlas dissolved oxygen data"""

    def __init__(self, data_dir: str = "./data/raw/woa"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/oxygen/netcdf/all/1.00/"

    def download_oxygen(self, temporal: str = "annual", resolution: str = "1.00",
                       save: bool = True) -> xr.Dataset:
        logger.info("Downloading WOA18 Dissolved Oxygen data...")

        # Annual climatology, 1 degree resolution
        filename = f"woa18_all_o00_01.nc"
        url = self.base_url + filename

        output_file = self.data_dir / filename

        if not output_file.exists() or not save:
            logger.info(f"Downloading from {url}...")
            response = requests.get(url, timeout=300)
            response.raise_for_status()

            if save:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved to {output_file}")

        ds = xr.open_dataset(output_file)
        logger.info(f"Loaded Oxygen data: {ds}")
        return ds


def main():
    collector = WOACollector()
    oxygen_data = collector.download_oxygen(save=True)


if __name__ == "__main__":
    main()
