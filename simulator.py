import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os
from device import Device

class NetworkSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rede")

        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.devices = []
        self.connections = []
        self.selected_device = None

        self.device_size = 60
        self.offset = 20

        self.add_buttons()

    def add_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM)

        tk.Button(button_frame, text="Adicionar Dispositivo", command=self.add_device).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Salvar Rede", command=self.save_network).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Carregar Rede", command=self.load_network).pack(side=tk.LEFT)

    def add_device(self):
        name = simpledialog.askstring("Nome", "Nome do dispositivo:")
        ip = simpledialog.askstring("IP", "Endereço IP do dispositivo:")
        device_type = simpledialog.askstring("Tipo", "Tipo do dispositivo (PC, Roteador, etc.):")

        if name and ip and device_type:
            x = self.offset + len(self.devices) * (self.device_size + 20)
            y = 100
            device = Device(name, ip, device_type, x, y)
            self.devices.append(device)
            self.draw_device(device)

    def draw_device(self, device):
        self.canvas.create_rectangle(
            device.x, device.y,
            device.x + self.device_size, device.y + self.device_size,
            fill="lightblue", tags=device.name
        )
        self.canvas.create_text(
            device.x + self.device_size / 2, device.y + self.device_size / 2,
            text=device.name, tags=device.name
        )
        self.canvas.tag_bind(device.name, "<Button-1>", lambda e, d=device: self.handle_click(d))

    def handle_click(self, device):
        if not self.selected_device:
            self.selected_device = device
        else:
            self.create_connection(self.selected_device, device)
            self.selected_device = None

    def create_connection(self, device1, device2):
        self.canvas.create_line(
            device1.x + self.device_size / 2, device1.y + self.device_size / 2,
            device2.x + self.device_size / 2, device2.y + self.device_size / 2,
            fill="black", width=2
        )
        self.connections.append((device1.name, device2.name))

    def save_network(self):
        filename = simpledialog.askstring("Salvar Rede", "Nome do arquivo (sem extensão):")
        if filename:
            data = {
                "devices": [device.__dict__ for device in self.devices],
                "connections": self.connections
            }
            with open(f"{filename}.json", "w") as f:
                json.dump(data, f)
            messagebox.showinfo("Sucesso", f"Rede salva como {filename}.json")

    def load_network(self):
        filename = simpledialog.askstring("Carregar Rede", "Nome do arquivo (sem extensão):")
        if filename and os.path.exists(f"{filename}.json"):
            with open(f"{filename}.json", "r") as f:
                data = json.load(f)
                self.clear_network()

                for dev_data in data["devices"]:
                    device = Device(**dev_data)
                    self.devices.append(device)
                    self.draw_device(device)

                for d1, d2 in data["connections"]:
                    dev1 = next(d for d in self.devices if d.name == d1)
                    dev2 = next(d for d in self.devices if d.name == d2)
                    self.create_connection(dev1, dev2)

            messagebox.showinfo("Sucesso", f"Rede {filename}.json carregada com sucesso!")
        else:
            messagebox.showerror("Erro", f"Arquivo {filename}.json não encontrado.")

    def clear_network(self):
        self.canvas.delete("all")
        self.devices = []
        self.connections = []
