"""
Temporal utilities for Shark Voyager AI project
Функції для часової обробки даних
"""

import pandas as pd
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
from typing import Union, Tuple


def aggregate_to_weekly(
    data: Union[xr.DataArray, xr.Dataset],
    method: str = 'mean'
) -> Union[xr.DataArray, xr.Dataset]:
    """
    Агрегувати дані до тижневого розділення

    Parameters:
    -----------
    data : xr.DataArray or xr.Dataset
        Вхідні дані з часовою координатою
    method : str
        Метод агрегації: 'mean', 'sum', 'median', 'max', 'min'

    Returns:
    --------
    weekly_data : xr.DataArray or xr.Dataset
        Дані, агреговані до тижневого розділення
    """
    # Переконатися, що є часова координата
    time_coord = get_time_coordinate(data)

    if time_coord is None:
        raise ValueError("No time coordinate found in data")

    # Виконати агрегацію
    if method == 'mean':
        weekly_data = data.resample({time_coord: '1W'}).mean()
    elif method == 'sum':
        weekly_data = data.resample({time_coord: '1W'}).sum()
    elif method == 'median':
        weekly_data = data.resample({time_coord: '1W'}).median()
    elif method == 'max':
        weekly_data = data.resample({time_coord: '1W'}).max()
    elif method == 'min':
        weekly_data = data.resample({time_coord: '1W'}).min()
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    return weekly_data


def get_time_coordinate(data: Union[xr.DataArray, xr.Dataset]) -> Union[str, None]:
    """
    Знайти назву часової координати в xarray об'єкті

    Parameters:
    -----------
    data : xr.DataArray or xr.Dataset
        Вхідні дані

    Returns:
    --------
    time_coord : str or None
        Назва часової координати або None
    """
    possible_names = ['time', 'Time', 'date', 'Date', 'datetime']

    for name in possible_names:
        if name in data.coords:
            return name

    return None


def add_temporal_features(
    df: pd.DataFrame,
    date_column: str = 'Date'
) -> pd.DataFrame:
    """
    Додати часові ознаки (Month, Week_of_Year) до DataFrame

    Parameters:
    -----------
    df : pd.DataFrame
        Вхідний DataFrame
    date_column : str
        Назва колонки з датами

    Returns:
    --------
    df : pd.DataFrame
        DataFrame з додатковими колонками Month, Week_of_Year
    """
    df = df.copy()

    # Конвертувати в datetime, якщо потрібно
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])

    # Додати ознаки
    df['Month'] = df[date_column].dt.month
    df['Week_of_Year'] = df[date_column].dt.isocalendar().week

    return df


def filter_date_range(
    data: Union[xr.DataArray, xr.Dataset, pd.DataFrame],
    start_date: str,
    end_date: str,
    date_column: str = None
) -> Union[xr.DataArray, xr.Dataset, pd.DataFrame]:
    """
    Відфільтрувати дані за діапазоном дат

    Parameters:
    -----------
    data : xr.DataArray, xr.Dataset, or pd.DataFrame
        Вхідні дані
    start_date : str
        Початкова дата (формат: 'YYYY-MM-DD')
    end_date : str
        Кінцева дата (формат: 'YYYY-MM-DD')
    date_column : str, optional
        Назва колонки дат для DataFrame

    Returns:
    --------
    filtered : same type as input
        Відфільтровані дані
    """
    if isinstance(data, (xr.DataArray, xr.Dataset)):
        time_coord = get_time_coordinate(data)
        if time_coord is None:
            raise ValueError("No time coordinate found")

        filtered = data.sel({time_coord: slice(start_date, end_date)})

    elif isinstance(data, pd.DataFrame):
        if date_column is None:
            raise ValueError("date_column must be specified for DataFrame")

        # Конвертувати в datetime
        df = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column])

        # Фільтрувати
        mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
        filtered = df[mask]

    else:
        raise TypeError("Unsupported data type")

    return filtered


def get_season(month: int) -> str:
    """
    Отримати пору року за номером місяця

    Parameters:
    -----------
    month : int
        Номер місяця (1-12)

    Returns:
    --------
    season : str
        Пора року: 'Winter', 'Spring', 'Summer', 'Autumn'
    """
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:  # 9, 10, 11
        return 'Autumn'


