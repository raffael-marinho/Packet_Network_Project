import tkinter as tk
from simulator import NetworkSimulator

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulator(root)
    root.mainloop()
