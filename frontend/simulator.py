import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk
from backend.network_manager import NetworkManager

class NetworkSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rede")
        self.canvas = tk.Canvas(root, width=800, height=600, bg="#f9f9f9", scrollregion=(0, 0, 1600, 1200))
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.manager = NetworkManager()
        self.selected_device = None
        self.device_size = 60
        self.offset = 20
        self.device_widgets = {}
        self.connection_lines = []

        self.images = {
            "pc": ImageTk.PhotoImage(Image.open("assets/pc.png").resize((60, 60))),
            "roteador": ImageTk.PhotoImage(Image.open("assets/roteador.png").resize((60, 60))),
            "envelope": ImageTk.PhotoImage(Image.open("assets/envelope.png").resize((30, 30))),
        }

        self.drag_data = {"x": 0, "y": 0, "device": None}

        self.add_buttons()

    def add_buttons(self):
        frame = tk.Frame(self.root, bg="#ffffff")
        frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        style = {"bg": "#3498db", "fg": "white", "font": ("Segoe UI", 10, "bold"), "padx": 10, "pady": 5}

        tk.Button(frame, text="➕ Adicionar", command=self.add_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="❌ Remover", command=self.remove_device, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="💾 Salvar Rede", command=self.save_network, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="📂 Carregar Rede", command=self.load_network, **style).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="🗑️ Excluir Rede", command=self.delete_network, **style).pack(side=tk.LEFT, padx=5)

    def ask_device_info(self):
        popup = tk.Toplevel(self.root)
        popup.title("Adicionar Dispositivo")
        popup.geometry("350x270")
        popup.configure(bg="#f0f2f5")
        popup.resizable(False, False)
        popup.grab_set()

        name_var = tk.StringVar()
        ip_var = tk.StringVar()
        type_var = tk.StringVar()
        result = {}

        def confirm():
            if name_var.get() and ip_var.get() and type_var.get():
                result["name"] = name_var.get()
                result["ip"] = ip_var.get()
                result["type"] = type_var.get()
                popup.destroy()
            else:
                messagebox.showwarning("Atenção", "Preencha todos os campos.")

        ttk.Label(popup, text="Nome do dispositivo:", background="#f0f2f5").pack(pady=(20, 5), padx=20, anchor="w")
        ttk.Entry(popup, textvariable=name_var).pack(pady=(0, 15), padx=20, fill='x')

        ttk.Label(popup, text="Endereço IP:", background="#f0f2f5").pack(pady=(0, 5), padx=20, anchor="w")
        ttk.Entry(popup, textvariable=ip_var).pack(pady=(0, 15), padx=20, fill='x')

        ttk.Label(popup, text="Tipo (PC, Roteador...):", background="#f0f2f5").pack(pady=(0, 5), padx=20, anchor="w")
        ttk.Entry(popup, textvariable=type_var).pack(pady=(0, 20), padx=20, fill='x')

        ttk.Button(popup, text="Adicionar", command=confirm).pack(pady=(0, 10))

        popup.wait_window()
        return result if result else None

    def add_device(self):
        data = self.ask_device_info()
        if data:
            x = self.offset + len(self.manager.devices) * (self.device_size + 20)
            y = 100
            device = self.manager.add_device(data["name"], data["ip"], data["type"], x, y)
            self.draw_device(device)

    def remove_device(self):
        name = simpledialog.askstring("Remover", "Nome do dispositivo a remover:")
        if name:
            self.manager.remove_device(name)
            self.redraw()

    def draw_device(self, device):
        device_type = device.device_type.lower()
        tag = f"device_{device.name}"
        image = self.images.get(device_type)
        img_id = self.canvas.create_image(device.x, device.y, anchor=tk.NW, image=image, tags=tag)
        text_id = self.canvas.create_text(device.x + self.device_size / 2, device.y + self.device_size + 10,
        text=device.name, font=("Segoe UI", 10, "bold"), tags=tag)

        self.device_widgets[device.name] = (img_id, text_id)

        self.canvas.tag_bind(tag, "<Button-1>", lambda e, d=device: self.select_device(d))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda e, d=device: self.move_device(e, d))
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda e: self.release_device())

    def select_device(self, device):
        if not self.selected_device:
            self.selected_device = device
        else:
            if (self.selected_device.name, device.name) in self.manager.connections or \
                (device.name, self.selected_device.name) in self.manager.connections:
                self.animate_transfer(self.selected_device, device)
            else:
                self.manager.create_connection(self.selected_device.name, device.name)
                self.redraw()
            self.selected_device = None

    def move_device(self, event, device):
        dx = event.x - device.x - self.device_size // 2
        dy = event.y - device.y - self.device_size // 2

        device.x += dx
        device.y += dy

        img_id, text_id = self.device_widgets[device.name]
        self.canvas.coords(img_id, device.x, device.y)
        self.canvas.coords(text_id, device.x + self.device_size / 2, device.y + self.device_size + 10)

        self.update_connections()

    def release_device(self):
        self.drag_data["device"] = None

    def update_connections(self):
        for line in self.connection_lines:
            self.canvas.delete(line)
        self.connection_lines = []

        for name1, name2 in self.manager.connections:
            d1 = next(d for d in self.manager.devices if d.name == name1)
            d2 = next(d for d in self.manager.devices if d.name == name2)

            line = self.canvas.create_line(
                d1.x + self.device_size / 2, d1.y + self.device_size / 2,
                d2.x + self.device_size / 2, d2.y + self.device_size / 2,
                fill="#424242", width=2
            )
            self.connection_lines.append(line)
    def animate_transfer(self, from_device, to_device):
        x1 = from_device.x + self.device_size / 2
        y1 = from_device.y + self.device_size / 2
        x2 = to_device.x + self.device_size / 2
        y2 = to_device.y + self.device_size / 2

        steps = 50
        delay = 15  # milissegundos
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        envelope = self.canvas.create_image(x1, y1, image=self.images["envelope"])

        def move(step=0):
            if step > steps:
                self.canvas.delete(envelope)
                return
            self.canvas.move(envelope, dx, dy)
            self.root.after(delay, lambda: move(step + 1))

        move()


    def redraw(self):
        self.canvas.delete("all")
        self.device_widgets.clear()
        self.connection_lines.clear()

        for device in self.manager.devices:
            self.draw_device(device)
        self.update_connections()

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
            if self.manager.delete_network_file(f"{filename}.json"):
                messagebox.showinfo("Sucesso", f"Rede '{filename}' excluída com sucesso!")
            else:
                messagebox.showerror("Erro", f"Arquivo '{filename}.json' não encontrado.")
