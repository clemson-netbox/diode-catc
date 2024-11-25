from netboxlabs.diode.sdk.ingester import Device, Interface, IPAddress, Entity
import logging

def prepare_device_data(catc_devices):
    """
    Transforms CATC device data into Diode-compatible Device entities.
    """
    entities = []
    for device in catc_devices:
        try:
            diode_device = Device(
                name=device["hostname"],
                platform=device["platformId"],
                manufacturer=device["vendor"],
                site=device["location"],
                serial=device["serialNumber"],
                model=device["type"],
                status="active",
                tags=["Diode-CATC-Agent"]
            )
            entities.append(Entity(device=diode_device))
        except KeyError as e:
            logging.error(f"Error transforming device {device['id']}: Missing key {e}")
    return entities

def prepare_interface_data(catc_interfaces):
    """
    Transforms CATC interface data into Diode-compatible Interface entities.
    """
    entities = []
    for interface in catc_interfaces:
        try:
            diode_interface = Interface(
                name=interface["portName"],
                device=interface["deviceId"],
                mac_address=interface["macAddress"],
                enabled=interface["adminStatus"] == "UP",
                tags=["Diode-CATC-Agent"]
            )
            entities.append(Entity(interface=diode_interface))
        except KeyError as e:
            logging.error(f"Error transforming interface {interface['id']}: Missing key {e}")
    return entities
