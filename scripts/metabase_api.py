import os
import time
import sys
import re
import requests

class MetabaseAPI:
    def __init__(self, domain, email, password):
        self.domain = domain.rstrip('/')
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.token = None

    def authenticate(self):
        print(f"Authenticating with Metabase at {self.domain}...")
        url = f"{self.domain}/api/session"
        max_retries = 30
        for i in range(max_retries):
            try:
                response = self.session.post(url, json={
                    "username": self.email,
                    "password": self.password
                }, timeout=10)
                if response.status_code == 200:
                    self.token = response.json()['id']
                    self.session.headers.update({"X-Metabase-Session": self.token})
                    print("Successfully authenticated.")
                    return True
                elif response.status_code == 401:
                    return False
            except:
                if i % 5 == 0:
                    print(f"Waiting for Metabase... ({i}/{max_retries})")
                time.sleep(5)
        return False

    def setup_fresh(self, first_name, last_name):
        print("Performing initial setup...")
        try:
            props = self.session.get(f"{self.domain}/api/session/properties").json()
            token = props.get('setup-token')
        except:
            token = None
            
        if not token:
             return False

        data = {
            "token": token,
            "user": {
                "first_name": first_name,
                "last_name": last_name,
                "email": self.email,
                "password": self.password
            },
            "prefs": {"allow_tracking": False, "site_name": "Delivery Forensics"}
        }
        response = self.session.post(f"{self.domain}/api/setup", json=data)
        if response.status_code == 200:
            print("Setup complete.")
            return self.authenticate()
        print(f"Setup failed: {response.text}")
        return False

    def add_database(self, name, engine, details):
        print(f"Checking database: {name}...")
        resp = self.session.get(f"{self.domain}/api/database")
        dbs = resp.json()
        existing = dbs if isinstance(dbs, list) else dbs.get('data', [])
        for db in existing:
            if isinstance(db, dict) and db.get('name') == name:
                return db['id']

        data = {
            "name": name,
            "engine": engine,
            "details": details,
            "auto_run_queries": True,
            "is_full_sync": True
        }
        response = self.session.post(f"{self.domain}/api/database", json=data)
        if response.status_code == 200:
            return response.json()['id']
        return None

    def create_collection(self, name):
        resp = self.session.get(f"{self.domain}/api/collection")
        cols = resp.json()
        existing = cols if isinstance(cols, list) else cols.get('data', [])
        for col in existing:
            if col['name'] == name:
                return col['id']
        response = self.session.post(f"{self.domain}/api/collection", json={"name": name, "color": "#509EE3"})
        return response.json()['id']

    def sync_card(self, name, collection_id, database_id, sql_query, display="table", viz_settings=None):
        # We search by name to deduplicate
        items_resp = self.session.get(f"{self.domain}/api/collection/{collection_id}/items")
        if items_resp.status_code != 200:
            print(f"Failed to fetch collection items: {items_resp.text}")
            return None
        items = items_resp.json()
        data = items if isinstance(items, list) else items.get('data', [])
        
        # Exact match logic
        existing_id = None
        for item in data:
            if item.get('model') == 'card' and item['name'] == name:
                existing_id = item['id']
                break

        payload = {
            "name": name,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql_query},
                "database": database_id
            },
            "display": display,
            "collection_id": collection_id,
            "visualization_settings": viz_settings or {}
        }

        if existing_id:
            print(f"Updating card: {name} (ID {existing_id}) as {display}")
            self.session.put(f"{self.domain}/api/card/{existing_id}", json=payload)
            return existing_id
        else:
            print(f"Creating card: {name} as {display}")
            resp = self.session.post(f"{self.domain}/api/card", json=payload)
            if resp.status_code != 200:
                print(f"Failed to create card: {resp.text}")
                return None
            return resp.json()['id']

    def create_dashboard(self, name, collection_id):
        items_resp = self.session.get(f"{self.domain}/api/collection/{collection_id}/items")
        items = items_resp.json()
        data = items if isinstance(items, list) else items.get('data', [])
        for item in data:
            if item['model'] == 'dashboard' and item['name'] == name:
                return item['id']
        resp = self.session.post(f"{self.domain}/api/dashboard", json={"name": name, "collection_id": collection_id})
        return resp.json()['id']

    def finalize_dashboard(self, dashboard_id, tab_definitions):
        """
        v0.61 Advanced Tabbed Provisioning:
        Supports custom sizing and layout logic.
        tab_definitions: List of { 
            "name": "Tab Name", 
            "cards": [ { "id": card_id, "width": 9, "height": 6 }, ... ] 
        }
        """
        print(f"Finalizing advanced tabbed dashboard {dashboard_id}...")
        
        api_tabs = []
        updated_dashcards = []
        dc_count = 1
        
        for t_idx, tab in enumerate(tab_definitions):
            tab_id = -(t_idx + 1)
            api_tabs.append({"id": tab_id, "name": tab['name']})
            
            y_pos = 0
            current_row_width = 0
            row_height = 0
            
            for c_idx, card_cfg in enumerate(tab['cards']):
                # Support both simple IDs and config dicts
                if isinstance(card_cfg, (int, str)):
                    cid = int(card_cfg)
                    width = 18 # Default full width
                    height = 6
                else:
                    cid = int(card_cfg['id'])
                    width = card_cfg.get('width', 18)
                    height = card_cfg.get('height', 6)

                # Grid logic (Metabase v0.61 width is typically 18 or 24)
                # We assume 18 units for safety across resolutions.
                if current_row_width + width > 18:
                    y_pos += row_height
                    current_row_width = 0
                    row_height = 0
                
                updated_dashcards.append({
                    "id": -dc_count,
                    "card_id": cid,
                    "dashboard_tab_id": tab_id,
                    "row": y_pos,
                    "col": current_row_width,
                    "size_x": width,
                    "size_y": height,
                    "parameter_mappings": [],
                    "visualization_settings": {}
                })
                
                current_row_width += width
                row_height = max(row_height, height)
                dc_count += 1

        payload = {
            "tabs": api_tabs,
            "dashcards": updated_dashcards
        }
        
        print(f"Synchronizing {len(updated_dashcards)} dashcards across {len(api_tabs)} tabs...")
        resp = self.session.put(f"{self.domain}/api/dashboard/{dashboard_id}", json=payload)
        
        if resp.status_code == 200:
            print("Successfully updated dashboard with aesthetic layout.")
        else:
            print(f"Dashboard update failed: {resp.status_code} - {resp.text}")




