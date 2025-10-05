"""
Interactive setup script for API credentials
Інтерактивне налаштування облікових даних
"""

import yaml
from pathlib import Path
import getpass
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from utils.config_loader import setup_nasa_credentials


def setup_credentials_interactive():
    """Інтерактивне налаштування облікових даних"""

    print("=" * 70)
    print("SHARK VOYAGER AI - Credentials Setup")
    print("=" * 70)
    print()
    print("This script will help you configure API credentials.")
    print("Press Enter to skip any optional credentials.")
    print()

    config_path = Path("config/config.yaml")

    # Завантажити існуючу конфігурацію
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # NASA Earthdata (обов'язково для MODIS, SMAP)
    print("1. NASA Earthdata Login (REQUIRED for MODIS SST/Chlorophyll, SMAP Salinity)")
    print("   Register at: https://urs.earthdata.nasa.gov/")
    nasa_user = input("   Username: ").strip()
    if nasa_user:
        nasa_pass = getpass.getpass("   Password: ")
        config['credentials']['nasa_earthdata']['username'] = nasa_user
        config['credentials']['nasa_earthdata']['password'] = nasa_pass

        # Налаштувати .netrc
        setup_netrc = input("   Setup .netrc file? (y/n): ").strip().lower()
        if setup_netrc == 'y':
            setup_nasa_credentials(nasa_user, nasa_pass)
            print("   ✓ .netrc configured")
    print()

    # Copernicus Marine (обов'язково для SLA)
    print("2. Copernicus Marine Service (REQUIRED for Sea Level Anomaly)")
    print("   Register at: https://data.marine.copernicus.eu/")
    cop_user = input("   Username: ").strip()
    if cop_user:
        cop_pass = getpass.getpass("   Password: ")
        config['credentials']['copernicus_marine']['username'] = cop_user
        config['credentials']['copernicus_marine']['password'] = cop_pass
        print("   ✓ Copernicus credentials saved")
    print()

    # Global Fishing Watch (опційно)
    print("3. Global Fishing Watch (OPTIONAL for fishing effort data)")
    print("   Request token at: https://globalfishingwatch.org/our-apis/tokens")
    gfw_token = input("   API Token: ").strip()
    if gfw_token:
        config['credentials']['global_fishing_watch']['api_token'] = gfw_token
        print("   ✓ GFW token saved")
    print()

    # GBIF (опційно, тільки для великих завантажень)
    print("4. GBIF (OPTIONAL - only needed for large downloads)")
    print("   Register at: https://www.gbif.org/")
    gbif_user = input("   Username: ").strip()
    if gbif_user:
        gbif_pass = getpass.getpass("   Password: ")
        gbif_email = input("   Email: ").strip()
        config['credentials']['gbif']['username'] = gbif_user
        config['credentials']['gbif']['password'] = gbif_pass
        config['credentials']['gbif']['email'] = gbif_email
        print("   ✓ GBIF credentials saved")
    print()

    # Зберегти конфігурацію
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print("=" * 70)
    print("✓ Credentials saved to config/config.yaml")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review config/config.yaml for study area and date range")
    print("2. Run: python main.py --step collect")
    print()
    print("Note: OCEARCH data requires separate permission.")
    print("Contact: tracker@ocearch.org")
    print()


if __name__ == "__main__":
    setup_credentials_interactive()
