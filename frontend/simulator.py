import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk
import ipaddress
import threading
import time

# --- MODELOS DE DADOS ---

class Device:
    def __init__(self, name, ip_str, device_type, x, y):
        self.name = name
        self.ip = ipaddress.IPv4Address(ip_str)
        self.device_type = device_type  # "pc", "roteador", etc
        self.x = x
        self.y = y
        self.connections = []  # lista de dispositivos conectados diretamente

    def add_connection(self, other_device):
        if other_device not in self.connections:
            self.connections.append(other_device)

    def remove_connection(self, other_device):
        if other_device in self.connections:
            self.connections.remove(other_device)

    def in_same_network(self, other, netmask="255.255.255.0"):
        network1 = ipaddress.IPv4Network(f"{self.ip}/{netmask}", strict=False)
        network2 = ipaddress.IPv4Network(f"{other.ip}/{netmask}", strict=False)
        return network1.network_address == network2.network_address

class Packet:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.path = []
        self.current_index = 0

    def next_hop(self):
        if self.current_index < len(self.path) - 1:
            self.current_index += 1
            return self.path[self.current_index]
        return None

class NetworkManager:
    def __init__(self):
        self.devices = []
        self.connections = []  # tuples (device1_name, device2_name)

    def add_device(self, name, ip, device_type, x, y):
        device_type = device_type.lower()
        if any(d.name == name for d in self.devices):
            raise ValueError("Nome já existe")
        device = Device(name, ip, device_type, x, y)
        self.devices.append(device)
        return device

    def remove_device(self, name):
        device = self.get_device(name)
        if device:
            self.devices.remove(device)
            # Remove conexões relacionadas
            self.connections = [c for c in self.connections if name not in c]
            for d in self.devices:
                d.remove_connection(device)

    def get_device(self, name):
        for d in self.devices:
            if d.name == name:
                return d
        return None

    def create_connection(self, name1, name2):
        if name1 == name2:
            return
        d1 = self.get_device(name1)
        d2 = self.get_device(name2)
        if d1 and d2 and (name1, name2) not in self.connections and (name2, name1) not in self.connections:
            self.connections.append((name1, name2))
            d1.add_connection(d2)
            d2.add_connection(d1)

    def remove_connection(self, name1, name2):
        if (name1, name2) in self.connections:
            self.connections.remove((name1, name2))
        elif (name2, name1) in self.connections:
            self.connections.remove((name2, name1))
        d1 = self.get_device(name1)
        d2 = self.get_device(name2)
        if d1 and d2:
            d1.remove_connection(d2)
            d2.remove_connection(d1)

    def find_path(self, source_name, destination_name):
        # BFS para achar caminho respeitando conexões e roteadores
        source = self.get_device(source_name)
        dest = self.get_device(destination_name)
        if not source or not dest:
            return None

        # Se estiverem na mesma rede, caminho direto
        if source.in_same_network(dest):
            return [source, dest]

        # Se não, deve passar por roteadores
        # BFS para achar caminho no grafo de conexões
        from collections import deque
        queue = deque()
        queue.append([source])
        visited = set()
        visited.add(source)

        while queue:
            path = queue.popleft()
            last = path[-1]
            if last == dest:
                return path
            for neighbor in last.connections:
                if neighbor not in visited:
                    # Só passa por roteadores ou destino final
                    if neighbor.device_type == "roteador" or neighbor == dest:
                        visited.add(neighbor)
                        queue.append(path + [neighbor])
        return None

# --- INTERFACE GRÁFICA ---

class NetworkSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Rede")
        self.manager = NetworkManager()
        self.selected_device = None
        self.device_size = 60
        self.offset = 20
        self.device_widgets = {}
        self.connection_lines = []
        self.animating_packets = False

        self.canvas = tk.Canvas(root, width=900, height=650, bg="#f9f9f9", scrollregion=(0, 0, 1600, 1200))
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.images = {
            "pc": ImageTk.PhotoImage(Image.open("assets/pc.png").resize((60, 60))),
            "roteador": ImageTk.PhotoImage(Image.open("assets/roteador.png").resize((60, 60))),
            "envelope": ImageTk.PhotoImage(Image.open("assets/envelope.png").resize((30, 30))),
        }

        self.drag_data = {"x": 0, "y": 0, "device": None}

        self.add_sidebar()

    def add_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#2c3e50", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        title = tk.Label(sidebar, text="Simulador", bg="#2c3e50", fg="white", font=("Segoe UI", 14, "bold"))
        title.pack(pady=20)

        button_style = {"bg": "#34495e", "fg": "white", "font": ("Segoe UI", 10, "bold"), "relief": tk.FLAT, "width": 20, "height": 2}

        tk.Button(sidebar, text="➕ Adicionar", command=self.add_device, **button_style).pack(pady=5)
        tk.Button(sidebar, text="❌ Remover", command=self.remove_device, **button_style).pack(pady=5)
        tk.Button(sidebar, text="🔗 Conectar", command=self.connect_devices, **button_style).pack(pady=5)
        tk.Button(sidebar, text="🚀 Enviar Pacotes", command=self.ask_send_packets, **button_style).pack(pady=5)
        tk.Button(sidebar, text="💾 Salvar", command=self.save_network, **button_style).pack(pady=5)
        tk.Button(sidebar, text="📂 Carregar", command=self.load_network, **button_style).pack(pady=5)
        tk.Button(sidebar, text="🗑️ Excluir", command=self.delete_network, **button_style).pack(pady=5)

    def ask_device_info(self):
        popup = tk.Toplevel(self.root)
        popup.title("Adicionar Dispositivo")
        popup.geometry("350x250")
        popup.configure(bg="#f0f2f5")
        popup.resizable(False, False)
        popup.grab_set()

        name_var = tk.StringVar()
        ip_var = tk.StringVar()
        type_var = tk.StringVar(value="PC")
        result = {}

        def confirm():
            try:
                ipaddress.IPv4Address(ip_var.get())  # valida IP
            except:
                messagebox.showerror("Erro", "IP inválido!")
                return
            if name_var.get() and ip_var.get() and type_var.get():
                result["name"] = name_var.get()
                result["ip"] = ip_var.get()
                result["type"] = type_var.get().lower()
                popup.destroy()
            else:
                messagebox.showwarning("Atenção", "Preencha todos os campos.")

        ttk.Label(popup, text="Nome do dispositivo:", background="#f0f2f5").pack(pady=(20, 5), padx=20, anchor="w")
        ttk.Entry(popup, textvariable=name_var).pack(pady=(0, 10), padx=20, fill='x')

        ttk.Label(popup, text="Endereço IP:", background="#f0f2f5").pack(pady=(0, 5), padx=20, anchor="w")
        ttk.Entry(popup, textvariable=ip_var).pack(pady=(0, 10), padx=20, fill='x')

        ttk.Label(popup, text="Tipo de dispositivo:", background="#f0f2f5").pack(pady=(0, 5), padx=20, anchor="w")
        type_options = ["PC", "Roteador"]
        ttk.OptionMenu(popup, type_var, type_options[0], *type_options).pack(pady=(0, 20), padx=20, fill='x')

        ttk.Button(popup, text="Adicionar", command=confirm).pack(pady=(0, 10))

        popup.wait_window()
        return result if result else None

    def add_device(self):
        data = self.ask_device_info()
        if data:
            x = self.offset + len(self.manager.devices) * (self.device_size + 20)
            y = 100
            try:
                device = self.manager.add_device(data["name"], data["ip"], data["type"], x, y)
                self.draw_device(device)
            except ValueError as e:
                messagebox.showerror("Erro", str(e))

    def remove_device(self):
        name = simpledialog.askstring("Remover", "Nome do dispositivo a remover:")
        if name:
            self.manager.remove_device(name)
            self.redraw()

    def connect_devices(self):
        # Seleciona dois dispositivos para conectar
        devices_names = [d.name for d in self.manager.devices]
        if len(devices_names) < 2:
            messagebox.showwarning("Aviso", "Adicione pelo menos dois dispositivos para conectar.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Conectar Dispositivos")
        popup.geometry("300x200")
        popup.grab_set()
        popup.resizable(False, False)

        src_var = tk.StringVar(value=devices_names[0])
        dst_var = tk.StringVar(value=devices_names[1])

        ttk.Label(popup, text="Dispositivo 1:").pack(pady=10)
        ttk.OptionMenu(popup, src_var, devices_names[0], *devices_names).pack()

        ttk.Label(popup, text="Dispositivo 2:").pack(pady=10)
        ttk.OptionMenu(popup, dst_var, devices_names[1], *devices_names).pack()

        def confirm():
            src = src_var.get()
            dst = dst_var.get()
            if src != dst:
                self.manager.create_connection(src, dst)
                self.redraw()
            popup.destroy()

        ttk.Button(popup, text="Conectar", command=confirm).pack(pady=20)

        popup.wait_window()

    def ask_send_packets(self):
        devices_names = [d.name for d in self.manager.devices]
        if len(devices_names) < 2:
            messagebox.showwarning("Aviso", "Adicione pelo menos dois dispositivos.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Enviar Pacotes")
        popup.geometry("300x250")
        popup.grab_set()
        popup.resizable(False, False)

        src_var = tk.StringVar(value=devices_names[0])
        dst_var = tk.StringVar(value=devices_names[1])
        qtd_var = tk.IntVar(value=1)

        ttk.Label(popup, text="Origem:").pack(pady=5)
        ttk.OptionMenu(popup, src_var, devices_names[0], *devices_names).pack()

        ttk.Label(popup, text="Destino:").pack(pady=5)
        ttk.OptionMenu(popup, dst_var, devices_names[1], *devices_names).pack()

        ttk.Label(popup, text="Quantidade de pacotes:").pack(pady=5)
        ttk.Entry(popup, textvariable=qtd_var).pack()

        def confirm():
            src = src_var.get()
            dst = dst_var.get()
            qtd = qtd_var.get()
            if src and dst and src != dst and qtd > 0:
                threading.Thread(target=self.send_packets, args=(src, dst, qtd), daemon=True).start()
            popup.destroy()

        ttk.Button(popup, text="Enviar", command=confirm).pack(pady=20)

        popup.wait_window()

    def send_packets(self, src_name, dst_name, qtd):
        for _ in range(qtd):
            path = self.manager.find_path(src_name, dst_name)
            if not path:
                messagebox.showerror("Erro", f"Sem caminho entre {src_name} e {dst_name}")
                return
            self.animate_packet(path)
            time.sleep(0.5)

    def animate_packet(self, path):
        img = self.images["envelope"]
        x, y = path[0].x, path[0].y
        packet_id = self.canvas.create_image(x + self.device_size // 2, y + self.device_size // 2, image=img)
        self.root.update()

        for device in path[1:]:
            dest_x = device.x + self.device_size // 2
            dest_y = device.y + self.device_size // 2
            steps = 20
            for i in range(1, steps + 1):
                new_x = x + (dest_x - x) * i / steps
                new_y = y + (dest_y - y) * i / steps
                self.canvas.coords(packet_id, new_x, new_y)
                self.root.update()
                time.sleep(0.05)
            x, y = dest_x, dest_y

        self.canvas.delete(packet_id)

    def save_network(self):
        messagebox.showinfo("Salvar", "Funcionalidade de salvar ainda não implementada.")

    def load_network(self):
        messagebox.showinfo("Carregar", "Funcionalidade de carregar ainda não implementada.")

    def delete_network(self):
        if messagebox.askyesno("Confirmar", "Deseja apagar toda a rede?"):
            self.manager = NetworkManager()
            self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        for device in self.manager.devices:
            self.draw_device(device)
        for conn in self.manager.connections:
            self.draw_connection(conn[0], conn[1])

    def draw_device(self, device):
        img = self.images.get(device.device_type, self.images["pc"])
        widget = self.canvas.create_image(device.x, device.y, image=img, anchor="nw")
        self.device_widgets[device.name] = widget
        self.canvas.tag_bind(widget, "<ButtonPress-1>", lambda e, dev=device: self.on_device_click(e, dev))
        self.canvas.tag_bind(widget, "<B1-Motion>", lambda e, dev=device: self.on_device_drag(e, dev))
        self.canvas.tag_bind(widget, "<ButtonRelease-1>", lambda e: self.on_device_release(e))

        # Nome do dispositivo
        self.canvas.create_text(device.x + self.device_size // 2, device.y + self.device_size + 10,
                                text=f"{device.name}\n{device.ip}", font=("Segoe UI", 8), fill="black")

    def draw_connection(self, name1, name2):
        d1 = self.manager.get_device(name1)
        d2 = self.manager.get_device(name2)
        if d1 and d2:
            x1 = d1.x + self.device_size // 2
            y1 = d1.y + self.device_size // 2
            x2 = d2.x + self.device_size // 2
            y2 = d2.y + self.device_size // 2
            self.canvas.create_line(x1, y1, x2, y2, fill="#2980b9", width=2)

    def on_device_click(self, event, device):
        self.drag_data["device"] = device
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_device_drag(self, event, device):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        device.x += dx
        device.y += dy
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.redraw()

    def on_device_release(self, event):
        self.drag_data = {"x": 0, "y": 0, "device": None}

# --- MAIN ---

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulatorUI(root)
    root.mainloop()
