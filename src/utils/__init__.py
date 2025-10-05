"""
Utilities package for Shark Voyager AI
"""

from .spatial_utils import (
    create_target_grid,
    resample_to_grid,
    calculate_distance_raster,
    calculate_slope,
    calculate_gradient,
    points_to_geodataframe,
    raster_to_geotiff,
    buffer_points,
    clip_to_bbox
)

from .temporal_utils import (
    aggregate_to_weekly,
    get_time_coordinate,
    add_temporal_features,
    filter_date_range,
    get_season,
    add_season_column,
    create_weekly_dates,
    interpolate_to_weekly,
    get_climatology,
    align_time_series,
    is_summer_month
)

from .config_loader import (
    load_config,
    get_credentials,
    get_bbox,
    get_date_range,
    get_target_species,
    get_prey_species,
    get_data_product_config,
    create_output_paths,
    validate_config,
    setup_nasa_credentials
)

__all__ = [
    # Spatial utilities
    'create_target_grid',
    'resample_to_grid',
    'calculate_distance_raster',
    'calculate_slope',
    'calculate_gradient',
    'points_to_geodataframe',
    'raster_to_geotiff',
    'buffer_points',
    'clip_to_bbox',
    # Temporal utilities
    'aggregate_to_weekly',
    'get_time_coordinate',
    'add_temporal_features',
    'filter_date_range',
    'get_season',
    'add_season_column',
    'create_weekly_dates',
    'interpolate_to_weekly',
    'get_climatology',
    'align_time_series',
    'is_summer_month',
    # Config loader
    'load_config',
    'get_credentials',
    'get_bbox',
    'get_date_range',
    'get_target_species',
    'get_prey_species',
    'get_data_product_config',
    'create_output_paths',
    'validate_config',
    'setup_nasa_credentials'
]
