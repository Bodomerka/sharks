"""
Configuration loader utility
Утиліта для завантаження конфігурації
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Завантажити конфігурацію з YAML файлу

    Parameters:
    -----------
    config_path : str, optional
        Шлях до конфігураційного файлу
        Якщо не вказано, шукає в ./config/config.yaml

    Returns:
    --------
    config : dict
        Словник з конфігурацією
    """
    if config_path is None:
        # Знайти корневу директорію проєкту
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        config_path = project_root / "config" / "config.yaml"

    # Завантажити YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def get_credentials(config: Dict[str, Any], service: str) -> Dict[str, Any]:
    """
    Отримати облікові дані для конкретного сервісу

    Parameters:
    -----------
    config : dict
        Конфігураційний словник
    service : str
        Назва сервісу: 'nasa_earthdata', 'copernicus_marine', 'global_fishing_watch', etc.

    Returns:
    --------
    credentials : dict
        Словник з обліковими даними
    """
    if 'credentials' not in config:
        raise ValueError("No credentials section in config")

    if service not in config['credentials']:
        raise ValueError(f"No credentials for service: {service}")

    return config['credentials'][service]


def get_bbox(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Отримати bounding box з конфігурації

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    bbox : dict
        Словник з min_lon, max_lon, min_lat, max_lat
    """
    if 'spatial' not in config or 'bbox' not in config['spatial']:
        raise ValueError("No bbox in config")

    return config['spatial']['bbox']


def get_date_range(config: Dict[str, Any]) -> tuple:
    """
    Отримати діапазон дат з конфігурації

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    start_date, end_date : tuple
        Початкова та кінцева дати
    """
    if 'temporal' not in config:
        raise ValueError("No temporal section in config")

    start_date = config['temporal']['start_date']
    end_date = config['temporal']['end_date']

    return start_date, end_date


def get_target_species(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Отримати інформацію про цільовий вид

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    species : dict
        Інформація про цільовий вид
    """
    if 'species' not in config or 'target' not in config['species']:
        raise ValueError("No target species in config")

    return config['species']['target']


def get_prey_species(config: Dict[str, Any]) -> list:
    """
    Отримати список видів здобичі

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    prey_species : list
        Список словників з інформацією про види здобичі
    """
    if 'prey_species' not in config:
        raise ValueError("No prey species in config")

    return config['prey_species']


def get_data_product_config(config: Dict[str, Any], product: str) -> Dict[str, Any]:
    """
    Отримати конфігурацію для конкретного продукту даних

    Parameters:
    -----------
    config : dict
        Конфігураційний словник
    product : str
        Назва продукту: 'modis_sst', 'modis_chlorophyll', 'smap_salinity', etc.

    Returns:
    --------
    product_config : dict
        Конфігурація продукту
    """
    if 'data_products' not in config:
        raise ValueError("No data_products in config")

    if product not in config['data_products']:
        raise ValueError(f"No configuration for product: {product}")

    return config['data_products'][product]


def create_output_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Створити вихідні директорії з конфігурації

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    paths : dict
        Словник з Path об'єктами
    """
    if 'paths' not in config:
        raise ValueError("No paths in config")

    paths = {}
    for key, value in config['paths'].items():
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        paths[key] = path

    return paths


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Валідувати конфігурацію

    Parameters:
    -----------
    config : dict
        Конфігураційний словник

    Returns:
    --------
    valid : bool
        True якщо конфігурація валідна

    Raises:
    -------
    ValueError: якщо конфігурація невалідна
    """
    required_sections = ['spatial', 'temporal', 'credentials', 'species', 'data_products', 'paths']

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")

    # Перевірка spatial
    if 'bbox' not in config['spatial']:
        raise ValueError("Missing bbox in spatial section")

    bbox = config['spatial']['bbox']
    required_bbox_keys = ['min_lon', 'max_lon', 'min_lat', 'max_lat']
    for key in required_bbox_keys:
        if key not in bbox:
            raise ValueError(f"Missing {key} in bbox")

    # Перевірка temporal
    if 'start_date' not in config['temporal'] or 'end_date' not in config['temporal']:
        raise ValueError("Missing start_date or end_date in temporal section")

    return True


def setup_nasa_credentials(username: str, password: str):
    """
    Налаштувати NASA Earthdata credentials у .netrc файлі

    Parameters:
    -----------
    username : str
        NASA Earthdata username
    password : str
        NASA Earthdata password
    """
    netrc_path = Path.home() / '.netrc'

    # Перевірити, чи існує файл
    if netrc_path.exists():
        with open(netrc_path, 'r') as f:
            content = f.read()

        # Перевірити, чи вже є запис
        if 'urs.earthdata.nasa.gov' in content:
            print("NASA Earthdata credentials already exist in .netrc")
            return

    # Додати запис
    with open(netrc_path, 'a') as f:
        f.write(f"\nmachine urs.earthdata.nasa.gov\n")
        f.write(f"login {username}\n")
        f.write(f"password {password}\n")

    # Встановити права доступу (тільки для власника)
    os.chmod(netrc_path, 0o600)

    print("NASA Earthdata credentials added to .netrc")
