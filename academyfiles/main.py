import tkinter as tk
from database import create_tables
from migrations import migrar_pago_unico
from app_academia import AppAcademia

if __name__ == "__main__":
    create_tables()
    migrar_pago_unico()

    root = tk.Tk()
    app = AppAcademia(root)
    root.mainloop()
