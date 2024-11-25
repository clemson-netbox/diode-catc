import logging

def fetch_device_data(catc):
    """
    Fetches device data from Cisco DNA Center.
    """
    logging.info("Fetching devices from Cisco DNA Center...")
    devices = []
    try:
        devices = catc.devices.get_device_list()
    except Exception as e:
        logging.error(f"Error fetching devices: {e}")
    return devices

def fetch_interface_data(catc, device_id):
    """
    Fetches interface data for a specific device.
    """
    logging.info(f"Fetching interfaces for device {device_id}...")
    interfaces = []
    try:
        interfaces = catc.interfaces.get_interface_by_device_id(device_id=device_id)
    except Exception as e:
        logging.error(f"Error fetching interfaces for device {device_id}: {e}")
    return interfaces
