"""
Copernicus Marine data collector
Збір даних Sea Surface Height Anomaly (SSHA)
"""

import copernicusmarine
import xarray as xr
from pathlib import Path
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CopernicusCollector:
    """Collector for Copernicus Marine sea level data"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 data_dir: str = "./data/raw/copernicus"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.username = username
        self.password = password

    def download_sea_level_anomaly(self, date_range: Tuple[str, str], bbox: dict,
                                   save: bool = True) -> xr.Dataset:
        logger.info(f"Downloading Sea Level Anomaly data for {date_range}...")

        dataset_id = "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D"

        output_file = self.data_dir / f"sla_{date_range[0]}_{date_range[1]}.nc"

        if save:
            copernicusmarine.subset(
                dataset_id=dataset_id,
                variables=["sla", "adt"],
                minimum_longitude=bbox['min_lon'],
                maximum_longitude=bbox['max_lon'],
                minimum_latitude=bbox['min_lat'],
                maximum_latitude=bbox['max_lat'],
                start_datetime=date_range[0],
                end_datetime=date_range[1],
                output_filename=output_file.name,
                output_directory=str(self.data_dir)
            )
            ds = xr.open_dataset(output_file)
        else:
            ds = copernicusmarine.open_dataset(
                dataset_id=dataset_id,
                minimum_longitude=bbox['min_lon'],
                maximum_longitude=bbox['max_lon'],
                minimum_latitude=bbox['min_lat'],
                maximum_latitude=bbox['max_lat'],
                start_datetime=date_range[0],
                end_datetime=date_range[1]
            )

        logger.info(f"Loaded SLA data: {ds}")
        return ds


def main():
    collector = CopernicusCollector()
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    date_range = ("2020-01-01", "2023-12-31")
    sla_data = collector.download_sea_level_anomaly(date_range, bbox, save=True)


if __name__ == "__main__":
    main()
