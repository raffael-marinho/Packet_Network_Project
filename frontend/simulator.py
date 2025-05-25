import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
from backend.network_manager import NetworkManager

class NetworkSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rede")

        self.canvas = tk.Canvas(root, width=800, height=600, bg="#f9f9f9", scrollregion=(0, 0, 1600, 1200))
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.manager = NetworkManager()
        self.selected_device = None
        self.device_size = 60
        self.offset = 20
        self.drag_data = {"x": 0, "y": 0, "device": None}

        self.images = {
            "pc": ImageTk.PhotoImage(Image.open("assets/pc.png").resize((60, 60))),
            "roteador": ImageTk.PhotoImage(Image.open("assets/roteador.png").resize((60, 60))),
        }

        self.device_widgets = {}  # Mapeia nomes dos dispositivos para (image_id, text_id)

        self.add_buttons()

    def add_buttons(self):
        frame = tk.Frame(self.root, bg="#ffffff")
        frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        style = {"bg": "#4CAF50", "fg": "white", "font": ("Segoe UI", 10, "bold"), "padx": 10, "pady": 5}

        tk.Button(frame, text="Adicionar Dispositivo", command=self.add_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Remover Dispositivo", command=self.remove_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Salvar Rede", command=self.save_network, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Carregar Rede", command=self.load_network, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Excluir Rede", command=self.delete_network, **style).pack(side=tk.LEFT, padx=5)

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
            if self.manager.remove_device(name):
                self.redraw()
            else:
                messagebox.showwarning("Aviso", f"Dispositivo '{name}' não encontrado.")

    def draw_device(self, device):
        image = self.images.get(device.device_type.lower())
        image_id = self.canvas.create_image(device.x, device.y, anchor=tk.NW, image=image, tags=("device", device.name))
        text_id = self.canvas.create_text(device.x + self.device_size / 2, device.y + self.device_size + 10,
                                          text=device.name, font=("Segoe UI", 10, "bold"), tags=("device", device.name))
        self.device_widgets[device.name] = (image_id, text_id)

        # Eventos de clique e arrasto
        self.canvas.tag_bind(image_id, "<Button-1>", lambda e, d=device: self.on_click(d))
        self.canvas.tag_bind(image_id, "<B1-Motion>", lambda e, d=device: self.on_drag(e, d))
        self.canvas.tag_bind(image_id, "<ButtonRelease-1>", lambda e: self.on_release())

    def on_click(self, device):
        if not self.selected_device:
            self.selected_device = device
        else:
            self.manager.create_connection(self.selected_device.name, device.name)
            self.selected_device = None
            self.redraw()

    def on_drag(self, event, device):
        dx = event.x - device.x
        dy = event.y - device.y
        device.x = event.x
        device.y = event.y

        image_id, text_id = self.device_widgets[device.name]
        self.canvas.coords(image_id, device.x, device.y)
        self.canvas.coords(text_id, device.x + self.device_size / 2, device.y + self.device_size + 10)

        self.redraw_connections()

    def on_release(self):
        self.selected_device = None

    def redraw(self):
        self.canvas.delete("all")
        self.device_widgets.clear()
        for device in self.manager.devices:
            self.draw_device(device)
        self.redraw_connections()

    def redraw_connections(self):
        # Remove todas as linhas antigas
        for item in self.canvas.find_all():
            if "line" in self.canvas.gettags(item):
                self.canvas.delete(item)

        # Desenha conexões novamente
        for name1, name2 in self.manager.connections:
            d1 = next(d for d in self.manager.devices if d.name == name1)
            d2 = next(d for d in self.manager.devices if d.name == name2)
            self.canvas.create_line(
                d1.x + self.device_size / 2, d1.y + self.device_size / 2,
                d2.x + self.device_size / 2, d2.y + self.device_size / 2,
                fill="#424242", width=2, tags="line"
            )

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

    def delete_network(self):
        filename = simpledialog.askstring("Excluir", "Nome do arquivo (sem .json):")
        if filename:
            full_path = f"{filename}.json"
            if self.manager.delete_network_file(full_path):
                messagebox.showinfo("Sucesso", f"Arquivo '{full_path}' excluído com sucesso!")
            else:
                messagebox.showerror("Erro", f"O arquivo '{full_path}' não foi encontrado.")
