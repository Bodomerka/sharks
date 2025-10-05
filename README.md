# Shark Voyager AI - Data Collection and Processing Pipeline

Комплексна система збору та обробки океанографічних даних для моделювання середовища існування білої акули (*Carcharodon carcharias*).

## 📋 Огляд Проєкту

Цей проєкт реалізує повний pipeline для:

1. **Збору даних** з 9 різних джерел (супутникові дані, біорізноманіття, батиметрія)
2. **Стандартизації** всіх даних до єдиної просторової сітки (0.1°) та часового роздільності (тижнева)
3. **Генерації синтетичних змінних** (точки відсутності, індекс придатності розплідника)
4. **Інтеграції** всіх шарів для ML моделювання

### Стандарти Даних

- **Проєкція**: WGS 84 (EPSG:4326)
- **Просторова сітка**: 0.1° × 0.1° (~11 км)
- **Часове роздільність**: 1 тиждень (для динамічних даних)
- **Формати**: GeoTIFF (растри), GeoPackage/CSV (вектори)

## 🗂️ Структура Проєкту

```
sharks/
├── config/
│   └── config.yaml                    # Головна конфігурація
├── src/
│   ├── data_collection/               # Модулі збору даних
│   │   ├── ocearch_collector.py       # OCEARCH треки акул
│   │   ├── gbif_obis_collector.py     # Морські ссавці та косатки
│   │   ├── nasa_ocean_collector.py    # MODIS SST та Chlorophyll
│   │   ├── copernicus_collector.py    # Sea Level Anomaly
│   │   ├── smap_collector.py          # Солоність
│   │   ├── woa_collector.py           # Розчинений кисень
│   │   ├── gebco_collector.py         # Батиметрія
│   │   ├── gfw_collector.py           # Рибальське зусилля
│   │   └── shipping_lanes_collector.py # Морські шляхи
│   ├── processing/
│   │   └── standardize_data.py        # Стандартизація даних
│   ├── synthetic/
│   │   ├── generate_absence_points.py # Генерація точок відсутності
│   │   └── nursery_index.py           # Індекс придатності розплідника
│   └── utils/
│       ├── spatial_utils.py           # Просторові утиліти
│       ├── temporal_utils.py          # Часові утиліти
│       └── config_loader.py           # Завантаження конфігурації
├── data/
│   ├── raw/                           # Сирі дані
│   ├── processed/                     # Оброблені дані
│   └── final/                         # Фінальні датасети
├── notebooks/                         # Jupyter notebooks для аналізу
├── main.py                            # Головний скрипт
├── requirements.txt                   # Python залежності
└── README.md                          # Ця документація
```

## 🚀 Швидкий Старт

### 1. Встановлення Середовища

```bash
# Створити віртуальне середовище
python -m venv venv

# Активувати середовище
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Встановити залежності
pip install -r requirements.txt
```

### 2. Налаштування Облікових Даних

Відредагуйте `config/config.yaml` та додайте свої облікові дані:

```yaml
credentials:
  nasa_earthdata:
    username: "YOUR_NASA_USERNAME"
    password: "YOUR_NASA_PASSWORD"

  copernicus_marine:
    username: "YOUR_COPERNICUS_USERNAME"
    password: "YOUR_COPERNICUS_PASSWORD"

  global_fishing_watch:
    api_token: "YOUR_GFW_API_TOKEN"
```

#### Де отримати облікові дані:

- **NASA Earthdata**: https://urs.earthdata.nasa.gov/ (безкоштовна реєстрація)
- **Copernicus Marine**: https://data.marine.copernicus.eu/ (безкоштовна реєстрація)
- **Global Fishing Watch**: https://globalfishingwatch.org/our-apis/tokens (безкоштовно для дослідників)
- **OCEARCH**: Потребує дозволу - напишіть на tracker@ocearch.org

### 3. Запуск Pipeline

```bash
# Запустити весь pipeline
python main.py --step all

# Або окремі кроки:
python main.py --step collect    # Тільки збір даних
python main.py --step process    # Тільки обробка
python main.py --step synthetic  # Генерація синтетичних змінних
python main.py --step integrate  # Інтеграція даних
```

