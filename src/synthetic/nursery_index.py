"""
Nursery Suitability Index calculator
Розрахунок індексу придатності розплідника
"""

import numpy as np
import xarray as xr
from pathlib import Path
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils import raster_to_geotiff, is_summer_month

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NurserySuitabilityCalculator:
    """
    Розрахунок Nursery Suitability Index

    Критерії:
    - Depth < 100 m
    - Slope < 5°
    - SST > 16°C (літні місяці)
    - Chlorophyll > середнє
    """

    def __init__(
        self,
        max_depth: float = 100,
        max_slope: float = 5,
        min_sst_summer: float = 16,
        summer_months: list = [6, 7, 8]
    ):
        """
        Parameters:
        -----------
        max_depth : float
            Максимальна глибина (м)
        max_slope : float
            Максимальний нахил (градуси)
        min_sst_summer : float
            Мінімальна SST для літніх місяців (°C)
        summer_months : list
            Літні місяці (default: червень, липень, серпень)
        """
        self.max_depth = max_depth
        self.max_slope = max_slope
        self.min_sst_summer = min_sst_summer
        self.summer_months = summer_months

        logger.info("Nursery Suitability Calculator initialized")
        logger.info(f"  Max depth: {max_depth}m")
        logger.info(f"  Max slope: {max_slope}°")
        logger.info(f"  Min SST (summer): {min_sst_summer}°C")
        logger.info(f"  Summer months: {summer_months}")

    def calculate_index(
        self,
        depth: np.ndarray,
        slope: np.ndarray,
        sst_summer: np.ndarray,
        chlorophyll: np.ndarray,
        transform: 'rasterio.Affine' = None,
        save: bool = True,
        output_dir: str = "./data/processed"
    ) -> np.ndarray:
        """
        Розрахувати Nursery Suitability Index

        Parameters:
        -----------
        depth : np.ndarray
            Растр глибини (метри)
        slope : np.ndarray
            Растр нахилу (градуси)
        sst_summer : np.ndarray
            Середня SST для літніх місяців (°C)
        chlorophyll : np.ndarray
            Середня концентрація хлорофілу (mg/m³)
        transform : rasterio.Affine, optional
            Афінне перетворення для збереження GeoTIFF
        save : bool
            Зберегти результат
        output_dir : str
            Директорія для збереження

        Returns:
        --------
        nursery_index : np.ndarray
            Індекс придатності розплідника (0-1)
        """
        logger.info("Calculating Nursery Suitability Index...")

        # Ініціалізувати індекс нулями
        nursery_index = np.zeros_like(depth, dtype=np.float32)

        # 1. Критерій глибини
        depth_suitable = (depth > 0) & (depth < self.max_depth)
        logger.info(f"  Depth criterion: {depth_suitable.sum()} suitable cells")

        # 2. Критерій нахилу
        slope_suitable = slope < self.max_slope
        logger.info(f"  Slope criterion: {slope_suitable.sum()} suitable cells")

        # 3. Критерій SST (літні місяці)
        sst_suitable = sst_summer > self.min_sst_summer
        logger.info(f"  SST criterion: {sst_suitable.sum()} suitable cells")

        # 4. Критерій хлорофілу (вище середнього)
        chl_mean = np.nanmean(chlorophyll)
        chl_suitable = chlorophyll > chl_mean
        logger.info(f"  Chlorophyll criterion (>{chl_mean:.3f}): {chl_suitable.sum()} suitable cells")

        # Комбінувати критерії
        # Кожен критерій додає 0.25 до індексу
        nursery_index[depth_suitable] += 0.25
        nursery_index[slope_suitable] += 0.25
        nursery_index[sst_suitable] += 0.25
        nursery_index[chl_suitable] += 0.25

        # Індекс від 0 до 1
        logger.info(f"Index range: {nursery_index.min():.2f} - {nursery_index.max():.2f}")

        # Статистика
        high_suitability = (nursery_index >= 0.75).sum()
        logger.info(f"  High suitability (>= 0.75): {high_suitability} cells")

        # Зберегти
        if save and transform is not None:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            output_file = output_path / "Nursery_Suitability_Index.tif"
            raster_to_geotiff(nursery_index, transform, str(output_file))

            logger.info(f"Nursery index saved to {output_file}")

        return nursery_index

    def calculate_from_files(
        self,
        depth_file: str,
        slope_file: str,
        sst_files: list,
        chlorophyll_files: list,
        save: bool = True,
        output_dir: str = "./data/processed"
    ) -> np.ndarray:
        """
        Розрахувати індекс з файлів

        Parameters:
        -----------
        depth_file : str
            Шлях до файлу глибини
        slope_file : str
            Шлях до файлу нахилу
        sst_files : list
            Список файлів SST (для літніх місяців)
        chlorophyll_files : list
            Список файлів хлорофілу
        save : bool
            Зберегти результат
        output_dir : str
            Директорія для збереження

        Returns:
        --------
        nursery_index : np.ndarray
        """
        import rasterio

        logger.info("Loading data from files...")

        # Завантажити глибину
        with rasterio.open(depth_file) as src:
            depth = src.read(1)
            transform = src.transform

        # Завантажити нахил
        with rasterio.open(slope_file) as src:
            slope = src.read(1)

        # Завантажити та усереднити SST для літніх місяців
        sst_summer_data = []
        for sst_file in sst_files:
            ds = xr.open_dataset(sst_file)
            # Фільтрувати літні місяці
            time_coord = list(ds.coords.keys())[0]
            if 'time' in ds.coords or 'Time' in ds.coords:
                time_var = 'time' if 'time' in ds.coords else 'Time'
                summer_mask = ds[time_var].dt.month.isin(self.summer_months)
                sst_summer = ds.where(summer_mask, drop=True)
                sst_summer_data.append(sst_summer.mean(dim=time_var).values)

        sst_summer = np.nanmean(sst_summer_data, axis=0) if sst_summer_data else np.zeros_like(depth)

        # Завантажити та усереднити хлорофіл
        chl_data = []
        for chl_file in chlorophyll_files:
            ds = xr.open_dataset(chl_file)
            chl_data.append(ds['chlor_a'].mean(dim='time').values if 'time' in ds.coords else ds['chlor_a'].values)

        chlorophyll = np.nanmean(chl_data, axis=0) if chl_data else np.zeros_like(depth)

        # Розрахувати індекс
        nursery_index = self.calculate_index(
            depth, slope, sst_summer, chlorophyll,
            transform=transform, save=save, output_dir=output_dir
        )

        return nursery_index


def main():
    """Приклад використання"""
    calculator = NurserySuitabilityCalculator(
        max_depth=100,
        max_slope=5,
        min_sst_summer=16,
        summer_months=[6, 7, 8]
    )

    # Приклад з синтетичними даними
    shape = (200, 200)
    depth = np.random.uniform(0, 200, shape)
    slope = np.random.uniform(0, 10, shape)
    sst_summer = np.random.uniform(14, 22, shape)
    chlorophyll = np.random.exponential(1.5, shape)

    # Розрахувати індекс
    nursery_index = calculator.calculate_index(
        depth, slope, sst_summer, chlorophyll, save=False
    )

    logger.info(f"Example nursery index calculated: shape={nursery_index.shape}")


if __name__ == "__main__":
    main()
