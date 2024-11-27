import logging
import re

def get_device_data(client):


    def _extract_site_name(hostname):
        """
        Extracts the site name prefix from the hostname.
        """
        match = re.match(r'^(.*?)-\d{3,3}[a-zA-Z]?$', hostname)
        if match:
            return match.group(1)
        return hostname
    
    response = client.devices.get_device_count()
    device_count = response['response']
    logging.info('Number of devices managed by Cisco Catalyst Center: ' + str(device_count))
    offset = 1
    limit = 500
    device_list = []
    items=0
    while offset <= device_count:
        response = client.devices.get_device_list(offset=offset)
        offset += limit
        device_list.extend(response['response'])
        items += limit
        logging.info(f"Retrieved {items} devices")
    logging.info('Collected complete device list from Cisco Catalyst Center')


    response = client.sites.get_site_count()
    site_count = response['response']    
    logging.info('Number of sites managed by Cisco Catalyst Center: ' + str(site_count))
    offset = 1
    limit = 500
    site_list = []
    items=0
    while offset <= site_count:
        response = client.sites.get_site(offset=offset)
        offset += limit
        site_list.extend(response['response'])
        items += limit
        logging.info(f"Retrieved {items} sites")
    logging.info('Collected complete site list from Cisco Catalyst Center')
    
    # site_sn={}
    # logging.info('Retrieving device locations')
    # for site in site_list:
    #     #if site['siteNameHierarchy'] == 'Global': continue
    #     #logging.info(f"Processing site = {site['siteNameHierarchy']}")
    #     response=client.sites.get_membership(site_id=site.id)
    #     devices_response = response.get('device', [])
    #     for device_entry in devices_response:
    #         devices = device_entry.get('response', [])
    #         for device in devices:
    #             site_sn[device.get('serialNumber')]=site['siteNameHierarchy']
    #             logging.info(f"Assigning {site['siteNameHierarchy']} to {device.get('hostname')}/SN {device.get('serialNumber')}")
    # logging.info('Collected complete device mapping list from Cisco Catalyst Center')
               
    device_inventory = []
    items=0
    site_cache = {}
    
    for device in device_list:
        interfaces = []    
        logging.info(f"Fetching interfaces for device #{items}/{str(device_count)}: {device['hostname']}")
        # if 'serialNumber' not in device:
        #     logging.warning(f"Serial number not found on device. Skipping device {device['hostname']}.")
        #     continue

        # serial_number = device['serialNumber']
        # if serial_number not in site_sn:
        #     logging.warning(f"Serial number {serial_number} not found in site mapping. Skipping device {device['hostname']}.")
        #     continue
            
        # print(f"{site_sn[device.serialNumber]} - {device['hostname']}")   
        # device.site=site_sn[device.serialNumber]  
        
        
        try:
            logging.info(f"Fetching site name for device #{items}/{str(device_count)}: {device['hostname']}")
            site_prefix = _extract_site_name(device['hostname'])
            hostname = device.get('hostname')
            if site_prefix in site_cache:
                device.site = site_cache[site_prefix]
                logging.info(f"Using cached site name for {hostname}: {device.site}")
            else:
                response = client.devices.get_device_detail(identifier='uuid', search_by=device['id'])
                device.site = response['response']['location']
                site_cache[site_prefix] = device.site
                logging.info(f"Caching site name {device.site} for prefix {site_prefix}")
                
            if not 'Unified AP' in device.family:
                try:
                    response = client.devices.get_interface_info_by_id(device_id=device['id'])
                except:
                    logging.info(f"NON AP: No interfaces found for device {device['hostname']}")
                    device_inventory.append(device)
                    continue
            else:
                logging.info(f"AP: No interfaces found for device {device['hostname']}")
                device_inventory.append(device)
                continue

        except Exception as e:
            logging.error(f"An error occurred collecting device data: {e}")
            continue
        
        interfaces.extend(response['response'])  
        logging.info(f"Found {len(interfaces)} interfaces for {device['hostname']}")
        device.interfaces=interfaces
        
        device_inventory.append(device)
        
    return device_inventory
