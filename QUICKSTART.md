# Shark Voyager AI - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Environment (2 min)

```bash
# Clone or navigate to project directory
cd d:\sharks

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate shark_habitat
```

### Step 2: Setup Credentials (3 min)

```bash
# Interactive setup
python setup_credentials.py
```

You'll need accounts for:
- ✅ **NASA Earthdata** → https://urs.earthdata.nasa.gov/
- ✅ **Copernicus Marine** → https://data.marine.copernicus.eu/
- ⭕ **Global Fishing Watch** → https://globalfishingwatch.org/our-apis/tokens (optional)

### Step 3: Run Pipeline

```bash
# Collect all data
python main.py --step collect

# Process data
python main.py --step process

# Generate synthetic variables
python main.py --step synthetic

# Or run everything at once
python main.py --step all
```

---

## 📋 Common Commands

### Data Collection

```bash
# Collect only specific sources (edit main.py to uncomment)
python main.py --step collect
```

### Custom Region

Edit `config/config.yaml`:

```yaml
spatial:
  bbox:
    min_lon: -130.0
    max_lon: -110.0
    min_lat: 25.0
    max_lat: 45.0
```

### Custom Date Range

```yaml
temporal:
  start_date: "2020-01-01"
  end_date: "2023-12-31"
```

---

## 🔍 Check Results

```bash
# View collected data
ls data/raw/*/

# View processed data
ls data/processed/

# View final datasets
ls data/final/
```

---

## 🐍 Quick Python Usage

```python
# Import utilities
from src.utils import load_config, create_target_grid

# Load configuration
config = load_config()

# Create a collector
from src.data_collection.nasa_ocean_collector import NASAOceanCollector
collector = NASAOceanCollector()

# Download data
sst = collector.download_modis_sst(
    date_range=("2023-01-01", "2023-12-31"),
    bbox={'min_lon': -130, 'max_lon': -110, 'min_lat': 25, 'max_lat': 45}
)
```

---

## ⚙️ Useful Configurations

### High-Resolution Data

```yaml
spatial:
  resolution: 0.05  # 5km instead of 11km
```

### Different Time Resolution

```yaml
temporal:
  resolution: "1D"  # Daily instead of weekly
```

### Change Output Directory

```yaml
paths:
  data_processed: "./output/processed"
  data_final: "./output/final"
```

---

## 🆘 Troubleshooting

### NASA Earthdata Login Fails

```bash
# Check .netrc file exists
cat ~/.netrc  # Linux/Mac
type ~\_netrc  # Windows

# Or setup manually
python -c "from src.utils.config_loader import setup_nasa_credentials; setup_nasa_credentials('USERNAME', 'PASSWORD')"
```

### Import Errors

```bash
# Reinstall environment
conda env remove -n shark_habitat
conda env create -f environment.yml
conda activate shark_habitat
```

### Out of Memory

Edit `config/config.yaml` to process smaller regions or shorter time periods.

### Missing Data

Some sources require:
- ✅ **OCEARCH**: Contact tracker@ocearch.org for permission
- ✅ **GFW**: Free API token required

---

## 📊 Example Workflow

### 1. Collect Test Data (Small Region)

```yaml
# config/config.yaml
spatial:
  bbox:
    min_lon: -122.0
    max_lon: -120.0
    min_lat: 36.0
    max_lat: 38.0

temporal:
  start_date: "2023-01-01"
  end_date: "2023-03-31"
```

```bash
python main.py --step collect
```

### 2. Process and Standardize

```bash
python main.py --step process
```

### 3. Generate Synthetic Variables

```bash
python main.py --step synthetic
```

### 4. View Results

```python
import xarray as xr
import geopandas as gpd

# Load processed SST
sst = xr.open_dataset("data/processed/SST_weekly.nc")
print(sst)

# Load rookery distances
import rasterio
with rasterio.open("data/processed/Dist_to_Rookery.tif") as src:
    dist = src.read(1)
    print(f"Distance range: {dist.min()}-{dist.max()} km")
```

---

## 🎯 Next Steps

1. **Verify data quality** in `data/processed/`
2. **Extract features** at shark occurrence points
3. **Train ML models** (Random Forest, MaxEnt, etc.)
4. **Create habitat suitability maps**
5. **Validate predictions**

---

## 📚 More Information

- **Full Documentation**: [README.md](README.md)
- **Data Sources Guide**: [oceanographic_data_sources_guide.md](oceanographic_data_sources_guide.md)
- **Project Summary**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

**Ready to model shark habitat? Start collecting data now! 🦈**

```bash
python main.py --step all
```
