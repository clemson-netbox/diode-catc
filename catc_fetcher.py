import logging

def get_device_data(client):
    # get the device count
    response = client.devices.get_device_count()
    device_count = response['response']
    logging.info('Number of devices managed by Cisco Catalyst Center: ' + str(device_count))

    # get the device info list
    offset = 1
    limit = 500
    device_list = []
    interfaces = []
    items=0
    while offset <= device_count:
        response = client.devices.get_device_list(offset=offset)
        offset += limit
        device_list.extend(response['response'])
        items += limit
        logging.info(f"Retrieved {items} devices")
    logging.info('Collected the device list from Cisco Catalyst Center')

    device_inventory = []
    for device in device_list:

        # get the device site hierarchy
        response = client.devices.get_device_detail(identifier='uuid', search_by=device['id'])
        site = response['response']['location']
        device.update({'site': site})
        logging.info(f"Collected site {site} for {device['hostname']}")

        try:
            response = client.devices.get_interface_info_by_id(device_id=device['id'])
        except:
            logging.error("No interfaces found for device {device['hostname']}")
            
        interfaces.extend(response['response'])  
        for interface in interfaces:
            logging.info(f"Collected interface {interface.portName} for {device['hostname']}")
        device.interfaces=interfaces
        
        device_inventory.append(device)
        
    logging.info('Collected the device inventory from Cisco DNA Center')
    return device_inventory
