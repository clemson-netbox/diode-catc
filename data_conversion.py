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
            # Transform device fields
            location = transformer.transform_location(device.get("siteNameHierarchy"))
            if len(location) < 1:
                location = transformer.transform_site(device.get("siteNameHierarchy"))

            device_data = Device(
                name=transformer.transform_name(device.get("hostname")),
                device_type=transformer.transform_device_type(device.get("platformId")),
                manufacturer="Cisco",
                role=transformer.transform_role(device.get("role")),
                platform=transformer.transform_platform(
                    device.get("softwareType"), device.get("softwareVersion")
                ),
                serial=device.get("serialNumber").upper() if device.get("serialNumber") else None,
                site=transformer.transform_site(device.get("siteNameHierarchy")),
                status=transformer.transform_status(device.get("reachabilityStatus")),
                tags=["Diode-CATC-Agent"],
            )
            entities.append(Entity(device=device_data))
            logging.info(f"Processed device: {device_data.name}")

            # Process interfaces for the device
            for interface in device.get("interfaces", []):
                try:

                    interface_data = Interface(
                        name=interface.get("portName"),
                        mac=interface.get("macAddress"),
                        description=interface.description,
                        type=transformer.infer_interface_type(
                            interface.get("portName"), interface.get("speed")
                        ),
                        speed=interface.get("speed", 0) * 1000,  # Convert Mbps to Kbps
                        duplex=transformer.map_duplex(interface.get("duplex")),
                        enabled=interface.get("status", "").lower() in ["connected", "up"],
                        mtu=interface.mtu if interface.mtu else None,
                        tags=["Diode-CATC-Agent"],
                    )
                    entities.append(Entity(interface=interface_data))
                    logging.info(f"Processed interface: {interface_data.name}")

                    # Process IPs for the interface
                    for ip in interface.get("ips", []):
                        try:
                            ip_data = IPAddress(
                                address=ip,
                                interface=interface_data,
                                description=f"{transformer.transform_name(device.get('hostname'))} {interface.get('portName')} {interface.description}",
                                tags=["Diode-CATC-Agent"],
                            )
                            entities.append(Entity(ip_address=ip_data))
                            logging.info(f"Processed IP: {ip}")
                            
                        except Exception as ip_error:
                            logging.error(f"Error processing IP {ip}: {ip_error}")

                except Exception as interface_error:
                    logging.error(
                        f"Error processing interface {interface.get('portName', 'unknown')}: {interface_error}"
                    )

        except Exception as device_error:
            logging.error(
                f"Error processing device {device.get('hostname', 'unknown')}: {device_error}"
            )

    logging.info(f"Completed transformation for {len(devices)} devices.")
    return entities
