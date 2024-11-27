from netboxlabs.diode.sdk.ingester import Device, Interface, IPAddress, Entity
from transformer import Transformer
import logging


def prepare_data(merged_data):
    
    transformer = Transformer()
    entities = []

    for site in merged_data:
        site_name = site["name"]
        logging.info(f"Processing site: {site_name}")

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


        for device_data in site["devices"]:
            try:
                # Transform device fields
                device=device_data.details
                location = transformer.transform_location(device_data.get("site"))
                if len(location) < 1:
                    location = transformer.transform_location(device_data.get("site"))
                if device.get("snmpLocation"):
                    location = device["snmpLocation"]

                #TODO: Handle stackwise
                device_entity = Device(
                    name=transformer.transform_name(device.get("hostname")),
                    device_type=transformer.transform_device_type(device.get("platformId")),
                    manufacturer="Cisco",
                    role=f"{device.get('family')} - {transformer.transform_role(device.get('role'))}",
                    platform=transformer.transform_platform(
                        device.get("softwareType") if device.get("softwareType") else "IOS", device.get("softwareVersion")
                    ),
                    serial=device.get("serialNumber").upper() if device.get("serialNumber") else None,
                    site=site_name,
                    # location=location,  # TODO: Uncomment when Diode adds location to device
                    status=transformer.transform_status(device.get("reachabilityStatus")),
                    tags=["Diode-CATC-Agent"],
                )
                entities.append(Entity(device=device_entity))
                logging.info(f"Processed device: {device.hostname}")

                # Process interfaces for the device
                if 'Unified AP' in device.family:
                    interface_entity = Interface(
                            name='mgmt0',
                            mac_address=device.get("macAddress"),
                            device=device, 
                            description="AP Mgmt Interface",
                            type="1000base-t",
                            speed=1000000, 
                            duplex='full',
                            enabled=True,
                            tags=["Diode-CATC-Agent"],
                        )
                    entities.append(Entity(interface=interface_entity))
                    ip_entity = IPAddress(
                        address=device['managementIpAddress'],
                        interface=interface_entity,
                        description=f"{device_data.name} mgmt0",
                        tags=["Diode-CATC-Agent"],
                    )
                    entities.append(Entity(ip_address=ip_entity))
                    logging.info(f"Processed interface: mgmt0")

                    interface_entity = Interface(
                            name='radio0',
                            device=device, 
                            mac_address=device.get("apEthernetMacAddress"),
                            description="AP Radio",
                            type='wireless',
                            enabled=True,
                            tags=["Diode-CATC-Agent"],
                        )
                    entities.append(Entity(interface=interface_entity))
                    logging.info(f"Processed interface: ap0")
                    
                for interface in device_data.get("interfaces", []):
                    try:
                        interface_entity = Interface(
                            name=interface.get("name"),
                            ma_address=interface.get("macAddress"),
                            description=interface.get("description"),
                            type=transformer.infer_interface_type(
                                interface.get("name"), interface.get("speed")
                            ),
                            speed=interface.get("speed", 0) * 1000,  # Convert Mbps to Kbps
                            duplex=transformer.map_duplex(interface.get("duplex")),
                            enabled=interface.get("status", "").lower()
                            in ["connected", "up", "reachable"],
                            mtu=interface.get("mtu"),
                            tags=["Diode-CATC-Agent"],
                        )
                        entities.append(Entity(interface=interface_entity))
                        logging.info(f"Processed interface: {interface_entity.name}")

                        # Process IPs for the interface
                        for ip in interface.get("ips", []):
                            try:
                                ip_data = IPAddress(
                                    address=ip,
                                    interface=interface_data,
                                    description=f"{device_data.name} {interface.get('name')} {interface.get('description')}",
                                    tags=["Diode-CATC-Agent"],
                                )
                                entities.append(Entity(ip_address=ip_data))
                                logging.info(f"Processed IP: {ip}")
                            except Exception as ip_error:
                                logging.error(f"Error processing IP {ip}: {ip_error}")

                    except Exception as interface_error:
                        logging.error(
                            f"Error processing interface {interface.get('name', 'unknown')}: {interface_error}"
                        )

            except Exception as device_error:
                logging.error(
                    f"Error processing device {device.get('hostname', 'unknown')}: {device_error}"
                )

    logging.info(f"Completed transformation for devices in {len(merged_data)} sites.")
    return entities
