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

    device_inventory = []
        
    items=0
    for device in device_list:
        interfaces = []
    
        logging.info(f"Found device #{items}/{str(device_count)}: {device['hostname']}")
        
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
        items += 1
        
    return device_inventory
