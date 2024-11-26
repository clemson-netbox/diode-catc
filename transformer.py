import re
import yaml
import logging

class Transformer:

    def transform_name(self,hostname):
        """
        Transforms hostname to name without the domain and converts to lowercase.
        """
        if not hostname:
            return None
        return hostname.lower().split(".clemson.edu")[0]

    # Utility function for regex replacement
    def regex_replace(self, value, pattern, replacement):
        """
        Applies a regex pattern replacement to a given string value.
        """
        import re
        return re.sub(pattern, replacement, value)

    def get_cidr(ip, subnet_mask):
        """
        Convert IP and subnet mask into CIDR notation.
        """
        from ipaddress import ip_network
        try:
            network = ip_network(f"{ip}/{subnet_mask}", strict=False)
            return str(network)
        except ValueError:
            return None

    def map_duplex(duplex):
        """
        Map Cisco DNAC duplex values to NetBox expected values.
        """
        if isinstance(duplex, str):
            if duplex.lower() in ["full", "half"]:
                return duplex.lower()
        elif isinstance(duplex, bool):
            return "full" if duplex else "half"
        return "auto"  # Default to auto if duplex is missing or unrecognized

    def infer_interface_type(port_name, speed):
        """
        Infer interface type based on portName and speed.
        """
        # Mapping of speeds to physical interface types
        speed_to_type_map = {
            100: "100base-t",
            1000: "1000base-t",
            10000: "10gbase-x-sfpp",
            25000: "25gbase-x-sfp28",
            40000: "40gbase-x-qsfpp",
            100000: "100gbase-x-qsfp28",
        }

        # Check if the portName indicates a virtual interface
        if "loopback" in port_name.lower():
            return "loopback"
        elif "vlan" in port_name.lower():
            return "vlan"
        elif "tunnel" in port_name.lower():
            return "tunnel"
        elif "ethernet" in port_name.lower() or "gigabit" in port_name.lower():
            # Map speed to physical interface type
            return speed_to_type_map.get(speed, "ethernet")
        else:
            return "virtual"

    def transform_device_type(self, platform_id):
        """
        Transforms platformId to device type with replacements for Cisco Catalyst models.
        """
        if not platform_id:
            return None
        device_type = platform_id
        replacements = [
            (r"^C", "Catalyst "),
            (r"^WS\-C", "Catalyst "),
            (r"^IE\-", "Catalyst IE"),
            (r"^AIR\-AP", "Catalyst "),
            (r"^AIR\-CAP", "Catalyst "),
            (r"\-K9$", ""),
            (r"^([^\,]+)\,.+", r"\1"),
        ]
        for pattern, replacement in replacements:
            device_type = self.regex_replace(device_type, pattern, replacement)
        return {"model": device_type, "manufacturer": {"name": "Cisco"}}


    def transform_role(self, role):
        """
        Transforms role into title case and looks up the object.
        """
        if not role:
            return None
        return role.title()


    def transform_platform(self, software_type, software_version):
        """
        Combines softwareType and softwareVersion into a single platform string.
        """
        software_type = software_type.upper() if software_type else "IOS"
        return f"{software_type} {software_version}"


    def transform_site(self,site_hierarchy):
        """
        Extracts the site name from the siteNameHierarchy.
        """
        if not site_hierarchy:
            return None
        return self.regex_replace(site_hierarchy, r"^[^/]+/[^/]+/([^/]+)/*.*$", r"\1")


    def transform_location(self,site_hierarchy):
        """
        Extracts the location from the siteNameHierarchy.
        """
        if not site_hierarchy:
            return None
        return self.regex_replace(site_hierarchy, r"^[^/]+/[^/]+/[^/]+/([^/]+)/*.*$", r"\1")


    def transform_status(self,reachability_status):
        """
        Maps reachabilityStatus to device status.
        """
        if not reachability_status:
            return None
        return (
            "active" if "Reachable" in reachability_status else
            "offline" if "Unreachable" in reachability_status else
            None
        )


    