## 📊 Джерела Даних

### 1. Цільовий Вид: Білі Акули
- **Джерело**: OCEARCH Shark Tracker
- **Дані**: GPS треки з супутниковими мітками
- **Змінні**: `Shark_Presence_Status`, `Shark_ID`, `Sex`, `Life_Stage`, `Date`
- **Використання**: Точки присутності для моделей

### 2. Здобич: Морські Ссавці
- **Джерела**: GBIF, OBIS
- **Види**:
  - Zalophus californianus (California Sea Lion)
  - Mirounga angustirostris (Northern Elephant Seal)
  - Arctocephalus pusillus (Cape Fur Seal)
  - Phoca vitulina (Harbor Seal)
- **Змінна**: `Dist_to_Rookery_km` (відстань до колонії)

### 3. Конкуренти/Хижаки: Косатки
- **Джерела**: GBIF, OBIS
- **Вид**: Orcinus orca
- **Змінна**: `Orca_Density_Index` (індекс щільності 0-1)

### 4. Океанографія

#### Температура
- **Джерело**: NASA OceanColor - MODIS-Aqua Level 3
- **Роздільність**: 4 км / тижнево
- **Змінні**:
  - `SST_mean_C` (середня температура)
  - `SST_grad_C_km` (градієнт температури)

#### Продуктивність
- **Джерело**: MODIS-Aqua Chlorophyll-a
- **Роздільність**: 4 км / тижнево
- **Змінна**: `Chla_mean_mg_m3` (хлорофіл)

#### Динаміка Океану
- **Джерело**: Copernicus Marine / AVISO
- **Роздільність**: 0.25° / щоденно
- **Змінна**: `SSHA_mean_m` (аномалія рівня моря)

#### Солоність
- **Джерело**: SMAP Level 3
- **Роздільність**: 0.25° / тижнево
- **Змінна**: `Salinity_mean_PSU`

#### Кисень
- **Джерело**: World Ocean Atlas 2018
- **Тип**: Кліматологія
- **Змінна**: `Oxygen_bottom_ml_L` (кисень біля дна)

### 5. Геоморфологія
- **Джерело**: GEBCO 2023
- **Роздільність**: ~450 м
- **Змінні**:
  - `Depth_m` (глибина)
  - `Slope_deg` (нахил)

### 6. Антропогенний Тиск

#### Рибальство
- **Джерело**: Global Fishing Watch
- **Роздільність**: 0.1° / тижнево
- **Змінна**: `Fishing_Effort_h_km2`
- **Типи знарядь**: longline, purse seine

#### Судноплавство
- **Джерело**: NOAA ENC Direct
- **Тип**: Векторні лінії
- **Змінна**: `Dist_to_Shipping_Lane_km`

## 🔬 Синтетичні Змінні

### 1. Точки Відсутності (Absence Points)

Для тренування моделей класифікації генеруються псевдо-відсутності:

- **Метод**: Випадкові точки в межах ареалу, але поза 100 км буфером від точок присутності
- **Співвідношення**: 1:1 (рівна кількість absence:presence)
- **Розподіл**: Окремо для дорослих самців, самок та молоді

```python
from src.synthetic.generate_absence_points import AbsencePointsGenerator

generator = AbsencePointsGenerator(buffer_distance_km=100)
absence_points = generator.generate_for_all_life_stages(
    presence_points, bbox, ratio=1.0, save=True
)
```

### 2. Індекс Придатності Розплідника (Nursery Suitability Index)

Показник потенційної придатності для народження молодняку:

**Критерії:**
- Глибина < 100 м
- Нахил < 5°
- SST > 16°C (літні місяці)
- Хлорофіл > середнього

**Формула:** Кожен критерій додає 0.25 → індекс від 0 до 1

```python
from src.synthetic.nursery_index import NurserySuitabilityCalculator

calculator = NurserySuitabilityCalculator()
nursery_index = calculator.calculate_index(
    depth, slope, sst_summer, chlorophyll, save=True
)
```

### 3. Часові Фактори

До всіх точкових даних додаються:

