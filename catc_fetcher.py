import logging

def get_device_data(client):


    def _extract_site_name(hostname):
        """
        Extracts the site name prefix from the hostname.
        """
        if '-' in hostname:
            parts = hostname.split('-')
            return '-'.join(parts[:-2])
        elif '.' in hostname:
            parts = hostname.split('.')
            return '-'.join(parts[:-2])
        return hostname  # Return full hostname if no clear separator

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
    
    site_sn = {}
    site_cache = {}  # Cache for inferred site names

    logging.info('Retrieving device locations')
    for site in site_list:
        # Skip the Global site if necessary
        # if site['siteNameHierarchy'] == 'Global': continue

        try:
            logging.info(f"Processing site: {site['siteNameHierarchy']}")
            response = client.sites.get_membership(site_id=site.id)
            devices_response = response.get('device', [])

            for device_entry in devices_response:
                devices = device_entry.get('response', [])

                for device in devices:
                    serial_number = device.get('serialNumber')
                    hostname = device.get('hostname')

                    # Infer site name from hostname and cache it
                    if hostname:
                        site_prefix = _extract_site_name(hostname)
                        if site_prefix in site_cache:
                            inferred_site = site_cache[site_prefix]
                            logging.info(f"Using cached site name for {hostname}: {inferred_site}")
                        else:
                            inferred_site = site['siteNameHierarchy']
                            site_cache[site_prefix] = inferred_site
                            logging.info(f"Caching site name {inferred_site} for prefix {site_prefix}")

                        # Assign the inferred site name
                        site_sn[serial_number] = inferred_site

                    else:
                        # Fallback to current site name if no hostname
                        site_sn[serial_number] = site['siteNameHierarchy']
                        logging.info(f"Assigning {site['siteNameHierarchy']} to device with SN {serial_number}")

        except Exception as e:
            logging.error(f"Error processing site {site['siteNameHierarchy']}: {e}")

    logging.info('Collected complete device mapping list from Cisco Catalyst Center')
                
    device_inventory = []
    items=0
    
    for device in device_list:
        interfaces = []    
        logging.info(f"Fetching interfaces for device #{items}/{str(device_count)}: {device['hostname']}")
        if 'serialNumber' not in device:
            logging.warning(f"Serial number not found on device. Skipping device {device['hostname']}.")
            continue

        serial_number = device['serialNumber']
        if serial_number not in site_sn:
            logging.warning(f"Serial number {serial_number} not found in site mapping. Skipping device {device['hostname']}.")
            continue
            
        print(f"{site_sn[device.serialNumber]} - {device['hostname']}")   
        device.site=site_sn[device.serialNumber]  
        try:
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
