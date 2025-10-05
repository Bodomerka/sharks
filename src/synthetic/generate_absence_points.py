"""
Generate absence/background points for model training
Генерація точок відсутності для тренування моделей
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils import buffer_points, add_temporal_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AbsencePointsGenerator:
    """
    Генератор точок відсутності (absence/background points)

    Створює випадкові точки в межах ареалу виду, але за межами
    100 км буферу навколо реальних точок присутності.
    """

    def __init__(self, buffer_distance_km: float = 100, random_seed: int = 42):
        """
        Parameters:
        -----------
        buffer_distance_km : float
            Відстань буферу від точок присутності (км)
        random_seed : int
            Seed для генератора випадкових чисел
        """
        self.buffer_distance = buffer_distance_km
        self.random_seed = random_seed
        np.random.seed(random_seed)

        logger.info(f"Absence points generator initialized with {buffer_distance_km}km buffer")

    def generate_absence_points(
        self,
        presence_points: gpd.GeoDataFrame,
        bbox: dict,
        ratio: float = 1.0,
        life_stage: str = None
    ) -> gpd.GeoDataFrame:
        """
        Згенерувати точки відсутності

        Parameters:
        -----------
        presence_points : gpd.GeoDataFrame
            Точки присутності акул
        bbox : dict
            Bounding box для генерації точок
        ratio : float
            Співвідношення absence:presence (default: 1.0 = рівна кількість)
        life_stage : str, optional
            Фільтрувати точки присутності за стадією життя

        Returns:
        --------
        absence_points : gpd.GeoDataFrame
            Згенеровані точки відсутності
        """
        logger.info(f"Generating absence points with ratio {ratio}...")

        # Фільтрувати за стадією життя, якщо вказано
        if life_stage:
            presence_filtered = presence_points[
                presence_points['Life_Stage'] == life_stage
            ]
            logger.info(f"Filtered {len(presence_filtered)} points for {life_stage}")
        else:
            presence_filtered = presence_points

        n_presence = len(presence_filtered)
        n_absence = int(n_presence * ratio)

        logger.info(f"Generating {n_absence} absence points...")

        # Створити буфер навколо точок присутності
        buffered = buffer_points(presence_filtered, self.buffer_distance)

        # Об'єднати всі буфери в одну геометрію
        exclusion_zone = buffered.unary_union

        # Створити прямокутник bbox
        study_area = Polygon([
            (bbox['min_lon'], bbox['min_lat']),
            (bbox['max_lon'], bbox['min_lat']),
            (bbox['max_lon'], bbox['max_lat']),
            (bbox['min_lon'], bbox['max_lat']),
            (bbox['min_lon'], bbox['min_lat'])
        ])

        # Зона для генерації = study_area - exclusion_zone
        available_area = study_area.difference(exclusion_zone)

        # Генерувати випадкові точки
        absence_points_list = []
        attempts = 0
        max_attempts = n_absence * 10  # Безпека від нескінченного циклу

        while len(absence_points_list) < n_absence and attempts < max_attempts:
            # Випадкові координати
            lon = np.random.uniform(bbox['min_lon'], bbox['max_lon'])
            lat = np.random.uniform(bbox['min_lat'], bbox['max_lat'])

            point = Point(lon, lat)

            # Перевірити, чи точка в доступній зоні
            if available_area.contains(point):
                absence_points_list.append(point)

            attempts += 1

        if len(absence_points_list) < n_absence:
            logger.warning(
                f"Could only generate {len(absence_points_list)} absence points "
                f"(target: {n_absence})"
            )

        # Створити GeoDataFrame
        absence_gdf = gpd.GeoDataFrame(
            {
                'Shark_Presence_Status': [0] * len(absence_points_list),
                'Life_Stage': [life_stage if life_stage else 'All'] * len(absence_points_list),
                'Point_Type': ['Absence'] * len(absence_points_list)
            },
            geometry=absence_points_list,
            crs="EPSG:4326"
        )

        logger.info(f"Generated {len(absence_gdf)} absence points")

        return absence_gdf

    def generate_for_all_life_stages(
        self,
        presence_points: gpd.GeoDataFrame,
        bbox: dict,
        life_stages: list = ['Adult_Male', 'Adult_Female', 'Juvenile'],
        ratio: float = 1.0,
        save: bool = True,
        output_dir: str = "./data/processed"
    ) -> dict:
        """
        Згенерувати точки відсутності для всіх стадій життя

        Parameters:
        -----------
        presence_points : gpd.GeoDataFrame
            Всі точки присутності
        bbox : dict
            Bounding box
        life_stages : list
            Список стадій життя
        ratio : float
            Співвідношення absence:presence
        save : bool
            Зберегти результати
        output_dir : str
            Директорія для збереження

        Returns:
        --------
        absence_datasets : dict
            Словник з точками відсутності для кожної стадії
        """
        logger.info("Generating absence points for all life stages...")

        absence_datasets = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for stage in life_stages:
            logger.info(f"Processing {stage}...")

            absence_points = self.generate_absence_points(
                presence_points,
                bbox,
                ratio=ratio,
                life_stage=stage
            )

            absence_datasets[stage] = absence_points

            if save:
                filename = output_path / f"absence_points_{stage}.gpkg"
                absence_points.to_file(filename, driver="GPKG")
                logger.info(f"Saved to {filename}")

        return absence_datasets

    def combine_presence_absence(
        self,
        presence_points: gpd.GeoDataFrame,
        absence_points: gpd.GeoDataFrame,
        add_temporal: bool = True,
        date_column: str = 'Date'
    ) -> gpd.GeoDataFrame:
        """
        Об'єднати точки присутності та відсутності

        Parameters:
        -----------
        presence_points : gpd.GeoDataFrame
            Точки присутності
        absence_points : gpd.GeoDataFrame
            Точки відсутності
        add_temporal : bool
            Додати часові ознаки (Month, Week_of_Year)
        date_column : str
            Назва колонки з датами

        Returns:
        --------
        combined : gpd.GeoDataFrame
            Об'єднаний датасет
        """
        logger.info("Combining presence and absence points...")

        # Переконатися, що обидва мають колонку Shark_Presence_Status
        presence_points = presence_points.copy()
        absence_points = absence_points.copy()

        presence_points['Shark_Presence_Status'] = 1
        absence_points['Shark_Presence_Status'] = 0

        # Об'єднати
        combined = gpd.GeoDataFrame(
            pd.concat([presence_points, absence_points], ignore_index=True),
            crs="EPSG:4326"
        )

        # Додати часові ознаки
        if add_temporal and date_column in combined.columns:
            combined = add_temporal_features(combined, date_column)

        logger.info(f"Combined dataset: {len(combined)} points")
        logger.info(f"  Presence: {len(presence_points)}")
        logger.info(f"  Absence: {len(absence_points)}")

        return combined


def main():
    """Приклад використання"""
    # Потребує завантажені дані OCEARCH
    # Приклад показує, як використовувати генератор

    generator = AbsencePointsGenerator(buffer_distance_km=100, random_seed=42)

    bbox = {
        'min_lon': -130,
        'max_lon': -110,
        'min_lat': 25,
        'max_lat': 45
    }

    # Приклад: завантажити точки присутності
    # presence_points = gpd.read_file("./data/raw/ocearch/white_shark_tracks.gpkg")

    # Згенерувати точки відсутності для всіх стадій
    # absence_datasets = generator.generate_for_all_life_stages(
    #     presence_points, bbox, save=True
    # )

    logger.info("Absence points generator ready")


if __name__ == "__main__":
    import pandas as pd
    main()
