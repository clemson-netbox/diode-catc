import logging

def fetch_device_data(client):
    """
    Fetches Catalyst Center devices, sites, and interfaces, organized by site.
    """
    try:
        # logging.info("Fetching all devices from Catalyst Center...")
        # devices_response = []
        # offset = 1
        # limit = 500  
        # while True:
        #     response = client.devices.get_device_list(offset=offset, limit=limit)
        #     if not response or not hasattr(response, "response"):
        #         break
        #     devices_response.extend(response.response)
        #     if len(response.response) < limit:
        #         break  # Last page
        #     offset += limit
        # all_devices = {
        #     device.serialNumber: device for device in devices_response if hasattr(device, "serialNumber")
        # }
        # logging.info(f"Fetched {len(all_devices)} devices.")

        logging.info("Fetching all sites from Catalyst Center...")
        sites = []
        offset = 1
        limit = 500  

        while True:
            response = client.sites.get_site(offset=offset, limit=limit)
            if not response or not hasattr(response, "response"):
                break
            sites.extend(response.response)
            if len(response.response) < limit:
                break  # Last page
            offset += limit
        logging.info(f"Fetched {len(sites)} sites.")
        
        logging.info("Linking Devices to Sites")
        devices =[]
        site_num = 0
        for site in sites:
            site_num += 1
            logging.info(f"Working on Site #{site_num}: {site.get('siteNameHierarchy')}")
            membership = client.sites.get_membership(site_id=site.id)
            if not membership or not hasattr(membership, 'device'): continue
            if membership.device is None: continue
            for members in membership.device:
                if not members or not hasattr(members, 'response'): continue
                for device in members.response:
                    if hasattr(device, 'serialNumber'):
                        logging.info(f"Found device {device.hostname}")
                        interfaces=[]
                        if int(device.interfaceCount) > 0:
                            try:
                                logging.info(f"Getting all interfaces for device: {device['hostname']}")
                                interface_response = client.devices.get_interface_info_by_id(device['id'])
                                if interface_response and hasattr(interface_response, "response"):
                                    for interface in interface_response.response:
                                        interfaces.append({
                                                "name": interface.portName,
                                                "mac": getattr(interface, "macAddress", None),
                                                "speed": interface.speed,
                                                "duplex": getattr(interface, "duplex", None),
                                                "enabled": interface.status.lower(),
                                                "mtu": interface.mtu,
                                                "description": interface.description,
                                                "ips": [
                                                f"{ip.address.ipAddress.address}/{ip.address.ipMask.addresss}" 
                                                for ip in getattr(interface, "addresses", {})
                                            ] if hasattr(interface, "addresses") else []
                                        })
                            except Exception as e:
                                 logging.error(f"Error fetching interfaces for device {device.hostname}: {e}")
                                 
                        elif 'Unified AP' in device.family:
                            logging.info(f"Getting Device {device.hostname} Access Point Interface info")
                            interfaces.append({
                                    "name": "mgmt0",
                                    "mac": device['macAddress'],
                                    "speed": 1000,
                                    "duplex": "full",
                                    "enabled": "up",
                                    "ips": [f"{device.managementIpAddress}/24"] 
                            })
                            interfaces.append({
                                    "name": "radio0",
                                    "mac": device['apEthernetMacAddress'],
                                    "speed": 1000,
                                    "duplex": "full",
                                    "enabled": "up",
                                    "ips": [],
                            })
                            device.enabled=device.reachabilityStatus.lower()
                        else:
                            logging.info(f"Device {device.name} has no interfaces")
                            
                        device.site = site.name
                        device.interfaces = interfaces
                        devices.append(device)

            logging.info(f"Completed processing site: {site.name}")

        logging.info("Completed fetching device data.")
        return devices

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
