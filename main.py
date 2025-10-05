"""
Shark Voyager AI - Main Orchestration Script
Головний скрипт для збору та обробки даних

Usage:
    python main.py --config config/config.yaml --step all
    python main.py --step collect
    python main.py --step process
    python main.py --step integrate
"""

import argparse
import logging
from pathlib import Path
import sys

# Додати src до Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.config_loader import load_config, get_bbox, get_date_range, create_output_paths

# Data collectors
from data_collection.ocearch_collector import OCEARCHCollector
from data_collection.gbif_obis_collector import GBIFOBISCollector
from data_collection.nasa_ocean_collector import NASAOceanCollector
from data_collection.copernicus_collector import CopernicusCollector
from data_collection.smap_collector import SMAPCollector
from data_collection.woa_collector import WOACollector
from data_collection.gebco_collector import GEBCOCollector
from data_collection.gfw_collector import GFWCollector
from data_collection.shipping_lanes_collector import ShippingLanesCollector

# Processing
from processing.standardize_data import DataStandardizer

# Synthetic
from synthetic.generate_absence_points import AbsencePointsGenerator
from synthetic.nursery_index import NurserySuitabilityCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SharkVoyagerPipeline:
    """Головний pipeline для проєкту Shark Voyager AI"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Parameters:
        -----------
        config_path : str
            Шлях до конфігураційного файлу
        """
        logger.info("=" * 70)
        logger.info("SHARK VOYAGER AI - Data Collection and Processing Pipeline")
        logger.info("=" * 70)

        # Завантажити конфігурацію
        self.config = load_config(config_path)
        logger.info(f"Configuration loaded from {config_path}")

        # Створити вихідні директорії
        self.paths = create_output_paths(self.config)

        # Параметри
        self.bbox = get_bbox(self.config)
        self.date_range = get_date_range(self.config)

        logger.info(f"Study area: {self.bbox}")
        logger.info(f"Date range: {self.date_range}")

    def step_1_collect_data(self):
        """Крок 1: Збір даних з усіх джерел"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: DATA COLLECTION")
        logger.info("=" * 70 + "\n")

        # 1. OCEARCH Shark Tracks
        logger.info("1/9: Collecting OCEARCH shark tracks...")
        logger.warning("OCEARCH requires permission - see data_collection/ocearch_collector.py")
        # ocearch = OCEARCHCollector()
        # shark_tracks = ocearch.collect_all_white_shark_tracks(save=True)

        # 2. GBIF/OBIS - Marine Mammals and Orcas
        logger.info("2/9: Collecting marine mammal and orca data...")
        gbif_obis = GBIFOBISCollector()

        prey_species = [sp['scientific_name'] for sp in self.config['prey_species']]
        prey_data = gbif_obis.collect_prey_species(prey_species, self.bbox, save=True)
        orca_data = gbif_obis.collect_orca_data(self.bbox, save=True)

        # Визначити колонії
        if not prey_data.empty:
            rookeries = gbif_obis.filter_rookeries(prey_data, min_observations=10)
            rookeries.to_file(
                self.paths['data_raw'] / "biodiversity" / "marine_mammal_rookeries.gpkg",
                driver="GPKG"
            )

        # 3. NASA OceanColor - MODIS SST and Chlorophyll
        logger.info("3/9: Collecting MODIS SST and Chlorophyll data...")
        nasa_creds = self.config.get('credentials', {}).get('nasa_earthdata', {})
        nasa = NASAOceanCollector(
            username=nasa_creds.get('username'),
            password=nasa_creds.get('password')
        )
        sst_data = nasa.download_modis_sst(self.date_range, self.bbox, save=True)
        chl_data = nasa.download_modis_chlorophyll(self.date_range, self.bbox, save=True)

        # 4. Copernicus Marine - Sea Level Anomaly
        logger.info("4/9: Collecting Sea Level Anomaly data...")
        copernicus_creds = self.config.get('credentials', {}).get('copernicus_marine', {})
        copernicus = CopernicusCollector(
            username=copernicus_creds.get('username'),
            password=copernicus_creds.get('password')
        )
        sla_data = copernicus.download_sea_level_anomaly(self.date_range, self.bbox, save=True)

        # 5. SMAP - Sea Surface Salinity
        logger.info("5/9: Collecting SMAP Salinity data...")
        smap = SMAPCollector(
            username=nasa_creds.get('username'),
            password=nasa_creds.get('password')
        )
        salinity_data = smap.download_salinity(self.date_range, self.bbox, save=True)

        # 6. WOA - Dissolved Oxygen
        logger.info("6/9: Collecting WOA Dissolved Oxygen data...")
        woa = WOACollector()
        oxygen_data = woa.download_oxygen(save=True)

        # 7. GEBCO - Bathymetry
        logger.info("7/9: Collecting GEBCO Bathymetry data...")
        gebco = GEBCOCollector()
        bathy_data = gebco.download_bathymetry(self.bbox, resolution="15s", save=True)

        # 8. Global Fishing Watch
        logger.info("8/9: Collecting Global Fishing Watch data...")
        logger.warning("GFW requires API token - see config/config.yaml")
        # gfw_token = self.config['credentials']['global_fishing_watch']['api_token']
        # gfw = GFWCollector(api_token=gfw_token)
        # fishing_data = gfw.download_fishing_effort(self.date_range, self.bbox, save=True)

        # 9. Shipping Lanes
        logger.info("9/9: Collecting Shipping Lanes data...")
        shipping = ShippingLanesCollector()
        lanes_data = shipping.download_shipping_lanes(self.bbox, save=True)

        logger.info("\nStep 1: Data collection completed!")

    def step_2_process_data(self):
        """Крок 2: Стандартизація та обробка даних"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: DATA PROCESSING AND STANDARDIZATION")
        logger.info("=" * 70 + "\n")

        standardizer = DataStandardizer(self.bbox, resolution=0.1)

        # Тут потрібно завантажити збережені дані та обробити їх
        # Приклад структури:

        # logger.info("Processing SST data...")
        # sst_ds = xr.open_mfdataset("./data/raw/nasa_ocean/modis_sst/*.nc")
        # standardizer.process_sst(sst_ds)

        # logger.info("Processing Chlorophyll data...")
        # chl_ds = xr.open_mfdataset("./data/raw/nasa_ocean/modis_chlorophyll/*.nc")
        # standardizer.process_chlorophyll(chl_ds)

        # logger.info("Processing Bathymetry...")
        # bathy = xr.open_dataarray("./data/raw/gebco/gebco_bathymetry_15s.nc")
        # standardizer.process_bathymetry(bathy)

        # і т.д. для інших даних...

        logger.info("\nStep 2: Data processing completed!")

    def step_3_generate_synthetic(self):
        """Крок 3: Генерація синтетичних змінних"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: GENERATE SYNTHETIC VARIABLES")
        logger.info("=" * 70 + "\n")

        # 1. Генерувати точки відсутності
        logger.info("Generating absence points...")

        # absence_gen = AbsencePointsGenerator(buffer_distance_km=100)
        # presence_points = gpd.read_file("./data/raw/ocearch/white_shark_tracks.gpkg")
        # absence_datasets = absence_gen.generate_for_all_life_stages(
        #     presence_points, self.bbox, save=True
        # )

        # 2. Розрахувати Nursery Suitability Index
        logger.info("Calculating Nursery Suitability Index...")

        # nursery_calc = NurserySuitabilityCalculator()
        # nursery_index = nursery_calc.calculate_from_files(
        #     depth_file="./data/processed/Depth.tif",
        #     slope_file="./data/processed/Slope.tif",
        #     sst_files=["./data/processed/SST_weekly.nc"],
        #     chlorophyll_files=["./data/processed/Chlorophyll_weekly.nc"],
        #     save=True
        # )

        logger.info("\nStep 3: Synthetic variables generated!")

    def step_4_integrate_data(self):
        """Крок 4: Інтеграція всіх даних"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: DATA INTEGRATION")
        logger.info("=" * 70 + "\n")

        # Об'єднати всі растрові шари
        # Створити фінальний датасет для ML моделей

        logger.info("Integrating all data layers...")
        logger.info("\nStep 4: Data integration completed!")

    def run_all(self):
        """Виконати весь pipeline"""
        logger.info("\nRunning complete pipeline...\n")

        self.step_1_collect_data()
        self.step_2_process_data()
        self.step_3_generate_synthetic()
        self.step_4_integrate_data()

        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Shark Voyager AI - Data Collection and Processing Pipeline"
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--step',
        type=str,
        choices=['all', 'collect', 'process', 'synthetic', 'integrate'],
        default='all',
        help='Pipeline step to run'
    )

    args = parser.parse_args()

    # Створити pipeline
    pipeline = SharkVoyagerPipeline(config_path=args.config)

    # Виконати вибраний крок
    if args.step == 'all':
        pipeline.run_all()
    elif args.step == 'collect':
        pipeline.step_1_collect_data()
    elif args.step == 'process':
        pipeline.step_2_process_data()
    elif args.step == 'synthetic':
        pipeline.step_3_generate_synthetic()
    elif args.step == 'integrate':
        pipeline.step_4_integrate_data()


if __name__ == "__main__":
    main()
