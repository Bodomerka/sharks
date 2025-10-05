"""
OCEARCH Shark Tracker data collector
Збір даних про треки білих акул з OCEARCH

IMPORTANT: OCEARCH requires permission for research use
Contact: tracker@ocearch.org for data sharing agreement
"""

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from typing import Optional, List
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCEARCHCollector:
    """
    Collector for OCEARCH shark tracking data

    Note: Використовує неофіційне API. Для дослідницьких цілей
    потрібен дозвіл від OCEARCH.
    """

    def __init__(self, data_dir: str = "./data/raw/ocearch"):
        """
        Parameters:
        -----------
        data_dir : str
            Директорія для збереження даних
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Базовий URL (неофіційний)
        self.base_url = "https://www.ocearch.org/tracker/api"

    def get_shark_list(self) -> pd.DataFrame:
        """
        Отримати список всіх акул у системі OCEARCH

        Returns:
        --------
        sharks_df : pd.DataFrame
            DataFrame зі списком акул
        """
        logger.info("Fetching shark list from OCEARCH...")

        try:
            # Endpoint для списку акул (може змінюватися)
            url = f"{self.base_url}/v1/sharks"

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Конвертувати в DataFrame
            sharks_df = pd.DataFrame(data)

            logger.info(f"Found {len(sharks_df)} sharks in database")

            return sharks_df

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching shark list: {e}")
            logger.warning("Note: OCEARCH API requires permission for research use")
            logger.warning("Contact tracker@ocearch.org for data sharing agreement")
            return pd.DataFrame()

    def get_shark_tracks(
        self,
        shark_id: str,
        species_filter: str = "Carcharodon carcharias"
    ) -> gpd.GeoDataFrame:
        """
        Отримати треки конкретної акули

        Parameters:
        -----------
        shark_id : str
            ID акули
        species_filter : str
            Фільтр за видом (default: Carcharodon carcharias)

        Returns:
        --------
        tracks_gdf : gpd.GeoDataFrame
            GeoDataFrame з треками
        """
        logger.info(f"Fetching tracks for shark ID: {shark_id}")

        try:
            url = f"{self.base_url}/v1/tracks/{shark_id}"

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Конвертувати в DataFrame
            tracks_df = pd.DataFrame(data)

            # Створити геометрію
            geometry = [Point(row['longitude'], row['latitude'])
                       for _, row in tracks_df.iterrows()]

            tracks_gdf = gpd.GeoDataFrame(
                tracks_df,
                geometry=geometry,
                crs="EPSG:4326"
            )

            logger.info(f"Retrieved {len(tracks_gdf)} track points")

            return tracks_gdf

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tracks: {e}")
            return gpd.GeoDataFrame()

    def collect_all_white_shark_tracks(
        self,
        save: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Зібрати всі доступні треки білих акул

        Parameters:
        -----------
        save : bool
            Зберегти результати у файл

        Returns:
        --------
        all_tracks : gpd.GeoDataFrame
            Всі треки білих акул
        """
        logger.info("Collecting all white shark tracks from OCEARCH...")

        # Отримати список акул
        sharks_df = self.get_shark_list()

        if sharks_df.empty:
            logger.error("No sharks found. Check API access.")
            return gpd.GeoDataFrame()

        # Фільтрувати білих акул
        white_sharks = sharks_df[
            sharks_df['species'] == 'Carcharodon carcharias'
        ]

        logger.info(f"Found {len(white_sharks)} white sharks")

        # Зібрати треки для кожної акули
        all_tracks = []

        for idx, shark in white_sharks.iterrows():
            shark_id = shark.get('id') or shark.get('shark_id')

            if shark_id:
                tracks = self.get_shark_tracks(shark_id)

                if not tracks.empty:
                    # Додати метадані
                    tracks['Shark_ID'] = shark_id
                    tracks['Shark_Name'] = shark.get('name', '')
                    tracks['Sex'] = shark.get('sex', '')
                    tracks['Length_m'] = shark.get('length', None)
                    tracks['Weight_kg'] = shark.get('weight', None)

                    all_tracks.append(tracks)

        # Об'єднати всі треки
        if all_tracks:
            combined_tracks = gpd.GeoDataFrame(
                pd.concat(all_tracks, ignore_index=True),
                crs="EPSG:4326"
            )

            # Додати статус присутності
            combined_tracks['Shark_Presence_Status'] = 1

            # Визначити стадію життя (спрощено)
            combined_tracks['Life_Stage'] = combined_tracks.apply(
                self._classify_life_stage,
                axis=1
            )

            logger.info(f"Total tracks collected: {len(combined_tracks)}")

            if save:
                output_file = self.data_dir / "white_shark_tracks.gpkg"
                combined_tracks.to_file(output_file, driver="GPKG")
                logger.info(f"Saved to: {output_file}")

            return combined_tracks

        else:
            logger.warning("No tracks collected")
            return gpd.GeoDataFrame()

    def _classify_life_stage(self, row) -> str:
        """
        Класифікувати стадію життя на основі розміру

        Parameters:
        -----------
        row : pd.Series
            Рядок DataFrame

        Returns:
        --------
        life_stage : str
            'Adult_Male', 'Adult_Female', або 'Juvenile'
        """
        length = row.get('Length_m', None)
        sex = row.get('Sex', '').lower()

        if length is None:
            return 'Unknown'

        # Білі акули стають дорослими при ~3.5-4 м
        if length >= 3.5:
            if sex == 'male' or sex == 'm':
                return 'Adult_Male'
            elif sex == 'female' or sex == 'f':
                return 'Adult_Female'
            else:
                return 'Adult'
        else:
            return 'Juvenile'

    def separate_by_life_stage(
        self,
        tracks: gpd.GeoDataFrame
    ) -> dict:
        """
        Розділити треки за стадією життя

        Parameters:
        -----------
        tracks : gpd.GeoDataFrame
            Всі треки

        Returns:
        --------
        separated : dict
            Словник з ключами: 'Adult_Male', 'Adult_Female', 'Juvenile'
        """
        separated = {
            'Adult_Male': tracks[tracks['Life_Stage'] == 'Adult_Male'],
            'Adult_Female': tracks[tracks['Life_Stage'] == 'Adult_Female'],
            'Juvenile': tracks[tracks['Life_Stage'] == 'Juvenile']
        }

        for stage, data in separated.items():
            logger.info(f"{stage}: {len(data)} points")

        return separated

    def load_from_csv(self, csv_path: str) -> gpd.GeoDataFrame:
        """
        Завантажити дані з CSV файлу (якщо вони вже отримані від OCEARCH)

        Parameters:
        -----------
        csv_path : str
            Шлях до CSV файлу

        Returns:
        --------
        tracks_gdf : gpd.GeoDataFrame
        """
        logger.info(f"Loading tracks from {csv_path}")

        df = pd.read_csv(csv_path)

        # Очікувані колонки: Date, Latitude, Longitude, Name, Sex, Length, etc.

        # Створити геометрію
        geometry = [Point(row['Longitude'], row['Latitude'])
                   for _, row in df.iterrows()]

        tracks_gdf = gpd.GeoDataFrame(
            df,
            geometry=geometry,
            crs="EPSG:4326"
        )

        # Додати статус присутності
        tracks_gdf['Shark_Presence_Status'] = 1

        logger.info(f"Loaded {len(tracks_gdf)} tracks")

        return tracks_gdf


def main():
    """
    Приклад використання
    """
    collector = OCEARCHCollector()

    # ВАЖЛИВО: Для використання API потрібен дозвіл від OCEARCH
    logger.warning("=" * 60)
    logger.warning("OCEARCH DATA ACCESS NOTICE")
    logger.warning("=" * 60)
    logger.warning("This script uses unofficial OCEARCH API endpoints.")
    logger.warning("For research use, you MUST obtain permission from OCEARCH.")
    logger.warning("Contact: tracker@ocearch.org")
    logger.warning("=" * 60)

    # Якщо у вас є дозвіл, розкоментуйте:
    # tracks = collector.collect_all_white_shark_tracks(save=True)

    # separated = collector.separate_by_life_stage(tracks)

    # Альтернатива: завантажити з власного CSV
    # tracks = collector.load_from_csv("path/to/ocearch_data.csv")


if __name__ == "__main__":
    main()
