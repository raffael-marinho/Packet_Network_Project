import tkinter as tk
from frontend.simulator import NetworkSimulatorUI

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulatorUI(root)
    root.mainloop()
