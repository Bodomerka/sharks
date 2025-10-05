"""
Spatial utilities for Shark Voyager AI project
Функції для просторової обробки даних
"""

import numpy as np
import xarray as xr
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from typing import Tuple, Union, List
import rioxarray


def create_target_grid(
    bbox: dict,
    resolution: float = 0.1,
    crs: str = "EPSG:4326"
) -> Tuple[np.ndarray, np.ndarray, rasterio.Affine]:
    """
    Створити цільову сітку для стандартизації даних

    Parameters:
    -----------
    bbox : dict
        Bounding box з ключами: min_lon, max_lon, min_lat, max_lat
    resolution : float
        Просторова роздільність у градусах (default: 0.1)
    crs : str
        Система координат (default: EPSG:4326)

    Returns:
    --------
    lon_grid : np.ndarray
        Масив довгот
    lat_grid : np.ndarray
        Масив широт
    transform : rasterio.Affine
        Афінне перетворення для растру
    """
    # Створити масиви координат
    lons = np.arange(bbox['min_lon'], bbox['max_lon'] + resolution, resolution)
    lats = np.arange(bbox['min_lat'], bbox['max_lat'] + resolution, resolution)

    # Створити meshgrid
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    # Створити афінне перетворення
    transform = from_bounds(
        bbox['min_lon'],
        bbox['min_lat'],
        bbox['max_lon'],
        bbox['max_lat'],
        len(lons),
        len(lats)
    )

    return lon_grid, lat_grid, transform


def resample_to_grid(
    data: Union[xr.DataArray, xr.Dataset],
    target_grid: Tuple[np.ndarray, np.ndarray],
    method: str = 'bilinear'
) -> xr.DataArray:
    """
    Ресемплювати дані до цільової сітки

    Parameters:
    -----------
    data : xr.DataArray or xr.Dataset
        Вхідні дані
    target_grid : tuple
        Кортеж (lon_grid, lat_grid) цільової сітки
    method : str
        Метод інтерполяції: 'bilinear', 'nearest', 'cubic'

    Returns:
    --------
    resampled : xr.DataArray
        Ресемпльовані дані
    """
    lon_grid, lat_grid = target_grid

    # Переконатися, що дані мають правильні координати
    if 'lon' not in data.coords and 'longitude' in data.coords:
        data = data.rename({'longitude': 'lon'})
    if 'lat' not in data.coords and 'latitude' in data.coords:
        data = data.rename({'latitude': 'lat'})

    # Інтерполяція
    resampled = data.interp(
        lon=lon_grid[0, :],
        lat=lat_grid[:, 0],
        method=method
    )

    return resampled


def calculate_distance_raster(
    points: gpd.GeoDataFrame,
    target_grid: Tuple[np.ndarray, np.ndarray],
    max_distance: float = None
) -> np.ndarray:
    """
    Розрахувати растр відстаней до найближчої точки

    Parameters:
    -----------
    points : gpd.GeoDataFrame
        GeoDataFrame з точками
    target_grid : tuple
        Кортеж (lon_grid, lat_grid)
    max_distance : float, optional
        Максимальна відстань (км). Значення більше будуть обмежені.

    Returns:
    --------
    distance_raster : np.ndarray
        Растр відстаней у кілометрах
    """
    lon_grid, lat_grid = target_grid

    # Отримати координати точок
    point_coords = np.array([(pt.x, pt.y) for pt in points.geometry])

    # Створити дерево KDTree для швидкого пошуку
    tree = cKDTree(point_coords)

    # Координати сітки
    grid_coords = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])

    # Знайти найближчі відстані
    distances, _ = tree.query(grid_coords)

    # Перетворити з градусів у кілометри (приблизно)
    # 1 градус ≈ 111 км на екваторі
    distances_km = distances * 111.0

    # Застосувати максимальну відстань, якщо вказано
    if max_distance is not None:
        distances_km = np.minimum(distances_km, max_distance)

    # Перетворити назад у форму сітки
    distance_raster = distances_km.reshape(lon_grid.shape)

    return distance_raster


def calculate_slope(
    elevation: Union[xr.DataArray, np.ndarray],
    resolution: float = 0.1
) -> np.ndarray:
    """
    Розрахувати нахил (slope) з растру висот/глибин

    Parameters:
    -----------
    elevation : xr.DataArray or np.ndarray
        Растр висот (негативні значення для глибин)
    resolution : float
        Просторова роздільність у градусах

    Returns:
    --------
    slope : np.ndarray
        Нахил у градусах
    """
    # Конвертувати в numpy array, якщо потрібно
    if isinstance(elevation, xr.DataArray):
        elev = elevation.values
    else:
        elev = elevation

    # Розрахунок градієнтів
    # 1 градус ≈ 111 км
    pixel_size = resolution * 111000  # метри

    dy, dx = np.gradient(elev, pixel_size)

    # Розрахунок slope
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

    return slope