- **Month** (1-12)
- **Week_of_Year** (1-52)
- **Season** (Winter, Spring, Summer, Autumn)

Це дозволяє моделям враховувати сезонність.

## 🛠️ Використання Окремих Модулів

### Збір Даних

```python
# MODIS SST та Chlorophyll
from src.data_collection.nasa_ocean_collector import NASAOceanCollector

collector = NASAOceanCollector()
sst_data = collector.download_modis_sst(
    date_range=("2020-01-01", "2023-12-31"),
    bbox={'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45},
    save=True
)
```

```python
# Морські ссавці та косатки
from src.data_collection.gbif_obis_collector import GBIFOBISCollector

collector = GBIFOBISCollector()
prey_species = ["Zalophus californianus", "Mirounga angustirostris"]
prey_data = collector.collect_prey_species(prey_species, bbox, save=True)
orca_data = collector.collect_orca_data(bbox, save=True)
```

### Обробка Даних

```python
from src.processing.standardize_data import DataStandardizer

standardizer = DataStandardizer(bbox, resolution=0.1)

# Обробити SST
sst_weekly = standardizer.process_sst(sst_ds)

# Обробити батиметрію
depth, slope = standardizer.process_bathymetry(bathy_grid)

# Створити растр відстаней до колоній
dist_raster = standardizer.process_rookeries(rookeries_gdf)
```

## 📝 Конфігурація

Головна конфігурація у `config/config.yaml` дозволяє налаштувати:

- **Просторові параметри**: bbox, роздільність
- **Часові параметри**: діапазон дат, часове роздільність
- **Облікові дані**: для всіх джерел даних
- **Параметри обробки**: методи ресемплювання, агрегації
- **Синтетичні змінні**: критерії для nursery index, параметри absence points

## 📚 Документація API

Детальна документація для кожного модуля з усіма параметрами та прикладами доступна у файлі:

```
oceanographic_data_sources_guide.md
```

## ⚠️ Важливі Примітки

### OCEARCH Дані
OCEARCH **не надає** офіційного публічного API. Для дослідницького використання даних:

1. Напишіть на tracker@ocearch.org
2. Опишіть ваш дослідницький проєкт
3. Запитайте дозвіл на використання даних
4. Отримайте угоду про обмін даними

### NASA Earthdata
Після створення облікового запису, налаштуйте `.netrc` файл:

```bash
# Linux/Mac: ~/.netrc
# Windows: ~/_netrc
machine urs.earthdata.nasa.gov
login YOUR_USERNAME
password YOUR_PASSWORD
```

Або використовуйте утиліту:

```python
from src.utils.config_loader import setup_nasa_credentials
setup_nasa_credentials("username", "password")
```

### Розміри Даних

Зверніть увагу на обсяги даних:

- **GEBCO Global**: ~7.5 GB
- **MODIS (3 роки, глобально)**: десятки GB
- **Регіональні дані (Eastern Pacific)**: ~5-10 GB

Рекомендується використовувати SSD та мінімум 50 GB вільного місця.

## 🤝 Внесок

Проєкт розроблено згідно з протоколом збору даних для дослідження білих акул.

### Цитування Даних

При використанні даних, будь ласка, цитуйте:

- **MODIS**: NASA Goddard Space Flight Center, Ocean Biology Processing Group
- **SMAP**: Remote Sensing Systems / NASA PO.DAAC
- **Copernicus**: E.U. Copernicus Marine Service
- **GEBCO**: GEBCO Compilation Group (2023), DOI:10.5285/f98b053b-0cbc-6c23-e053-6c86abc0af7b
- **GBIF**: GBIF.org
- **OBIS**: Ocean Biodiversity Information System, IOC-UNESCO
- **Global Fishing Watch**: globalfishingwatch.org

## 📧 Контакт

Для питань щодо проєкту або технічної підтримки, створіть issue у репозиторії.

## 📄 Ліцензія

Цей код надається "as is" для дослідницьких цілей. Дані підлягають ліцензіям їх відповідних провайдерів.

---

**Shark Voyager AI** - Прогнозування середовища існування білої акули з використанням машинного навчання та океанографічних даних.

Створено: 2025-10-05
