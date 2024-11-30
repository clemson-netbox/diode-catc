import re
import yaml
import logging
import ipaddress

class Transformer:
    def __init__(self, site_rules_path, skip_rules_path):
        """
        Initialize the Transformer with paths to regex rules for site and tenant mappings.
        """
        self.site_rules = self._load_rules(site_rules_path)
        self.skip_device_rules = self._load_rules(skip_rules_path)

    def _load_rules(self, path):
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load rules from {path}: {e}")
            exit(1)
    
    def should_skip_device(self, name):
        for pattern in self.skip_device_rules:
            if re.match(pattern, name, flags=re.IGNORECASE):
                logging.debug(f"Skipping Device: {name} (matched pattern: {pattern})")
                return True
        return False       
    
    def transform_name(self,hostname):
        if not hostname:
            return None
        return hostname.lower().split(".clemson.edu")[0]

    def apply_regex_replacements(self, value, rules):
        try:
            for rule in rules:
                # Validate rule structure
                if len(rule) != 2:
                    logging.error(f"Malformed rule: {rule}")
                    continue

                pattern, replacement = rule
                if re.match(pattern, value, flags=re.IGNORECASE):
                    return re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        except re.error as e:
            # Handle regex errors gracefully
            logging.error(f"Regex error {value} {rule}: {e}")
            return value

        return value

    def regex_replace(self, value, pattern, replacement):
        try:
            return re.sub(pattern, replacement, value)
        except re.error as e:
            # Handle regex errors gracefully
            logging.error(f"Regex error {value} {pattern}: {e}")
            return "Unknown"

    def get_cidr(self, ip, mask):
        try:
            prefix_length = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
            return f"{ip}/{prefix_length}"
        except ValueError:
            logging.error(f"CIDR error {ip} {mask}: {e}")
            return None

    def get_network_addr(self, ip, prefix_or_mask):
        try:
            if "." in ip:  # IPv4
                network = ipaddress.IPv4Network(f"{ip}/{prefix_or_mask}", strict=False)
                return f"{network.network_address}/{network.prefixlen}"
            else:  # IPv6
                prefix_length = int(prefix_or_mask)
                network = ipaddress.IPv6Network(f"{ip}/{prefix_length}", strict=False)
                return f"{network.network_address}/{network.prefixlen}"
        except Exception as e:
            print(f"Error calculating network address: {e}")
            return None

    def site_to_site(self, name):
        """
        Apply site_rules        
        """
        return self.apply_regex_replacements(name, self.site_rules)

    def map_duplex(self,duplex):
        """
        Map Cisco DNAC duplex values to NetBox expected values.
        """
        if isinstance(duplex, str):
            if duplex.lower() in ["full", "half"]:
                return duplex.lower()
        elif isinstance(duplex, bool):
            return "full" if duplex else "half"
        return "auto"  # Default to auto if duplex is missing or unrecognized

    def infer_interface_type(self, port_name, speed):
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
        try:
            # Check if the portName indicates an ethernet interface
            if "E" in port_name:
                # Map speed to physical interface type
                return speed_to_type_map.get(speed)
            elif "channel" in port_name:
                return "lag"
            else:
                return "virtual"
        except Exception as e:
            logging.error(f"Infer interface type error {port_name} {speed}: {e}")
            return None

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


    def extract_site(self,site_hierarchy):
        try:
            match = re.match(r"^(?:[^/]+/){2}([^/]+)", site_hierarchy)
            if match:
                return match.group(1).title()  
            return site_hierarchy 
        except re.error as e:
            # Handle regex errors gracefully
            logging.error(f"Regex error processing site from {site_hierarchy}: {e}")
            return  site_hierarchy

    def extract_location(self,site_hierarchy):
        try:
            match = re.match(r"^(?:[^/]+/){3}([^/]+)", site_hierarchy)
            if match:
                return match.group(1).title()  
            return  site_hierarchy  
        except re.error as e:
            # Handle regex errors gracefully
            logging.error(f"Regex error processing location from {site_hierarchy}: {e}")
            return site_hierarchy


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


    