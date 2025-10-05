"""
NASA OceanColor data collector
Збір даних MODIS-Aqua: SST (Sea Surface Temperature) та Chlorophyll-a
"""

import earthaccess
import xarray as xr
import numpy as np
from pathlib import Path
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NASAOceanCollector:
    """
    Collector for NASA OceanColor data (MODIS-Aqua SST and Chlorophyll-a)
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        data_dir: str = "./data/raw/nasa_ocean"
    ):
        """
        Parameters:
        -----------
        username : str, optional
            NASA Earthdata username
        password : str, optional
            NASA Earthdata password
        data_dir : str
            Директорія для збереження даних
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Аутентифікація
        if username and password:
            earthaccess.login(strategy="environment")
        else:
            # Інтерактивний логін або з .netrc
            earthaccess.login()

    def download_modis_sst(
        self,
        date_range: Tuple[str, str],
        bbox: Optional[dict] = None,
        temporal_resolution: str = "monthly",
        save: bool = True
    ) -> xr.Dataset:
        """
        Завантажити дані MODIS SST

        Parameters:
        -----------
        date_range : tuple
            (start_date, end_date) як ('YYYY-MM-DD', 'YYYY-MM-DD')
        bbox : dict, optional
            Bounding box
        temporal_resolution : str
            'monthly' or '8day'
        save : bool
            Зберегти файли

        Returns:
        --------
        ds : xr.Dataset
            Dataset з SST
        """
        logger.info(f"Downloading MODIS SST data for {date_range}...")

        # Визначити short_name на основі роздільності
        if temporal_resolution == "monthly":
            short_name = "MODIS_AQUA_L3_SST_THERMAL_MONTHLY_4KM_DAYTIME_V2019.0"
        else:
            short_name = "MODIS_AQUA_L3_SST_THERMAL_8DAY_4KM_DAYTIME_V2019.0"

        # Пошук даних
        results = earthaccess.search_data(
            short_name=short_name,
            temporal=date_range,
            bounding_box=(bbox['min_lon'], bbox['min_lat'],
                         bbox['max_lon'], bbox['max_lat']) if bbox else None
        )

        logger.info(f"Found {len(results)} granules")

        if not results:
            logger.warning("No data found")
            return None

        # Завантажити файли
        if save:
            output_dir = self.data_dir / "modis_sst"
            output_dir.mkdir(exist_ok=True)
            files = earthaccess.download(results, str(output_dir))
        else:
            # Відкрити без завантаження
            files = earthaccess.open(results)

        # Відкрити як xarray Dataset
        ds = xr.open_mfdataset(files, combine='by_coords', engine='netcdf4')

        logger.info(f"Loaded SST data: {ds}")

        return ds

    def download_modis_chlorophyll(
        self,
        date_range: Tuple[str, str],
        bbox: Optional[dict] = None,
        save: bool = True
    ) -> xr.Dataset:
        """
        Завантажити дані MODIS Chlorophyll-a

        Parameters:
        -----------
        date_range : tuple
            (start_date, end_date)
        bbox : dict, optional
            Bounding box
        save : bool
            Зберегти файли

        Returns:
        --------
        ds : xr.Dataset
        """
        logger.info(f"Downloading MODIS Chlorophyll-a data for {date_range}...")

        short_name = "MODISA_L3m_CHL"

        # Пошук
        results = earthaccess.search_data(
            short_name=short_name,
            temporal=date_range,
            bounding_box=(bbox['min_lon'], bbox['min_lat'],
                         bbox['max_lon'], bbox['max_lat']) if bbox else None
        )

        logger.info(f"Found {len(results)} granules")

        if not results:
            logger.warning("No data found")
            return None

        # Завантажити
        if save:
            output_dir = self.data_dir / "modis_chlorophyll"
            output_dir.mkdir(exist_ok=True)
            files = earthaccess.download(results, str(output_dir))
        else:
            files = earthaccess.open(results)

        # Відкрити
        ds = xr.open_mfdataset(files, combine='by_coords', engine='netcdf4')

        logger.info(f"Loaded Chlorophyll data: {ds}")

        return ds


def main():
    """
    Приклад використання
    """
    collector = NASAOceanCollector()

    bbox = {
        'min_lon': -130,
        'max_lon': -110,
        'min_lat': 25,
        'max_lat': 45
    }

    date_range = ("2020-01-01", "2023-12-31")

    # Завантажити SST
    sst_data = collector.download_modis_sst(date_range, bbox, save=True)

    # Завантажити Chlorophyll
    chl_data = collector.download_modis_chlorophyll(date_range, bbox, save=True)


if __name__ == "__main__":
    main()
