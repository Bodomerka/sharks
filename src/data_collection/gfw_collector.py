"""
Global Fishing Watch data collector
Збір даних про рибальське зусилля
"""

import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GFWCollector:
    """Collector for Global Fishing Watch fishing effort data"""

    def __init__(self, api_token: str = None, data_dir: str = "./data/raw/gfw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.api_token = api_token

    def download_fishing_effort(self, date_range: tuple, bbox: dict,
                                gear_types: list = None, save: bool = True):
        logger.info("Downloading Global Fishing Watch data...")

        if not self.api_token:
            logger.error("GFW API token required. Get from: https://globalfishingwatch.org/our-apis/tokens")
            logger.info("Alternative: Download data manually from https://globalfishingwatch.org/data-download/")
            return None

        try:
            import gfwapiclient as gfw

            client = gfw.Client(access_token=self.api_token)

            if gear_types is None:
                gear_types = ["tuna_purse_seines", "drifting_longlines"]

            gear_filter = ','.join([f'"{g}"' for g in gear_types])

            params = {
                'datasets': ['public-global-fishing-effort:latest'],
                'date-range': f'{date_range[0]},{date_range[1]}',
                'region': {
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [bbox['min_lon'], bbox['min_lat']],
                            [bbox['max_lon'], bbox['min_lat']],
                            [bbox['max_lon'], bbox['max_lat']],
                            [bbox['min_lon'], bbox['max_lat']],
                            [bbox['min_lon'], bbox['min_lat']]
                        ]]
                    }
                },
                'filters': [f'geartype in ({gear_filter})'],
                'temporal-resolution': 'monthly',
                'spatial-resolution': 0.1
            }

            effort_data = client.get_4wings_data(**params)
            df = pd.DataFrame(effort_data)

            logger.info(f"Downloaded {len(df)} fishing effort records")

            if save:
                output_file = self.data_dir / "fishing_effort.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"Saved to {output_file}")

            return df

        except ImportError:
            logger.error("gfw-api-python-client not installed. Install: pip install gfw-api-python-client")
            return None
        except Exception as e:
            logger.error(f"Error downloading GFW data: {e}")
            return None


def main():
    # Requires API token
    collector = GFWCollector(api_token="YOUR_TOKEN_HERE")
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    date_range = ("2020-01-01", "2023-12-31")
    fishing_data = collector.download_fishing_effort(date_range, bbox, save=True)


if __name__ == "__main__":
    main()
