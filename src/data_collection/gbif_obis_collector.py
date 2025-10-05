"""
GBIF/OBIS data collector
Збір даних про морських ссавців (здобич) та косаток (конкуренти/хижаки)
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pygbif import occurrences as gbif_occ
from pygbif import species as gbif_species
from pyobis import occurrences as obis_occ
from typing import List, Optional
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GBIFOBISCollector:
    """
    Collector for marine mammal and orca observations from GBIF/OBIS
    """

    def __init__(self, data_dir: str = "./data/raw/biodiversity"):
        """
        Parameters:
        -----------
        data_dir : str
            Директорія для збереження даних
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def collect_from_obis(
        self,
        species_name: str,
        bbox: Optional[dict] = None,
        max_records: int = 10000
    ) -> gpd.GeoDataFrame:
        """
        Зібрати дані з OBIS для конкретного виду

        Parameters:
        -----------
        species_name : str
            Наукова назва виду
        bbox : dict, optional
            Bounding box (min_lon, max_lon, min_lat, max_lat)
        max_records : int
            Максимальна кількість записів

        Returns:
        --------
        gdf : gpd.GeoDataFrame
            GeoDataFrame зі спостереженнями
        """
        logger.info(f"Collecting OBIS data for {species_name}...")

        try:
            # Параметри запиту
            params = {
                'scientificname': species_name,
                'size': max_records
            }

            # Додати bbox, якщо вказано
            if bbox:
                params['geometry'] = (
                    f"POLYGON(("
                    f"{bbox['min_lon']} {bbox['min_lat']}, "
                    f"{bbox['max_lon']} {bbox['min_lat']}, "
                    f"{bbox['max_lon']} {bbox['max_lat']}, "
                    f"{bbox['min_lon']} {bbox['max_lat']}, "
                    f"{bbox['min_lon']} {bbox['min_lat']}))"
                )

            # Виконати запит
            result = obis_occ.search(**params)

            if not result or 'results' not in result or not result['results']:
                logger.warning(f"No records found for {species_name}")
                return gpd.GeoDataFrame()

            # Конвертувати в DataFrame
            df = pd.DataFrame(result['results'])

            # Фільтрувати записи з координатами
            df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])

            # Створити GeoDataFrame
            geometry = [
                Point(row['decimalLongitude'], row['decimalLatitude'])
                for _, row in df.iterrows()
            ]

            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

            # Додати назву виду
            gdf['Species'] = species_name

            logger.info(f"Found {len(gdf)} records for {species_name}")

            return gdf

        except Exception as e:
            logger.error(f"Error collecting OBIS data: {e}")
            return gpd.GeoDataFrame()

    def collect_from_gbif(
        self,
        species_name: str,
        bbox: Optional[dict] = None,
        limit: int = 10000
    ) -> gpd.GeoDataFrame:
        """
        Зібрати дані з GBIF для конкретного виду

        Parameters:
        -----------
        species_name : str
            Наукова назва виду
        bbox : dict, optional
            Bounding box
        limit : int
            Ліміт записів

        Returns:
        --------
        gdf : gpd.GeoDataFrame
        """
        logger.info(f"Collecting GBIF data for {species_name}...")

        try:
            # Отримати taxon key
            species_info = gbif_species.name_backbone(name=species_name)

            if 'usageKey' not in species_info:
                logger.warning(f"Species not found in GBIF: {species_name}")
                return gpd.GeoDataFrame()

            taxon_key = species_info['usageKey']

            # Параметри запиту
            params = {
                'taxonKey': taxon_key,
                'hasCoordinate': True,
                'limit': min(limit, 300)  # GBIF limit per request
            }

            # Додати bbox
            if bbox:
                params['decimalLatitude'] = f"{bbox['min_lat']},{bbox['max_lat']}"
                params['decimalLongitude'] = f"{bbox['min_lon']},{bbox['max_lon']}"

            # Виконати запит
            result = gbif_occ.search(**params)

            if not result or 'results' not in result:
                logger.warning(f"No records found for {species_name}")
                return gpd.GeoDataFrame()

            # Конвертувати в DataFrame
            df = pd.DataFrame(result['results'])

            # Фільтрувати записи з координатами
            df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])

            # Створити GeoDataFrame
            geometry = [
                Point(row['decimalLongitude'], row['decimalLatitude'])
                for _, row in df.iterrows()
            ]

            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            gdf['Species'] = species_name

            logger.info(f"Found {len(gdf)} records for {species_name}")

            return gdf

        except Exception as e:
            logger.error(f"Error collecting GBIF data: {e}")
            return gpd.GeoDataFrame()

    def collect_prey_species(
        self,
        species_list: List[str],
        bbox: Optional[dict] = None,
        use_obis: bool = True,
        use_gbif: bool = True,
        save: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Зібрати дані про види здобичі (морські ссавці)

        Parameters:
        -----------
        species_list : list
            Список наукових назв видів
        bbox : dict, optional
            Bounding box
        use_obis : bool
            Використовувати OBIS
        use_gbif : bool
            Використовувати GBIF
        save : bool
            Зберегти результати

        Returns:
        --------
        combined_gdf : gpd.GeoDataFrame
            Всі спостереження
        """
        logger.info("Collecting prey species data...")

        all_data = []

        for species in species_list:
            logger.info(f"Processing: {species}")

            # Збір з OBIS
            if use_obis:
                obis_data = self.collect_from_obis(species, bbox)
                if not obis_data.empty:
                    obis_data['Source'] = 'OBIS'
                    all_data.append(obis_data)

                time.sleep(1)  # Rate limiting

            # Збір з GBIF
            if use_gbif:
                gbif_data = self.collect_from_gbif(species, bbox)
                if not gbif_data.empty:
                    gbif_data['Source'] = 'GBIF'
                    all_data.append(gbif_data)

                time.sleep(1)  # Rate limiting

        # Об'єднати всі дані
        if all_data:
            combined_gdf = gpd.GeoDataFrame(
                pd.concat(all_data, ignore_index=True),
                crs="EPSG:4326"
            )

            logger.info(f"Total prey species records: {len(combined_gdf)}")

            if save:
                output_file = self.data_dir / "prey_species_occurrences.gpkg"
                combined_gdf.to_file(output_file, driver="GPKG")
                logger.info(f"Saved to: {output_file}")

            return combined_gdf
        else:
            logger.warning("No prey species data collected")
            return gpd.GeoDataFrame()

    def collect_orca_data(
        self,
        bbox: Optional[dict] = None,
        use_obis: bool = True,
        use_gbif: bool = True,
        save: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Зібрати дані про косаток (Orcinus orca)

        Parameters:
        -----------
        bbox : dict, optional
            Bounding box
        use_obis : bool
            Використовувати OBIS
        use_gbif : bool
            Використовувати GBIF
        save : bool
            Зберегти результати

        Returns:
        --------
        orca_gdf : gpd.GeoDataFrame
        """
        logger.info("Collecting Orca (Orcinus orca) data...")

        all_data = []

        # Збір з OBIS
        if use_obis:
            obis_data = self.collect_from_obis("Orcinus orca", bbox, max_records=20000)
            if not obis_data.empty:
                obis_data['Source'] = 'OBIS'
                all_data.append(obis_data)

        # Збір з GBIF
        if use_gbif:
            gbif_data = self.collect_from_gbif("Orcinus orca", bbox, limit=10000)
            if not gbif_data.empty:
                gbif_data['Source'] = 'GBIF'
                all_data.append(gbif_data)

        # Об'єднати
        if all_data:
            orca_gdf = gpd.GeoDataFrame(
                pd.concat(all_data, ignore_index=True),
                crs="EPSG:4326"
            )

            logger.info(f"Total Orca records: {len(orca_gdf)}")

            if save:
                output_file = self.data_dir / "orca_occurrences.gpkg"
                orca_gdf.to_file(output_file, driver="GPKG")
                logger.info(f"Saved to: {output_file}")

            return orca_gdf
        else:
            logger.warning("No Orca data collected")
            return gpd.GeoDataFrame()

    def filter_rookeries(
        self,
        species_data: gpd.GeoDataFrame,
        min_observations: int = 5,
        cluster_distance_km: float = 10
    ) -> gpd.GeoDataFrame:
        """
        Фільтрувати дані для визначення колоній/рокерій

        Parameters:
        -----------
        species_data : gpd.GeoDataFrame
            Спостереження виду
        min_observations : int
            Мінімальна кількість спостережень для колонії
        cluster_distance_km : float
            Відстань для кластеризації (км)

        Returns:
        --------
        rookeries : gpd.GeoDataFrame
            Ймовірні колонії
        """
        from sklearn.cluster import DBSCAN

        logger.info("Identifying rookeries/colonies...")

        # Отримати координати
        coords = species_data.geometry.apply(lambda geom: [geom.x, geom.y]).tolist()
        coords_array = pd.DataFrame(coords, columns=['lon', 'lat']).values

        # Кластеризація
        # eps в градусах: ~10 км / 111 км/градус
        eps = cluster_distance_km / 111.0

        clustering = DBSCAN(eps=eps, min_samples=min_observations).fit(coords_array)

        species_data['Cluster'] = clustering.labels_

        # Фільтрувати кластери (не шум)
        rookeries_df = species_data[species_data['Cluster'] != -1]

        # Розрахувати центроїди кластерів
        centroids = rookeries_df.groupby('Cluster').geometry.apply(
            lambda x: Point(x.x.mean(), x.y.mean())
        ).reset_index()

        rookeries = gpd.GeoDataFrame(
            centroids,
            geometry='geometry',
            crs="EPSG:4326"
        )

        # Додати кількість спостережень
        counts = rookeries_df.groupby('Cluster').size().reset_index(name='Observation_Count')
        rookeries = rookeries.merge(counts, on='Cluster')

        logger.info(f"Identified {len(rookeries)} rookeries/colonies")

        return rookeries


def main():
    """
    Приклад використання
    """
    collector = GBIFOBISCollector()

    # Визначити регіон (Eastern Pacific)
    bbox = {
        'min_lon': -130,
        'max_lon': -110,
        'min_lat': 25,
        'max_lat': 45
    }

    # Список видів здобичі
    prey_species = [
        "Zalophus californianus",  # California Sea Lion
        "Mirounga angustirostris",  # Northern Elephant Seal
        "Arctocephalus pusillus",   # Cape Fur Seal
        "Phoca vitulina"            # Harbor Seal
    ]

    # Зібрати дані про здобич
    prey_data = collector.collect_prey_species(
        prey_species,
        bbox=bbox,
        save=True
    )

    # Зібрати дані про косаток
    orca_data = collector.collect_orca_data(
        bbox=bbox,
        save=True
    )

    # Визначити колонії морських ссавців
    if not prey_data.empty:
        rookeries = collector.filter_rookeries(prey_data, min_observations=10)

        output_file = Path("./data/raw/biodiversity/marine_mammal_rookeries.gpkg")
        rookeries.to_file(output_file, driver="GPKG")
        logger.info(f"Rookeries saved to: {output_file}")


if __name__ == "__main__":
    main()
