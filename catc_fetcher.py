import re
import os
import json

def get_device_data(client,logging):

    SITE_CACHE_FILE = "./site_cache.json"

    def _load_site_cache():
        if os.path.exists(SITE_CACHE_FILE):
            with open(SITE_CACHE_FILE, "r") as file:
                try:
                    site_cache = json.load(file)
                    logging.debug(f"Loaded site cache from {SITE_CACHE_FILE}")
                    return site_cache
                except json.JSONDecodeError as e:
                    logging.warning(f"Could not decode site cache file: {e}")
      
        logging.debug(f"No cache found at {SITE_CACHE_FILE}")                    
        return {}  # Return an empty cache if the file doesn't exist or is invalid

    def _save_site_cache(site_cache):
        try:
            with open(SITE_CACHE_FILE, "w") as file:
                json.dump(site_cache, file, indent=4)
                logging.debug(f"Saved site cache to {SITE_CACHE_FILE}")
        except Exception as e:
            logging.error(f"Failed to save site cache: {e}")

    def _extract_site_name(hostname):
        """
        Extracts the site name prefix from the hostname.
        """
        match = re.match(r'^(.+?)-[C0-9]{2,3}.*$', hostname)
        if match:
            return match.group(1)
        else:
            match = re.match(r'^([a-z]-.+)-.+-ap.*$', hostname)
            if match:
                return match.group(1)
        return hostname
    
    response = client.devices.get_device_count()
    device_count = response['response']
    logging.info(f'Retrieving {device_count} devices from Cisco Catalyst Center')
    offset = 1
    limit = 500
    device_list = []
    items=0
    while offset <= device_count:
        response = client.devices.get_device_list(offset=offset)
        offset += limit
        device_list.extend(response['response'])
        items += limit
        logging.debug(f"Retrieved {items} devices")
    logging.info('Collected complete device list from Cisco Catalyst Center')


    response = client.sites.get_site_count()
    site_count = response['response']    
    logging.info(f'Retrieving {site_count} sites from Cisco Catalyst Center')
    offset = 1
    limit = 500
    site_list = []
    items=0
    while offset <= site_count:
        response = client.sites.get_site(offset=offset)
        offset += limit
        site_list.extend(response['response'])
        items += limit
        logging.debug(f"Retrieved {items} sites")
    logging.info('Collected complete site list from Cisco Catalyst Center')
    
    device_inventory = []
    items=0
    site_cache = _load_site_cache()  # Load cache at startup
    
    for device in device_list:
        interfaces = []   
        items += 1         
        
        try:
            logging.debug(f"Retrieving site name for device #{items}/{str(device_count)}: {device['hostname']}")
            site_prefix = _extract_site_name(device['hostname'])
            hostname = device.get('hostname')
            if site_prefix in site_cache:
                device.site = site_cache[site_prefix]
                logging.info(f"Using cached site name for {site_prefix} {hostname}: {device.site}")
            else:
                response = client.devices.get_device_detail(identifier='uuid', search_by=device['id'])
                device.site = response['response']['location']
                site_cache[site_prefix] = device.site
                logging.info(f"Caching site name {device.site} for prefix {site_prefix}")
                
            #AP have no interfaces in CATC    
            if not 'Unified AP' in device.family:
                try:
                    logging.info(f"Fetching interfaces for device #{items}/{str(device_count)}: {device['hostname']}")
                    response = client.devices.get_interface_info_by_id(device_id=device['id'])
                except:
                    logging.debug(f"No interfaces found for device {device['hostname']}")
                    device_inventory.append(device)
                    continue
            else:
                device_inventory.append(device)
                continue

        except Exception as e:
            logging.error(f"An error occurred collecting device data: {e}")
            continue
        
        interfaces.extend(response['response'])  
        logging.debug(f"Found {len(interfaces)} interfaces for {device['hostname']}")
        device.interfaces=interfaces
        _save_site_cache(site_cache)  # Save cache at the end of processing

        device_inventory.append(device)
    return device_inventory
