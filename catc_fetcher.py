import logging

def fetch_device_data(client):
    """
    Fetches Catalyst Center devices, sites, and interfaces, organized by site.
    """
    try:
        logging.info("Fetching all devices from Catalyst Center...")
        devices_response = client.devices.get_device_list()
        all_devices = {
            device.serialNumber: device for device in devices_response.response if hasattr(device, "serialNumber")
        }
        logging.info(f"Fetched {len(all_devices)} devices.")

        logging.info("Fetching all sites from Catalyst Center...")
        sites_response = client.sites.get_site()
        if not sites_response.response:
            raise ValueError("No sites found in Catalyst Center.")
        logging.info(f"Fetched {len(sites_response.response)} sites.")

        site_device_map = {}

        for site in sites_response.response:
            site_name = site.get("siteNameHierarchy", "Unknown")
            logging.info(f"Processing site: {site_name}")

            membership = client.sites.get_membership(site_id=site.id)
            if not membership or not hasattr(membership, "device") or not membership.device:
                logging.warning(f"No devices found for site: {site_name}")
                continue

            site_devices = []
            for member_device in membership.device.response:
                serial_number = member_device.get("serialNumber")
                if serial_number and serial_number in all_devices:
                    device_record = all_devices[serial_number]

                    # Fetch interfaces for this device
                    interfaces = []
                    try:
                        logging.info(f"Fetching interfaces for device: {device_record.hostname}")
                        interface_response = client.devices.get_interface_info_by_id(device_record.id)
                        if interface_response and hasattr(interface_response, "response"):
                            for interface in interface_response.response:
                                interfaces.append({
                                        "name": interface.portName,
                                        "mac": getattr(interface, "macAddress", None),
                                        "speed": interface.speed,
                                        "duplex": getattr(interface, "duplex", None),
                                        "enabled": interface.status.lower(),
                                        "ips": [
                                        f"{ip.address.ipAddress.address}/{ip.address.ipMask.addresss}" 
                                        for ip in getattr(interface, "addresses", {})
                                    ] if hasattr(interface, "addresses") else []
                                })
                    except Exception as e:
                        logging.error(f"Error fetching interfaces for device {device_record.hostname}: {e}")

                    # Add interfaces to the device record
                    device_record.interfaces = interfaces
                    site_devices.append(device_record)

            site_device_map[site_name] = site_devices
            logging.info(f"Completed processing site: {site_name}")

        logging.info("Completed fetching device data.")
        return site_device_map

    except Exception as e:
        logging.error(f"Error fetching data from Catalyst Center: {e}")
        raise

    
    
    #    for ip_info in interface.ipv4Address:
    #         ip = ip_info.ipAddress
    #         subnet = ip_info.subnetMask
    #         if ip and subnet:
    #             cidr = transformer.get_cidr(ip, subnet)
    #             if cidr:
    #                 ip_addresses.append(cidr)
    #     #TODO: IPV6 Addresses
        
    interfaces.append({
         "name": interface.portName,
         "mac": getattr(interface, "macAddress", None),
         "speed": interface.speed,
         "duplex": getattr(interface, "duplex", None),
         "enabled": interface.status.lower(),
         "ips": ip_addresses if ip_addresses else None, 
     })
