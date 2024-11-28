from netboxlabs.diode.sdk.ingester import Device, Interface, IPAddress, Prefix, Entity
from transformer import Transformer


def prepare_data(client,devices,logging):
    
    transformer = Transformer("includes/site_rules.yml","includes/skip_device_rules.yml")
    entities = []

    
    #{'instanceUuid': '3dbe852a-1354-4d54-a77b-3219e995364b', 'instanceTenantId': '5f203c960f1a1c00c6926d61', 'deployPending': 'NONE', 'instanceVersion': 2, 
    # 'apEthernetMacAddress': '38:90:a5:f9:3d:cc', 'apManagerInterfaceIp': '172.19.3.84', 'associatedWlcIp': '172.19.3.84', 'collectionInterval': 'NA', 
    # 'collectionStatus': 'Managed', 'collectionTier': '', 'deviceSupportLevel': 'Supported', 'dnsResolvedManagementAddress': '', 'errorCode': 'null', 
    # 'family': 'Unified AP', 'hostname': 'o-edisto-towere-ap2702e-115', 'interfaceCount': '0', 'inventoryStatusDetail': 'NA', 'lastDeviceResyncStartTime': '', 
    # 'lastManagedResyncReasons': '', 'lastUpdateTime': 1732635607009, 'lastUpdated': '2024-11-26 15:40:07', 'lineCardCount': '0', 'lineCardId': '', 
    # 'macAddress': '70:7d:b9:33:47:c0', 'managedAtleastOnce': False, 'managementIpAddress': '10.120.53.115', 'managementState': 'Managed', 'memorySize': 'NA', 
    # 'paddedMgmtIpAddress': ' 10.120. 53.115', 'pendingSyncRequestsCount': '0', 'platformId': 'AIR-CAP2702E-B-K9', 'reachabilityFailureReason': 'NA', 
    # 'reachabilityStatus': 'Reachable', 'reasonsForDeviceResync': '', 'reasonsForPendingSyncRequests': '', 'role': 'ACCESS', 'roleSource': 'AUTO', 
    # 'serialNumber': 'FJC2139M0TN', 'series': 'Cisco 2700E Series Unified Access Points', 'snmpContact': '', 'snmpLocation': 'Edisto Tower E', 
    # 'softwareVersion': '8.5.182.105', 'syncRequestedByApp': '', 'tagCount': '0', 'tunnelUdpPort': '16666', 'type': 'Cisco 2700E Unified Access Point', 
    # 'upTime': '56 days, 13:35:07.570', 'uptimeSeconds': 4927533, 'vendor': 'NA'}  

    for device in devices:
        
        try:
            # location = transformer.extract_location(device_data.get("site"))
            # if len(location) < 1:
            #     location = transformer.site_to_site(transformer.extract_site(device_data.get("site")))
            # if device.get("snmpLocation"):
            #     location = device["snmpLocation"]
        
                
            #TODO: Handle stackwise when multi serial#s
            site_name = transformer.site_to_site(transformer.extract_site(device.get("site")))
            device_name=transformer.transform_name(device.get("hostname")),

            device_entity = Device(
                name=device_name,
                device_type=transformer.transform_device_type(device.get("platformId")),
                manufacturer="Cisco",
                role=f"{device.get('family')} - {transformer.transform_role(device.get('role'))}",
                platform=transformer.transform_platform(
                    device.get("softwareType") if device.get("softwareType") else "IOS", device.get("softwareVersion")
                ),
                serial=device.get("serialNumber").upper() if device.get("serialNumber") else None,
                site=site_name,
                # location=location,  
                # TODO: Uncomment when Diode adds location to device
                status=transformer.transform_status(device.get("reachabilityStatus")),
                tags=["Diode-CATC-Agent","Diode"],
            )
            entities.append(Entity(device=device_entity))
            logging.info(f"Processed device: {device.hostname}")

            #TODO: Create Location, Rack, and assign device to rack when diode supports

            logging.info(f"Processing interfaces and IPs for device: {device.hostname}")

            # Process interfaces for the device
            if 'Unified AP' in device.family:
                interface_entity = Interface(
                        name='mgmt0',
                        mac_address=device.get("macAddress"),
                        device=device_entity, 
                        description=f"{device_name}: Management Interface",
                        type="1000base-t",
                        speed=1000000, 
                        enabled=True,
                        mgmt_only=True,
                        tags=["Diode-CATC-Agent","Diode"],
                    )
                entities.append(Entity(interface=interface_entity))
                ip_entity = IPAddress(
                    address=device['managementIpAddress'],
                    interface=interface_entity,
                    description=f"{device_name}: mgmt0",
                    tags=["Diode-CATC-Agent","Diode"],
                )
                entities.append(Entity(ip_address=ip_entity))
                logging.debug(f"Processed AP interface: mgmt0 / IP: {device['managementIpAddress']}")

                interface_entity = Interface(
                        name='radio0',
                        device=device_entity, 
                        mac_address=device.get("apEthernetMacAddress"),
                        description=f"{device_name} Radio Interface",
                        type='other-wireless',
                        enabled=True,
                        tags=["Diode-CATC-Agent","Diode"],
                    )
                entities.append(Entity(interface=interface_entity))
                logging.debug(f"Processed AP interface: radio0")
            
            else:
                    
                for interface in device.get("interfaces", []):
                    try:
                        interface_entity = Interface(
                            name=interface.get("portName"),
                            mac_address=interface.get("macAddress"),
                            description=f"{device_name}: {interface.get('portName')} ({interface.get('description')})",
                            type=transformer.infer_interface_type(
                                interface.get("portName"), interface.get("speed")
                            ),
                            speed=int(interface.get("speed", 0)),
                            enabled=True if 'status' in interface and interface.get("status") in ["connected", "up", "reachable"] else False,
                            mtu=int(interface.get("mtu")),
                            tags=["Diode-CATC-Agent","Diode"],
                        )
                        entities.append(Entity(interface=interface_entity))
                        #TODO: assign LAG members if port-channel
                        
                        logging.debug(f"Processed interface: {interface.get('portName')}")


                        try:
                            if interface.get('ipv4Address'):
                                ip_data = IPAddress(
                                    address=transformer.get_cidr(interface.get('ipv4Address'),interface.get('ipv4Mask')),
                                    interface=interface_entity,
                                    description=f"{device_name}: {interface.get('portName')} ({interface.get('description')})",
                                    tags=["Diode-CATC-Agent","Diode"],
                                )
                                if 'Vlan' in interface.get('portName'):
                                    prefix_entity = Prefix(
                                        prefix=transformer.get_network_addr(interface.get('ipv4Address'),interface.get('ipv4Mask')),
                                        site = device_entity.site,
                                        description = f"{interface_entity.name}: {site_name} {interface_entity.description}",
                                        status='active',
                                        tags=["Diode-CATC-Agent","Diode"],

                                    )
                                    entities.append(Entity(prefix=prefix_entity))

                                entities.append(Entity(ip_address=ip_data))
                                logging.debug(f"Processed {interface_entity.name} IP: {ip_data.address}")
                                
                                #TODO: Create Prefix if VLAN interface
                                #TODO: Create VLAN when Diode Updated
                        except Exception as ip_error:
                            logging.error(f"Error processing IP {ip_data}: {ip_error}")

                    except Exception as interface_error:
                        logging.error(
                            f"Error processing interface {interface.get('portName', 'unknown')}: {interface_error}"
                        )
            # Ingest data into Diode
            logging.info(f"Ingesting device {device.hostname} data into Diode...")
            response = client.ingest(entities=entities)# + interface_entities)
            if response.errors:
                logging.error(f"Errors during ingestion: {response.errors}")
            else:
                logging.info("Data ingested successfully into Diode.")
            entities = []
                
        except Exception as device_error:
            logging.error(
                f"Error processing device {device.get('hostname', 'unknown')}: {device_error}"
            )

    return entities