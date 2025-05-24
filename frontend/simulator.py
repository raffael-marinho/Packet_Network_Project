import tkinter as tk
from tkinter import simpledialog, messagebox
from backend.network_manager import NetworkManager

class NetworkSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rede")
        self.canvas = tk.Canvas(root, width=800, height=600, bg="#f9f9f9")
        self.canvas.pack()

        self.manager = NetworkManager()
        self.selected_device = None
        self.device_size = 60
        self.offset = 20

        self.add_buttons()

    def add_buttons(self):
        frame = tk.Frame(self.root, bg="#ffffff")
        frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        style = {"bg": "#4CAF50", "fg": "white", "font": ("Segoe UI", 10, "bold"), "padx": 10, "pady": 5}

        tk.Button(frame, text="Adicionar Dispositivo", command=self.add_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Remover Dispositivo", command=self.remove_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Salvar Rede", command=self.save_network, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Carregar Rede", command=self.load_network, **style).pack(side=tk.LEFT, padx=5)

    def add_device(self):
        name = simpledialog.askstring("Nome", "Nome do dispositivo:")
        ip = simpledialog.askstring("IP", "Endereço IP:")
        dev_type = simpledialog.askstring("Tipo", "Tipo (PC, Roteador...):")

        if name and ip and dev_type:
            x = self.offset + len(self.manager.devices) * (self.device_size + 20)
            y = 100
            device = self.manager.add_device(name, ip, dev_type, x, y)
            self.draw_device(device)
            
    def remove_device(self):
        name = simpledialog.askstring("Remover", "Nome do dispositivo a remover:")
        if name:
            existing = [d for d in self.manager.devices if d.name == name]
            if not existing:
                messagebox.showwarning("Aviso", f"Dispositivo '{name}' não encontrado.")
                return
            self.manager.remove_device(name)
            self.redraw()

    def draw_device(self, device):
        rect = self.canvas.create_rectangle(
            device.x, device.y, device.x + self.device_size, device.y + self.device_size,
            fill="#b3e5fc", outline="#0288d1", width=2, tags=device.name
        )
        text = self.canvas.create_text(
            device.x + self.device_size / 2, device.y + self.device_size / 2,
            text=device.name, font=("Segoe UI", 10, "bold"), tags=device.name
        )
        self.canvas.tag_bind(device.name, "<Button-1>", lambda e: self.handle_click(device))

    def handle_click(self, device):
        if not self.selected_device:
            self.selected_device = device
        else:
            self.manager.create_connection(self.selected_device.name, device.name)
            self.canvas.create_line(
                self.selected_device.x + self.device_size / 2, self.selected_device.y + self.device_size / 2,
                device.x + self.device_size / 2, device.y + self.device_size / 2,
                fill="#424242", width=2
            )
            self.selected_device = None

    def save_network(self):
        filename = simpledialog.askstring("Salvar", "Nome do arquivo (sem .json):")
        if filename:
            self.manager.save_to_file(f"{filename}.json")
            messagebox.showinfo("Sucesso", f"Rede salva como {filename}.json")

    def load_network(self):
        filename = simpledialog.askstring("Carregar", "Nome do arquivo (sem .json):")
        if filename:
            try:
                self.manager.load_from_file(f"{filename}.json")
                self.redraw()
                messagebox.showinfo("Sucesso", "Rede carregada com sucesso!")
            except FileNotFoundError:
                messagebox.showerror("Erro", "Arquivo não encontrado.")

    def redraw(self):
        self.canvas.delete("all")
        for device in self.manager.devices:
            self.draw_device(device)
        for name1, name2 in self.manager.connections:
            d1 = next(d for d in self.manager.devices if d.name == name1)
            d2 = next(d for d in self.manager.devices if d.name == name2)
            self.canvas.create_line(
                d1.x + self.device_size / 2, d1.y + self.device_size / 2,
                d2.x + self.device_size / 2, d2.y + self.device_size / 2,
                fill="#424242", width=2
            )
