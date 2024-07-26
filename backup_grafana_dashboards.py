#!/usr/bin/env python3
"""
Created by Thomas Bourcey

This script exports Grafana dashboards to JSON files, preserving the folder structure.
Supports Prometheus, Loki, and InfluxDB datasources.

Version: 0.5.3

Usage:
    python export_grafana_dashboards.py [--grafana_url URL] [--api_key API_KEY] [--save_folder /path/to/save] [--export_sharing True/False] [--force True/False]
"""

import os
import requests
import json
import argparse
import sys

# Script version
script_version = "0.5.3"

# Default configuration for Grafana API
default_grafana_url = ''
default_api_key = ''
default_output_dir = 'backup_dashboard_grafana'
export_sharing_externally_support = True  # Default setting for "Export for sharing externally" support
force_write = False  # Default setting for force write option

# Mapping for datasource types
datasource_map = {
    'prometheus': {
        'name': 'DS_PROMETHEUS',
        'label': 'Prometheus',
        'description': '',
        'type': 'datasource',
        'pluginId': 'prometheus',
        'pluginName': 'Prometheus'
    },
    'loki': {
        'name': 'DS_LOKI',
        'label': 'Loki',
        'description': '',
        'type': 'datasource',
        'pluginId': 'loki',
        'pluginName': 'Loki'
    },
    'influxdb': {
        'name': 'DS_INFLUXDB',
        'label': 'InfluxDB',
        'description': '',
        'type': 'datasource',
        'pluginId': 'influxdb',
        'pluginName': 'InfluxDB'
    }
}