def add_season_column(
    df: pd.DataFrame,
    date_column: str = 'Date'
) -> pd.DataFrame:
    """
    Додати колонку з порою року

    Parameters:
    -----------
    df : pd.DataFrame
        Вхідний DataFrame
    date_column : str
        Назва колонки з датами

    Returns:
    --------
    df : pd.DataFrame
        DataFrame з додатковою колонкою Season
    """
    df = df.copy()

    # Переконатися, що є колонка Month
    if 'Month' not in df.columns:
        df = add_temporal_features(df, date_column)

    df['Season'] = df['Month'].apply(get_season)

    return df


def create_weekly_dates(
    start_date: str,
    end_date: str
) -> pd.DatetimeIndex:
    """
    Створити послідовність тижневих дат

    Parameters:
    -----------
    start_date : str
        Початкова дата (формат: 'YYYY-MM-DD')
    end_date : str
        Кінцева дата (формат: 'YYYY-MM-DD')

    Returns:
    --------
    dates : pd.DatetimeIndex
        Тижневі дати
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='W-MON')
    return dates


def interpolate_to_weekly(
    data: xr.DataArray,
    start_date: str,
    end_date: str
) -> xr.DataArray:
    """
    Інтерполювати дані до тижневої сітки

    Parameters:
    -----------
    data : xr.DataArray
        Вхідні дані з часовою координатою
    start_date : str
        Початкова дата
    end_date : str
        Кінцева дата

    Returns:
    --------
    interpolated : xr.DataArray
        Інтерпольовані дані
    """
    time_coord = get_time_coordinate(data)

    if time_coord is None:
        raise ValueError("No time coordinate found")

    # Створити цільові дати
    weekly_dates = create_weekly_dates(start_date, end_date)

    # Інтерполяція
    interpolated = data.interp({time_coord: weekly_dates}, method='linear')

    return interpolated


def get_climatology(
    data: xr.DataArray,
    groupby: str = 'month'
) -> xr.DataArray:
    """
    Розрахувати кліматологію (середнє по місяцях або тижнях)

    Parameters:
    -----------
    data : xr.DataArray
        Вхідні дані з часовою координатою
    groupby : str
        Групувати за: 'month', 'week', 'season'

    Returns:
    --------
    climatology : xr.DataArray
        Кліматологічні значення
    """
    time_coord = get_time_coordinate(data)

    if time_coord is None:
        raise ValueError("No time coordinate found")

    if groupby == 'month':
        climatology = data.groupby(f'{time_coord}.month').mean()
    elif groupby == 'week':
        climatology = data.groupby(f'{time_coord}.week').mean()
    elif groupby == 'season':
        climatology = data.groupby(f'{time_coord}.season').mean()
    else:
        raise ValueError(f"Unknown groupby option: {groupby}")

    return climatology


def align_time_series(
    data1: xr.DataArray,
    data2: xr.DataArray,
    method: str = 'outer'
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Вирівняти два часові ряди за часовою координатою

    Parameters:
    -----------
    data1, data2 : xr.DataArray
        Вхідні дані
    method : str
        Метод вирівнювання: 'inner', 'outer', 'left', 'right'

    Returns:
    --------
    aligned1, aligned2 : xr.DataArray
        Вирівняні дані
    """
    time_coord1 = get_time_coordinate(data1)
    time_coord2 = get_time_coordinate(data2)

    if time_coord1 is None or time_coord2 is None:
        raise ValueError("Time coordinate not found in one or both datasets")

    # Перейменувати координати для узгодження
    if time_coord1 != time_coord2:
        data2 = data2.rename({time_coord2: time_coord1})

    # Вирівняти
    aligned1, aligned2 = xr.align(data1, data2, join=method)

    return aligned1, aligned2


def is_summer_month(date: Union[pd.Timestamp, datetime], months: list = [6, 7, 8]) -> bool:
    """
    Перевірити, чи дата належить до літніх місяців

    Parameters:
    -----------
    date : pd.Timestamp or datetime
        Дата для перевірки
    months : list
        Список літніх місяців (за замовчуванням: червень, липень, серпень)

    Returns:
    --------
    is_summer : bool
    """
    if isinstance(date, pd.Timestamp):
        month = date.month
    elif isinstance(date, datetime):
        month = date.month
    else:
        raise TypeError("Date must be pd.Timestamp or datetime")

    return month in months
