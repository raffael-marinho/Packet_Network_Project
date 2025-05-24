import json
import os
from .device import Device

class NetworkManager:
    def __init__(self):
        self.devices = []
        self.connections = []

    def add_device(self, name, ip, device_type, x, y):
        device = Device(name, ip, device_type, x, y)
        self.devices.append(device)
        return device

    def create_connection(self, name1, name2):
        self.connections.append((name1, name2))

    def remove_device(self, name):
        self.devices = [d for d in self.devices if d.name != name]
        self.connections = [(a, b) for a, b in self.connections if name not in (a, b)]
        
    def save_to_file(self, filename):
        data = {
            "devices": [device.__dict__ for device in self.devices],
            "connections": self.connections
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    def load_from_file(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Arquivo {filename} não encontrado.")

        with open(filename, "r") as f:
            data = json.load(f)
            self.devices = [Device(**dev) for dev in data["devices"]]
            self.connections = data["connections"]
    
    def delete_network_file(self, filename):
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False
