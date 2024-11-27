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

    device_inventory = []
    
    for device in device_list:
        interfaces = []
        
        response = client.devices.get_device_detail(identifier='uuid', search_by=device['id'])
        site = response['response']['location']
        device.update({'site': site})
        logging.info(f"Found {device['hostname']} in {site}")

        try:
            response = client.devices.get_interface_info_by_id(device_id=device['id'])
        except:
            logging.error(f"No interfaces found for device {device['hostname']}")
            device_inventory.append(device)
            continue
            
        interfaces.extend(response['response'])  
        logging.info(f"Found {len(interfaces)} interfaces for {device['hostname']}")
        device.interfaces=interfaces
        
        device_inventory.append(device)
        
    return device_inventory
