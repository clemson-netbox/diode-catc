from netboxlabs.diode.sdk.ingester import Device, Interface, IPAddress, Entity
from transformer import Transformer
import logging

def prepare_device_data(devices):
    """
    Transforms Catalyst Center device data into Diode-compatible Device entities.
    """
    transformer = Transformer()
    entities = []

    for device in devices:
        try:
            # Use the Transformer class to handle field transformations
            location = transformer.transform_location(device.get("siteNameHierarchy"))
            if len(location)<1 : location=transformer.transform_site(device.get("siteNameHierarchy"))
            
            device_data = Device(
                name=transformer.transform_name(device.get("hostname")),
                device_type=transformer.transform_device_type(device.get("platformId")),
                manufacturer="Cisco",
                role=transformer.transform_role(device.get("role")),
                platform=transformer.transform_platform(device.get("softwareType"), device.get("softwareVersion")),
                serial=device.get("serialNumber").upper() if device.get("serialNumber") else None,
                site=transformer.transform_site(device.get("siteNameHierarchy")),
                #location=location,
                status=transformer.transform_status(device.get("reachabilityStatus")),
                tags=["Diode-CATC-Agent"],
            )
            entities.append(Entity(device=device_data))
            
            for interface in device.get('interfaces'):
                interface_data = Interface(
                    name=interface.portName,
                    mac=interface.macAddress,
                    type=transformer.infer_interface_type(interface.portName, interface.speed),
                    speed=interface.speed * 1000,
                    duplex=transformer.map_duplex(interface.duplex),
                    enabled=interface.enabled in ["connected", "up"],
                    tags=["Diode-CATC-Agent"],
                )
                entities.append(Entity(interface=interface_data))
                
                for ip in interface.ips:
                    ip_data = IPAddress(
                        adddress=ip,
                        interface=interface_data,
                        description=f"{transformer.transform_name(device.get("hostname"))} {interface.portName}",
                        tags=["Diode-vCenter-Agent"],
                    )
                    entities.append(Entity(ip_address=ip_data))

        except Exception as e:
            logging.error(f"Error transforming device {device.get('hostname', 'unknown')}: {e}")

    return entities
