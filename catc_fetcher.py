import logging

def get_device_data(client):
    # get the device count
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
    logging.info('Number of devices managed by Cisco Catalyst Center: ' + str(site_count))

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

    site_sn={}
    logging.info('Retrieving device locations')
    for site in site_list:
        if site['siteNameHierarchy'] == 'Global': continue
        logging.info(f"Processing site = {site['siteNameHierarchy']}")
        response=client.sites.get_membership(site_id=site.id)
        devices_response = response.get('device', [])
        for device_entry in devices_response:
            device_list = device_entry.get('response', [])
            for device in device_list:
                items += 1
                site_sn[device.get('serialnumber')]=site['siteNameHierarchy']
                if items % 500 == 0:
                    logging.info(f"Processed {items}/{str(device_count)} devices ")
    
                #logging.info(f"Assigning {site['siteNameHierarchy']} to {device.get('hostname')}/SN {device.get('serialNumber')}")
    logging.info('Collected complete device mapping list from Cisco Catalyst Center')
               
    device_inventory = []
        
    items=0
    for device in device_list:
        items += 1

        interfaces = []
    
        logging.info(f"Found device #{items}/{str(device_count)}: {device['hostname']}")
        if 'serialNumber' not in device:
            continue
        
        print(f"{site_sn[device.serialNumber]} - {device['hostname']}")   
        device.site=site_sn[device.serialNumber]  
        
        try:
            if not 'Unified AP' in device.family:
                try:
                    response = client.devices.get_interface_info_by_id(device_id=device['id'])
                except:
                    logging.info(f"No interfaces found for device {device['hostname']}")
                    device_inventory.append(device)
                    continue
            else:
                logging.info(f"No interfaces found for device {device['hostname']}")
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