def calculate_gradient(
    data: Union[xr.DataArray, np.ndarray],
    resolution: float = 0.1
) -> np.ndarray:
    """
    Розрахувати градієнт (напр., для SST фронтів)

    Parameters:
    -----------
    data : xr.DataArray or np.ndarray
        Вхідні дані (напр., температура)
    resolution : float
        Просторова роздільність у градусах

    Returns:
    --------
    gradient_magnitude : np.ndarray
        Магнітуда градієнту
    """
    # Конвертувати в numpy array, якщо потрібно
    if isinstance(data, xr.DataArray):
        arr = data.values
    else:
        arr = data

    # Розрахунок градієнтів
    pixel_size = resolution * 111  # км

    dy, dx = np.gradient(arr, pixel_size)

    # Магнітуда градієнту
    gradient_magnitude = np.sqrt(dx**2 + dy**2)

    return gradient_magnitude


def points_to_geodataframe(
    lons: np.ndarray,
    lats: np.ndarray,
    data: dict = None,
    crs: str = "EPSG:4326"
) -> gpd.GeoDataFrame:
    """
    Перетворити масиви координат у GeoDataFrame

    Parameters:
    -----------
    lons : np.ndarray
        Довготи
    lats : np.ndarray
        Широти
    data : dict, optional
        Додаткові атрибути
    crs : str
        Система координат

    Returns:
    --------
    gdf : gpd.GeoDataFrame
    """
    geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]

    if data is None:
        data = {}

    gdf = gpd.GeoDataFrame(data, geometry=geometry, crs=crs)

    return gdf


def raster_to_geotiff(
    data: np.ndarray,
    transform: rasterio.Affine,
    output_path: str,
    crs: str = "EPSG:4326",
    nodata: float = -9999,
    compress: str = "LZW"
):
    """
    Зберегти растр у форматі GeoTIFF

    Parameters:
    -----------
    data : np.ndarray
        Растрові дані (2D або 3D масив)
    transform : rasterio.Affine
        Афінне перетворення
    output_path : str
        Шлях до вихідного файлу
    crs : str
        Система координат
    nodata : float
        Значення NoData
    compress : str
        Метод стиснення
    """
    # Визначити кількість каналів
    if data.ndim == 2:
        count = 1
        height, width = data.shape
        data = data.reshape(1, height, width)
    else:
        count, height, width = data.shape

    # Записати GeoTIFF
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=count,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress=compress
    ) as dst:
        dst.write(data)


def buffer_points(
    points: gpd.GeoDataFrame,
    distance_km: float
) -> gpd.GeoDataFrame:
    """
    Створити буфер навколо точок

    Parameters:
    -----------
    points : gpd.GeoDataFrame
        Точки
    distance_km : float
        Відстань буферу в кілометрах

    Returns:
    --------
    buffered : gpd.GeoDataFrame
        GeoDataFrame з буферами
    """
    # Перепроєктувати в метричну систему для точних буферів
    # Використаємо UTM або аналог
    # Для спрощення: 1 градус ≈ 111 км
    distance_degrees = distance_km / 111.0

    buffered = points.copy()
    buffered['geometry'] = points.geometry.buffer(distance_degrees)

    return buffered


def clip_to_bbox(
    data: Union[xr.DataArray, xr.Dataset, gpd.GeoDataFrame],
    bbox: dict
) -> Union[xr.DataArray, xr.Dataset, gpd.GeoDataFrame]:
    """
    Обрізати дані до bounding box

    Parameters:
    -----------
    data : xr.DataArray, xr.Dataset, or gpd.GeoDataFrame
        Вхідні дані
    bbox : dict
        Bounding box з ключами: min_lon, max_lon, min_lat, max_lat

    Returns:
    --------
    clipped : same type as input
        Обрізані дані
    """
    if isinstance(data, (xr.DataArray, xr.Dataset)):
        # Обрізати xarray об'єкт
        clipped = data.sel(
            lon=slice(bbox['min_lon'], bbox['max_lon']),
            lat=slice(bbox['min_lat'], bbox['max_lat'])
        )
    elif isinstance(data, gpd.GeoDataFrame):
        # Обрізати GeoDataFrame
        clipped = data.cx[
            bbox['min_lon']:bbox['max_lon'],
            bbox['min_lat']:bbox['max_lat']
        ]
    else:
        raise TypeError("Unsupported data type")

    return clipped
