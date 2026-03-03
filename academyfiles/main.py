import tkinter as tk
from database import create_tables
from migrations import migrar_pago_unico, migrar_nota_fk_correcta
from app_academia import AppAcademia

if __name__ == "__main__":
    create_tables()
    migrar_pago_unico()
    migrar_nota_fk_correcta()

    root = tk.Tk()
    app = AppAcademia(root)
    root.mainloop()

