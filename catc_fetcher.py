import re
import os
import json
from transformer import Transformer

def get_device_data(client,logging):

    SITE_CACHE_FILE = "./site_cache.json"
    transformer = Transformer("includes/site_rules.yml","includes/skip_device_rules.yml")

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

    def _extract_site_prefix(hostname):
        try:
            # Access Points Regex
            ap_regex = r"^([a-z].+)-[^-]+-[ap]*[0-9]{4,4}.*$"
            # Routers/Switches Regex
            rs_regex = r"^(.*)-[Cc]*[0-9]{4,4}-.+$"
            #rs_regex = r"^(.+)-C*\d{4,4}.+$"

            ap_match = re.match(ap_regex, hostname)
            if ap_match:
                return ap_match.group(1)
            rs_match = re.match(rs_regex, hostname)
            if rs_match:
                return rs_match.group(1)
            return hostname
        except re.error as e:
            logging.error(f"Regex error processing hostname {hostname}: {e}")
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
            hostname = device.get('hostname')
            if transformer.should_skip_device(hostname):
                continue
            
            logging.debug(f"Retrieving site name for device #{items}/{str(device_count)}: {hostname}")
            site_prefix = _extract_site_prefix(hostname)
            if site_prefix in site_cache:
                device.site = site_cache[site_prefix]
                logging.debug (f"Using cache {site_prefix}: {device.site}")
            else:
                response = client.devices.get_device_detail(identifier='uuid', search_by=device['id'])
                device.site = response['response']['location']
                logging.debug(f"Cache Miss: {hostname}: {device.site}")
                if site_prefix != hostname:
                    site_cache[site_prefix] = device.site
                    logging.debug(f"CACHING prefix {site_prefix}")
                    _save_site_cache(site_cache) 
                
            #AP have no interfaces in CATC    
            if not 'Unified AP' in device.family:
                try:
                    logging.info(f"Retrieving interfaces for device #{items}/{str(device_count)}: {device['hostname']}")
                    response = client.devices.get_interface_info_by_id(device_id=device['id'])        
                    interfaces.extend(response['response'])  
                    device.interfaces=interfaces
                    logging.debug(f"Found {len(interfaces)} interfaces for {device['hostname']}")
                except:
                    logging.debug(f"No interfaces found for device {device['hostname']}")
                    continue
    
        except Exception as e:
            logging.error(f"An error occurred collecting device data: {e}")
            continue
        
        device_inventory.append(device)
        
    return device_inventory
