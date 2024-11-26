import logging

def get_paginated_objects(client, fetch_method, object_name, limit=500):

    logging.info(f"Fetching all {object_name} from Catalyst Center...")
    results = []
    offset = 1

    while True:
        try:
            response = fetch_method(offset=offset, limit=limit)
            if not response or not hasattr(response, "response"):
                break
            results.extend(response.response)
            logging.info(f"Fetched {len(response.response)} {object_name} (offset: {offset})")
            if len(response.response) < limit:
                break
            offset += limit
        except Exception as e:
            logging.error(f"Error fetching {object_name} at offset {offset}: {e}")
            break

    logging.info(f"Fetched a total of {len(results)} {object_name}.")
    return results

def get_sites_with_devices(client):

    sites = get_paginated_objects(client, client.sites.get_site, "sites")
    site_structure = []

    for site in sites:
        site_name = site.get("siteNameHierarchy", "Unknown")
        site_entry = {"name": site_name, "devices": []}
        try:
            response = client.sites.get_membership(site_id=site.id)
            
            if len(response.device) == 1:
                logging.warning(f"No devices found for site: {site_name}")
            else:
                for members in response.device:
                    for member in members.response:
                        logging.info(f"{member} found for site: {site_name}")
                        site_entry["devices"].append(member.response)
        except Exception as e:
            logging.error(f"Error fetching membership for site {site_name}: {e}")

        site_structure.append(site_entry)

    return site_structure

def get_device_details(client):

    devices = get_paginated_objects(client, client.devices.get_device_list, "devices")
    return {device.serialNumber: device for device in devices if hasattr(device, "serialNumber")}

def get_interfaces(client, device_id):
    """
    Fetches interfaces for a device by ID.
    """
    interfaces = []
    try:
        response = client.devices.get_interface_info_by_id(device_id)
        if response and hasattr(response, "response"):
            for interface in response.response:
                interfaces.append({
                    "name": interface.portName,
                    "macAddress": interface.macAddress,
                    "speed": interface.speed * 1000 if hasattr(interface, "speed") else None,
                    "type": interface.interfaceType if hasattr(interface, "interfaceType") else None,
                    "status": interface.status if hasattr(interface, "status") else "unknown",
                    "ips": [
                        f"{ip.ipAddress}/{ip.prefixLength}" 
                        for ip in getattr(interface, "ipConfig", {}).get("ipAddress", [])
                    ] if hasattr(interface, "ipConfig") else []
                })
    except Exception as e:
        logging.error(f"Error fetching interfaces for device ID {device_id}: {e}")
    return interfaces

def merge_data(client):
    """
    Merges site, device, and interface data into a single structure.
    """
    try:
        # Fetch all sites with their devices
        site_structure = get_sites_with_devices(client)

        # Fetch all devices
        device_dict = get_device_details(client)

        # Enrich devices with interfaces and IPs
        for site in site_structure:
            for member_device in site["devices"]:
                serial_number = member_device.get("serialNumber")
                if serial_number in device_dict:
                    device = device_dict[serial_number]
                    device_id = device.id
                    interfaces = get_interfaces(client, device_id) if device_id else []

                    # Update member device with complete details
                    member_device.update({
                        "site": site["name"],
                        "interfaces": interfaces,
                        "details": device  # Include full device details
                    })

        logging.info("Data merging complete.")
        return site_structure

    except Exception as e:
        logging.error(f"Error merging data: {e}")
        raise

