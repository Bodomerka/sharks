"""
Data standardization pipeline
Стандартизація всіх даних до єдиної сітки та часового роздільності
"""

import xarray as xr
import numpy as np
import geopandas as gpd
from pathlib import Path
import logging
import sys

sys.path.append(str(Path(__file__).parent.parent))
from utils import (
    create_target_grid, resample_to_grid, calculate_distance_raster,
    calculate_slope, calculate_gradient, raster_to_geotiff,
    aggregate_to_weekly, get_time_coordinate
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataStandardizer:
    """
    Стандартизація даних до:
    - Проєкція: WGS 84 (EPSG:4326)
    - Сітка: 0.1° x 0.1°
    - Часове роздільність: тижнева (для динамічних даних)
    """

    def __init__(self, bbox: dict, resolution: float = 0.1,
                 output_dir: str = "./data/processed"):
        self.bbox = bbox
        self.resolution = resolution
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Створити цільову сітку
        self.lon_grid, self.lat_grid, self.transform = create_target_grid(
            bbox, resolution
        )

        logger.info(f"Target grid created: {self.lon_grid.shape}")

    def process_sst(self, sst_ds: xr.Dataset) -> xr.DataArray:
        """Обробити SST дані"""
        logger.info("Processing SST data...")

        # Отримати змінну SST
        if 'sst' in sst_ds:
            sst = sst_ds['sst']
        elif 'sea_surface_temperature' in sst_ds:
            sst = sst_ds['sea_surface_temperature']
        else:
            raise ValueError("SST variable not found")

        # Ресемплювати до цільової сітки
        sst_resampled = resample_to_grid(sst, (self.lon_grid, self.lat_grid), method='bilinear')

        # Агрегувати до тижневого роздільності
        sst_weekly = aggregate_to_weekly(sst_resampled, method='mean')

        # Розрахувати градієнт (океанічні фронти)
        gradient = calculate_gradient(sst_weekly, self.resolution)

        # Зберегти
        output_file = self.output_dir / "SST_weekly.nc"
        sst_weekly.to_netcdf(output_file)

        gradient_file = self.output_dir / "SST_gradient.nc"
        xr.DataArray(gradient, coords=sst_weekly.coords).to_netcdf(gradient_file)

        logger.info(f"SST data saved to {output_file}")

        return sst_weekly

    def process_chlorophyll(self, chl_ds: xr.Dataset) -> xr.DataArray:
        """Обробити Chlorophyll-a дані"""
        logger.info("Processing Chlorophyll-a data...")

        if 'chlor_a' in chl_ds:
            chl = chl_ds['chlor_a']
        elif 'chlorophyll' in chl_ds:
            chl = chl_ds['chlorophyll']
        else:
            raise ValueError("Chlorophyll variable not found")

        chl_resampled = resample_to_grid(chl, (self.lon_grid, self.lat_grid), method='bilinear')
        chl_weekly = aggregate_to_weekly(chl_resampled, method='mean')

        output_file = self.output_dir / "Chlorophyll_weekly.nc"
        chl_weekly.to_netcdf(output_file)

        logger.info(f"Chlorophyll data saved to {output_file}")

        return chl_weekly

    def process_bathymetry(self, bathy_grid: xr.DataArray) -> tuple:
        """Обробити батиметрію та розрахувати нахил"""
        logger.info("Processing bathymetry data...")

        # Ресемплювати
        bathy_resampled = resample_to_grid(bathy_grid, (self.lon_grid, self.lat_grid), method='bilinear')

        # Конвертувати в глибину (позитивні значення)
        depth = -bathy_resampled.where(bathy_resampled < 0, 0)

        # Розрахувати нахил
        slope = calculate_slope(depth, self.resolution)

        # Зберегти як GeoTIFF
        depth_file = self.output_dir / "Depth.tif"
        raster_to_geotiff(depth.values, self.transform, str(depth_file))

        slope_file = self.output_dir / "Slope.tif"
        raster_to_geotiff(slope, self.transform, str(slope_file))

        logger.info(f"Bathymetry saved to {depth_file}")
        logger.info(f"Slope saved to {slope_file}")

        return depth, slope

    def process_rookeries(self, rookeries_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Створити растр відстаней до колоній"""
        logger.info("Processing marine mammal rookeries...")

        dist_raster = calculate_distance_raster(
            rookeries_gdf,
            (self.lon_grid, self.lat_grid),
            max_distance=500  # км
        )

        output_file = self.output_dir / "Dist_to_Rookery.tif"
        raster_to_geotiff(dist_raster, self.transform, str(output_file))

        logger.info(f"Rookery distance raster saved to {output_file}")

        return dist_raster

    def process_shipping_lanes(self, lanes_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Створити растр відстаней до морських шляхів"""
        logger.info("Processing shipping lanes...")

        # Конвертувати лінії в точки для розрахунку відстаней
        points = []
        for geom in lanes_gdf.geometry:
            if geom.geom_type == 'LineString':
                points.extend([Point(x, y) for x, y in geom.coords])
            elif geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    points.extend([Point(x, y) for x, y in line.coords])

        points_gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")

        dist_raster = calculate_distance_raster(
            points_gdf,
            (self.lon_grid, self.lat_grid),
            max_distance=500
        )

        output_file = self.output_dir / "Dist_to_Shipping_Lane.tif"
        raster_to_geotiff(dist_raster, self.transform, str(output_file))

        logger.info(f"Shipping lanes distance raster saved to {output_file}")

        return dist_raster

    def process_orca_density(self, orca_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Створити растр щільності косаток (kernel density)"""
        logger.info("Processing Orca density...")

        from scipy.stats import gaussian_kde

        # Отримати координати
        coords = np.array([[pt.x, pt.y] for pt in orca_gdf.geometry])

        if len(coords) < 2:
            logger.warning("Not enough Orca observations for KDE")
            return np.zeros(self.lon_grid.shape)

        # Kernel Density Estimation
        kde = gaussian_kde(coords.T)

        # Обчислити на сітці
        grid_coords = np.column_stack([self.lon_grid.ravel(), self.lat_grid.ravel()])
        density = kde(grid_coords.T).reshape(self.lon_grid.shape)

        # Нормалізувати до 0-1
        density = (density - density.min()) / (density.max() - density.min())

        output_file = self.output_dir / "Orca_Density_Index.tif"
        raster_to_geotiff(density, self.transform, str(output_file))

        logger.info(f"Orca density raster saved to {output_file}")

        return density


def main():
    """Приклад використання"""
    bbox = {'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
    standardizer = DataStandardizer(bbox, resolution=0.1)

    logger.info("Data standardization pipeline ready")
    logger.info("Use individual process methods to standardize each data type")


if __name__ == "__main__":
    main()
