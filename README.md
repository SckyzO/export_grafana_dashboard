# Grafana Dashboard Backup

This Python script backs up Grafana dashboards to JSON files while preserving the folder structure and supporting the "Export for sharing externally" feature of Grafana. It supports Prometheus, Loki, and InfluxDB datasources.

## Features
- Backup Grafana dashboards to JSON files.
- Preserve the folder structure of dashboards.
- Support for Prometheus, Loki, and InfluxDB datasources.
- Configurable via command line arguments or default values in the script.
- Option to enable or disable "Export for sharing externally" support.
- Option to force write to the output folder even if it is not empty.

## Requirements

Python 3.x
- requests library (install using pip install requests)

## Usage

```
python backup_grafana_dashboards.py \ 
  [--grafana_url URL] \
  [--api_key API_KEY] \ 
  [--save_folder /path/to/save] \
  [--export_sharing True/False] \
  [--force True/False]
```

### Command Line Arguments


- `--grafana_url`: The URL of your Grafana instance.
- `--api_key`: The API key for your Grafana instance.
- `--save_folder`: The folder to save the backed-up dashboards. Default is `backup_dashboard_grafana`.
- `--export_sharing`: Enable or disable "Export for sharing externally" support. Default is `True`.
- `--force`: Force writing to the output folder even if it is not empty. Default is `False`.

### Example

```
python backup_grafana_dashboards.py --grafana_url https://monitoring.domain.local --api_key your_api_key --save_folder /tmp/backup_dashboard_grafana --export_sharing True --force True
```

## Default Configuration in Script

You can set default values directly in the script:

```
# Default configuration for Grafana API
default_grafana_url = 'http://your-grafana-instance'
default_api_key = 'your_grafana_api_key'
default_output_dir = 'backup_dashboard_grafana'
export_sharing_externally_support = True  # Enable or disable "Export for sharing externally" support by default
force_write = False  # Force write to the output folder even if it is not empty
```