def get_folder_list(grafana_url, headers):
    """Retrieve the list of folders from Grafana."""
    folders_url = f'{grafana_url}/api/folders'
    response = requests.get(folders_url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_all_dashboards_and_folders(grafana_url, headers):
    """Retrieve the list of all dashboards and folders from Grafana."""
    search_url = f'{grafana_url}/api/search?query='
    response = requests.get(search_url, headers=headers)
    response.raise_for_status()
    return response.json()

def build_folder_structure(folders, dashboards, output_dir):
    """Build the folder structure based on retrieved folders and dashboards."""
    folder_structure = {folder['uid']: {'title': folder['title'], 'path': os.path.join(output_dir, folder['title'])} for folder in folders}
    
    for dashboard in dashboards:
        folder_uid = dashboard.get('folderUid')
        if folder_uid in folder_structure:
            folder_path = os.path.join(folder_structure[folder_uid]['path'], dashboard['title'])
            if dashboard['type'] == 'dash-folder':
                folder_structure[dashboard['uid']] = {'title': dashboard['title'], 'path': folder_path}
            else:
                folder_structure[folder_uid].setdefault('dashboards', []).append({
                    'uid': dashboard['uid'],
                    'title': dashboard['title'],
                    'path': folder_structure[folder_uid]['path']
                })

    return folder_structure

def export_dashboard(dashboard_uid, dashboard_title, folder_path, grafana_url, headers, export_sharing):
    """Export a single dashboard to a specified folder."""
    dashboard_url = f'{grafana_url}/api/dashboards/uid/{dashboard_uid}'
    response = requests.get(dashboard_url, headers=headers)
    response.raise_for_status()
    dashboard = response.json()
    
    if export_sharing:
        inputs = []
        requires = [{'type': 'grafana', 'id': 'grafana', 'name': 'Grafana', 'version': '11.0.0'}]
        elements = {}

        datasources = set()
        for panel in dashboard['dashboard'].get('panels', []):
            if 'datasource' in panel:
                ds = panel['datasource']
                if isinstance(ds, dict) and 'type' in ds:
                    datasources.add(ds['type'])
                elif isinstance(ds, str):
                    datasources.add(ds)

        for ds in datasources:
            if ds in datasource_map:
                inputs.append(datasource_map[ds])
                requires.append({
                    'type': 'datasource',
                    'id': ds,
                    'name': datasource_map[ds]['pluginName'],
                    'version': '1.0.0'
                })

        dashboard['dashboard']['__inputs'] = inputs
        dashboard['dashboard']['__elements'] = elements
        dashboard['dashboard']['__requires'] = requires
        dashboard['dashboard']['id'] = None
        for panel in dashboard['dashboard'].get('panels', []):
            if 'datasource' in panel:
                if isinstance(panel['datasource'], dict):
                    panel['datasource']['uid'] = "${DS_PROMETHEUS}"
            for target in panel.get('targets', []):
                if 'datasource' in target:
                    if isinstance(target['datasource'], dict):
                        target['datasource']['uid'] = "${DS_PROMETHEUS}"

        if 'templating' in dashboard['dashboard']:
            for variable in dashboard['dashboard']['templating'].get('list', []):
                variable['current'] = {}
                if 'datasource' in variable and isinstance(variable['datasource'], dict):
                    variable['datasource']['uid'] = "${DS_PROMETHEUS}"

    sanitized_title = ''.join(e for e in dashboard_title if e.isalnum() or e in (' ', '-', '_')).strip()
    output_path = os.path.join(folder_path, f'{sanitized_title}.json')
    os.makedirs(folder_path, exist_ok=True)

    dashboard_data = dashboard['dashboard']
    specific_info = {k: dashboard_data.get(k) for k in ['timezone', 'title', 'uid', 'version', 'weekStart']}
    
    # Update specific_info in the dashboard data without changing the original UID
    dashboard_data['__inputs'] = dashboard_data.get('__inputs', [])
    dashboard_data['__elements'] = dashboard_data.get('__elements', {})
    dashboard_data['__requires'] = dashboard_data.get('__requires', [])
    dashboard_data.update(specific_info)

    with open(output_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    print(f'Dashboard "{dashboard_title}" exported successfully in folder "{folder_path}".')

def export_dashboards(folder_structure, grafana_url, headers, export_sharing):
    """Export all dashboards based on the folder structure."""
    total_folders_created = 0
    total_dashboards_exported = 0

    for folder_uid, folder_info in folder_structure.items():
        if not os.path.exists(folder_info['path']):
            os.makedirs(folder_info['path'])
            total_folders_created += 1

        if 'dashboards' in folder_info:
            for dashboard in folder_info['dashboards']:
                export_dashboard(dashboard['uid'], dashboard['title'], dashboard['path'], grafana_url, headers, export_sharing)
                total_dashboards_exported += 1
    
    print(f"\nSummary:")
    print(f"Total folders created: {total_folders_created}")
    print(f"Total dashboards exported: {total_dashboards_exported}")

def main():
    parser = argparse.ArgumentParser(description=f'Export Grafana dashboards to JSON files. Version: {script_version}')
    parser.add_argument('--grafana_url', type=str, default=default_grafana_url, help='Grafana instance URL.')
    parser.add_argument('--api_key', type=str, default=default_api_key, help='Grafana API key.')
    parser.add_argument('--save_folder', type=str, default=default_output_dir, help='Folder to save exported dashboards.')
    parser.add_argument('--export_sharing', type=bool, default=export_sharing_externally_support, help='Enable export for sharing externally support.')
    parser.add_argument('--force', type=bool, default=force_write, help='Force writing to the output folder even if it is not empty.')
    args = parser.parse_args()

    grafana_url = args.grafana_url or default_grafana_url
    api_key = args.api_key or default_api_key
    output_dir = args.save_folder or default_output_dir
    export_sharing = args.export_sharing if args.export_sharing is not None else export_sharing_externally_support
    force = args.force if args.force is not None else force_write

    if not grafana_url:
        print("Error: Grafana URL must be specified either as a default or via --grafana_url.")
        sys.exit(1)
    if not api_key:
        print("Error: Grafana API key must be specified either as a default or via --api_key.")
        sys.exit(1)

    if os.path.exists(output_dir) and os.listdir(output_dir) and not force:
        print(f"Error: Output directory '{output_dir}' is not empty. Use --force True to overwrite.")
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        folders = get_folder_list(grafana_url, headers)
        dashboards = get_all_dashboards_and_folders(grafana_url, headers)
        folder_structure = build_folder_structure(folders, dashboards, output_dir)
        export_dashboards(folder_structure, grafana_url, headers, export_sharing)
    except requests.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
