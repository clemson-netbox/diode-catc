import logging
from dnacentersdk import api
from transformer import Transformer

def fetch_device_data(client):
    """
    Fetches data from Catalyst Center including sites and devices with their site associations.
    """
    transformer=Transformer()
    
    try:
        devices = []
        sites = []
        offset = 1
        #limit = 500
        #items = 501
        limit = 5
        items = 5

        # Fetch all sites in Catalyst Center
        #while items > limit:
        while items == limit:
            response = client.sites.get_site(offset=offset, limit=limit)
            sites.extend(response.response if hasattr(response, "response") else [])
            items = len(response.response) if hasattr(response, "response") else 0
            logging.info(f"Found {len(sites)} sites in Catalyst Center.")
            offset += limit

        if not sites:
            raise ValueError("No sites found in Cisco Catalyst Center.")

        # Process each site to fetch associated devices
        items = 0
        devcount = 0    
        for site in sites:
            items += 1
            site_name = site.get("siteNameHierarchy")
            logging.info(f"Processing Site #{items}: {site_name}")

            # Get devices associated with the site
            membership = client.sites.get_membership(site_id=site.id)
            if not membership or not hasattr(membership, "device"):
                continue

            for members in (membership.device or []):
                if not members or not hasattr(members, "response"):
                    continue

                for device in members.response:
                    if hasattr(device, "serialNumber"):
                        device["siteNameHierarchy"] = site_name
                        #logging.info(f"Found device {device.hostname} in site {site_name}")
                        devcount +=1
                        
                        try:
                            interface_response = client.devices.get_interface_info_by_id(device.id).response
                        except Exception as e:
                                interface_response = []
                        interfaces=[]    
                        if interface_response:     
                            print(f"Fetched {len(interface_response)} interfaces for device {device['name']}")
                            for interface in interface_response:
                                ip_addresses = []
                                if hasattr(interface, "ipv4Address"):
                                    for ip_info in interface.ipv4Address:
                                        ip = ip_info.ipAddress
                                        subnet = ip_info.subnetMask
                                        if ip and subnet:
                                            cidr = transformer.get_cidr(ip, subnet)
                                            if cidr:
                                                ip_addresses.append(cidr)
                                    #TODO: IPV6 Addresses
                                    
                                interfaces.append({
                                    "name": interface.portName,
                                    "mac": getattr(interface, "macAddress", None),
                                    "speed": interface.speed,
                                    "duplex": getattr(interface, "duplex", None),
                                    "enabled": interface.status.lower(),
                                    "ips": ip_addresses if ip_addresses else None, 
                                })
                                
                        device['interfaces'] = interfaces
                        devices.append(device)

                        
            logging.info(f"Processed {devcount} Devices...")
            devcount=0    
            
        return devices

    except Exception as e:
        logging.error(f"Error fetching data from Catalyst Center: {e}")
        raise
