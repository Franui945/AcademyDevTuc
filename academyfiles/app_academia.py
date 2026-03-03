import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Optional

from database import get_connection, create_tables
from models import Telefono, Usuario, Alumno, Docente, Administrador, Inscripcion, Examen, Nota


from services import (
    # seguridad / auth
    password_strength,
    hash_password,
    verificar_login,

    # usuarios / roles
    crear_usuario,
    crear_rol_alumno,
    crear_rol_docente,
    crear_rol_admin,

    # cursos
    listar_cursos_admin,
    crear_curso_service,
    editar_curso_service,
    cerrar_curso_service,
    listar_cursos_abiertos,

    # inscripciones
    inscribir_alumno,
    listar_inscripciones_alumno,
    listar_inscripciones_admin,
    cambiar_estado_inscripcion_admin,
    cancelar_inscripcion_alumno,
    listar_alumnos,

    # pagos
    guardar_o_actualizar_pago,
    obtener_id_inscripcion_por_pago,
    listar_pagos_admin,
    obtener_pago_admin_detalle,
    eliminar_pago_admin,
    listar_pagos_por_alumno,

    # teléfonos
    agregar_telefono,
    listar_telefonos_por_usuario,
    eliminar_telefono,

    #exámenes
    crear_examen_service,
    listar_notas_por_alumno,
    listar_inscriptos_por_curso,
    guardar_nota_service,
    listar_examenes_por_curso,
    registrar_nota,
    debug_listar_examenes



)




# =========================
#   APP PRINCIPAL
# =========================
class AppAcademia:
    def __init__(self, root: tk.Tk, usuario_actual=None):
        self.root = root
        self.usuario_actual = usuario_actual   # None al inicio (sin sesión)
        self.root.title("Academy DevTuc")
        self.root.geometry("900x550")
        self.root.minsize(800, 500)

        # ==== BD ====
        create_tables()

        # ==== ESTILO GENERAL ====
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Fondo general
        self.root.configure(bg="#1E1E2E")  # gris/violeta oscuro

        # Frame tipo "card"
        style.configure(
            "Card.TFrame",
            background="#24273A",
            relief="flat",
        )

        # Labels de título
        style.configure(
            "Title.TLabel",
            background="#1E1E2E",
            foreground="#F5E0DC",
            font=("Segoe UI", 22, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background="#1E1E2E",
            foreground="#BAC2DE",
            font=("Segoe UI", 12)
        )

        # Labels de formulario
        style.configure(
            "FormLabel.TLabel",
            background="#24273A",
            foreground="#CDD6F4",
            font=("Segoe UI", 10)
        )

        # Entradas
        style.configure(
            "TEntry",
            fieldbackground="#1E1E2E",
            background="#1E1E2E",
            foreground="#FFFFFF",
            bordercolor="#45475A",
            lightcolor="#89B4FA",
            darkcolor="#11111B",
            padding=4,
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground="#1E1E2E",
            background="#1E1E2E",
            foreground="#FFFFFF",
            arrowcolor="#89B4FA",
        )

        # Botón principal
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            foreground="#FFFFFF",
            background="#89B4FA",
            padding=(10, 6),
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#74C7EC")],
        )

        # Botón secundario
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            foreground="#CDD6F4",
            background="#313244",
            padding=(8, 4),
            borderwidth=0,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#45475A")],
        )

        # ==== CONTENEDOR CENTRAL TIPO CARD ====
        wrapper = ttk.Frame(self.root, style="Card.TFrame", padding=20)
        wrapper.pack(fill="both", expand=True, padx=40, pady=40)

        self.contenedor = wrapper
        self.entradas = {}

        # entradas de login (las defino acá para usarlas en _do_login)
        self.login_user_entry = None
        self.login_pass_entry = None

        self._crear_menu()
        self._mostrar_home()

    def _es_admin(self) -> bool:
        return bool(self.usuario_actual and self.usuario_actual.get("rol") == "ADMIN")
    
    def _es_docente(self) -> bool:
        return bool(self.usuario_actual and self.usuario_actual.get("rol") == "DOCENTE")
    
    

    # ---------- MENÚ CON CASCADE ----------
    def _crear_menu(self):
        menu_principal = tk.Menu(self.root)
        self.root.config(menu=menu_principal)

        # 👇 Detectar rol actual (si hay sesión)
        rol = None
        if self.usuario_actual:
            rol = self.usuario_actual.get("rol", None)

        # ===== MENÚ ARCHIVO =====
        menu_archivo = tk.Menu(menu_principal, tearoff=False)
        menu_archivo.add_command(label="Inicio", command=self._mostrar_home)
        if self.usuario_actual:
            menu_archivo.add_separator()
            menu_archivo.add_command(label="Cerrar sesión", command=self._do_logout)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.root.destroy)
        menu_principal.add_cascade(label="Archivo", menu=menu_archivo)

        # ===== MENÚ USUARIOS =====
        menu_usuarios = tk.Menu(menu_principal, tearoff=False)

        if self.usuario_actual:
            menu_usuarios.add_command(label="Mi perfil", command=self._mostrar_perfil_usuario)
        else:
            menu_usuarios.add_command(label="(Iniciá sesión para ver el perfil)", state="disabled")

        # Solo ADMIN puede gestionar / crear usuarios
        if rol == "ADMIN":
            menu_usuarios.add_separator()
            menu_usuarios.add_command(label="Gestionar Usuarios", command=self._no_implementado)
            menu_usuarios.add_command(label="Nuevo Usuario", command=self._form_usuario)

        menu_principal.add_cascade(label="Usuarios", menu=menu_usuarios)

        # ===== MENÚ CURSOS =====
        menu_cursos = tk.Menu(menu_principal, tearoff=False)
    

        if rol == "DOCENTE":
            menu_cursos.add_command(
                label="Mis cursos",
                command=self._mis_cursos_docente
            )
          
        elif rol == "ADMIN":
            # Admin: gestionar + crear
            menu_cursos.add_command(label="Gestionar Cursos", command=self._gestionar_cursos)
            menu_cursos.add_separator()
            menu_cursos.add_command(label="Nuevo Curso", command=self._form_curso)

        else:
            # Alumno o sin sesión
            menu_cursos.add_command(
                label="(Requiere rol DOCENTE o ADMIN)",
                state="disabled"
            )

        menu_principal.add_cascade(label="Cursos", menu=menu_cursos)

        menu_insc = tk.Menu(menu_principal, tearoff=False)

        if rol == "ADMIN":
            menu_insc.add_command(
                label="Nueva inscripción",
                command=self._form_inscripcion
            )
            menu_insc.add_separator()
            menu_insc.add_command(
                label="Gestionar inscripciones",
                command=self._gestionar_inscripciones_admin
            )


        elif rol == "ALUMNO":
            menu_insc.add_command(
                label="Mis inscripciones",
                command=self._mis_inscripciones
            )

            menu_insc.add_command(
                label="Mis Pagos",
                command=self._mis_pagos
            )

        else:
            menu_insc.add_command(
                label="(Solo Alumno)",
                state="disabled"
            )

        menu_principal.add_cascade(label="Inscripciones", menu=menu_insc)

    # ======== MENU PAGOS =========

        menu_pagos = tk.Menu(menu_principal, tearoff=False)
        if rol == "ADMIN":
            menu_pagos.add_command(
                label="Gestionar Pagos",
                command=self._gestionar_pagos_admin
            )
        
        elif rol == "ALUMNO":
            menu_pagos.add_command(
                label="Mis Pagos",
                command=self._mis_pagos
            )
        else:
            menu_pagos.add_command(
                label="(Requiere Sesión)",
                state="disabled"
            )
        menu_principal.add_cascade(label="Pagos", menu=menu_pagos)

    # ========================= MENU - EXAMENES =========================
        menu_examenes = tk.Menu(menu_principal, tearoff=False)

        if rol == "DOCENTE":
            menu_examenes.add_command(label="Crear examen", command=self._form_examen_docente)
            menu_examenes.add_command(label="Cargar notas", command=self._cargar_notas_docente)
        elif rol == "ALUMNO":
            menu_examenes.add_command(label="Mis notas", command=self._mis_notas_alumno)
        else:
            menu_examenes.add_command(label="(Requiere sesión)", state="disabled")

        menu_principal.add_cascade(label="Exámenes", menu=menu_examenes)

    def _gestionar_inscripciones_admin(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede gestionar inscripciones.")
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Gestión de inscripciones",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        # ✅ OJO: estas columnas definen el ORDEN del values=(...)
        columnas = (
            "ID", "Alumno", "Curso", "Fecha inscripción",
            "Estado insc", "Costo", "Estado pago", "Método pago", "Fecha pago"
        )

        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        for col in columnas:
            tree.heading(col, text=col)

        tree.column("ID", width=60, anchor="center")
        tree.column("Alumno", width=180)
        tree.column("Curso", width=170)
        tree.column("Fecha inscripción", width=110, anchor="center")
        tree.column("Estado insc", width=110, anchor="center")
        tree.column("Costo", width=80, anchor="e")
        tree.column("Estado pago", width=110, anchor="center")
        tree.column("Método pago", width=110, anchor="center")
        tree.column("Fecha pago", width=110, anchor="center")

        tree.pack(side="left", fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        # ✅ guardamos el tree para cargarlo
        self.tree_insc_admin = tree

        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        ttk.Button(
            frame_botones,
            text="Ver detalle",
            style="Secondary.TButton",
            command=self._ver_detalle_inscripcion_admin
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Cambiar estado",
            style="Secondary.TButton",
            command=self._cambiar_estado_inscripcion_admin
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_inscripciones_en_tree
        ).pack(side="left", padx=5)

        # cargar por primera vez

       

    

    





    def _form_inscripcion(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede inscribir alumnos.")
            return

        win = tk.Toplevel(self.root)
        win.title("Nueva Inscripción")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)

        # --- datos ---
        alumnos = listar_alumnos()
        cursos = listar_cursos_abiertos()

        # mapeos: "Texto visible" -> id
        map_alumno = {a["alumno"]: a["id"] for a in alumnos}
        map_curso = {c["nombre"]: c["id"] for c in cursos}

        ttk.Label(frm, text="Alumno:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        cb_alumno = ttk.Combobox(frm, state="readonly", values=list(map_alumno.keys()), width=40)
        cb_alumno.grid(row=0, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frm, text="Curso (ABIERTO):").grid(row=1, column=0, sticky="w", pady=(0, 6))
        cb_curso = ttk.Combobox(frm, state="readonly", values=list(map_curso.keys()), width=40)
        cb_curso.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frm, text="Costo:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        var_costo = tk.StringVar(value="0")
        ent_costo = ttk.Entry(frm, textvariable=var_costo)
        ent_costo.grid(row=2, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frm, text="Fecha inscripción:").grid(row=3, column=0, sticky="w", pady=(0, 6))
        var_fecha = tk.StringVar(value=str(date.today()))
        ent_fecha = ttk.Entry(frm, textvariable=var_fecha)
        ent_fecha.grid(row=3, column=1, sticky="ew", pady=(0, 6))

        frm.columnconfigure(1, weight=1)

        # --- acciones ---
        acciones = ttk.Frame(frm)
        acciones.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def on_guardar():
            self._guardar_inscripcion(
                win=win,
                cb_alumno=cb_alumno,
                cb_curso=cb_curso,
                map_alumno=map_alumno,
                map_curso=map_curso,
                costo_str=var_costo.get(),
                fecha_str=var_fecha.get(),
            )

        ttk.Button(acciones, text="Cancelar", command=win.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(acciones, text="Guardar", command=on_guardar).grid(row=0, column=1)


    def _guardar_inscripcion(
        self,
        win,
        cb_alumno,
        cb_curso,
        map_alumno,
        map_curso,
        costo_str: str,
        fecha_str: str,
    ):
        alumno_txt = (cb_alumno.get() or "").strip()
        curso_txt = (cb_curso.get() or "").strip()

        if not alumno_txt:
            messagebox.showwarning("Atención", "Seleccioná un alumno.")
            return
        if not curso_txt:
            messagebox.showwarning("Atención", "Seleccioná un curso.")
            return

        id_alumno = map_alumno.get(alumno_txt)
        id_curso = map_curso.get(curso_txt)

        if id_alumno is None or id_curso is None:
            messagebox.showwarning("Atención", "Alumno o curso inválido.")
            return

        # costo
        try:
            costo = float(str(costo_str).replace(",", "."))
            if costo < 0:
                raise ValueError
        except Exception:
            messagebox.showwarning("Atención", "El costo debe ser un número válido (>= 0).")
            return

        # fecha (YYYY-MM-DD)
        fecha = (fecha_str or "").strip()
        if not fecha:
            messagebox.showwarning("Atención", "La fecha de inscripción es obligatoria.")
            return

        try:
            date.fromisoformat(fecha)  # valida YYYY-MM-DD
        except Exception:
            messagebox.showwarning("Atención", "La fecha debe estar en formato YYYY-MM-DD.")
            return

        # crear inscripción según tu modelo
        insc = Inscripcion(
            id=None,
            estado="PENDIENTE",
            fecha_inscripcion=fecha,
            costo=costo,
            id_curso=int(id_curso),
            id_alumno=int(id_alumno),
        )

        try:
            inscribir_alumno(insc)

        except ValueError as e:
            # tu service tira ValueError si ya está inscripto
            messagebox.showwarning("Atención", str(e))
            return

        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "unique" in msg:
                messagebox.showwarning("Atención", "El alumno ya está inscripto en este curso.")
            elif "foreign key" in msg:
                messagebox.showwarning("Atención", "Alumno o curso inexistente en la base.")
            else:
                messagebox.showerror("Error", f"No se pudo guardar la inscripción:\n{e}")
            return

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la inscripción:\n{e}")
            return

        messagebox.showinfo("Éxito", "Inscripción creada correctamente.")
        try:
            self._cargar_inscripciones_en_tree()
        except Exception:
            pass

        win.destroy()





    def _mis_inscripciones(self):
        # Solo para alumnos logueados
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            messagebox.showwarning(
                "Permiso denegado",
                "Esta opción solo está disponible para alumnos."
            )
            self._mostrar_home()
            return

        id_alumno = self.usuario_actual.get("id")
        if not id_alumno:
            messagebox.showerror(
                "Error",
                "No se encontró el ID del alumno en la sesión."
            )
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Mis inscripciones",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        # ---- Frame para la tabla ----
        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = (
            "ID", "Curso", "Fecha inscripción", "Estado insc",
            "Costo", "Estado pago", "Método pago", "Fecha pago"
        )

        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        # Configurar columnas
        tree.column("ID", width=50, anchor="center")
        tree.column("Curso", width=180)
        tree.column("Fecha inscripción", width=110, anchor="center")
        tree.column("Estado insc", width=100, anchor="center")
        tree.column("Costo", width=80, anchor="e")
        tree.column("Estado pago", width=100, anchor="center")
        tree.column("Método pago", width=100, anchor="center")
        tree.column("Fecha pago", width=110, anchor="center")

        for col in columnas:
            tree.heading(col, text=col)

        tree.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        # Guardamos el tree para otros métodos (detalle, etc.)
        self.tree_mis_insc = tree

        # ---- Botones inferiores ----
        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        btn_detalle = ttk.Button(
            frame_botones,
            text="Ver detalle",
            style="Secondary.TButton",
            command=self._ver_detalle_mi_inscripcion
        )
        btn_detalle.pack(side="left", padx=5)

        btn_recargar = ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_mis_inscripciones_en_tree
        )
        btn_recargar.pack(side="left", padx=5)

        btn_cancelar = ttk.Button(
            frame_botones,
            text="Cancelar inscripción",
            style="Secondary.TButton",
            command=self._cancelar_mi_inscripcion
        )
        btn_cancelar.pack(side="left", padx=5)

        # Cargamos los datos
        self._cargar_mis_inscripciones_en_tree()

    
    def _cargar_mis_inscripciones_en_tree(self):
        if not hasattr(self, "tree_mis_insc"):
            return

        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            return

        id_alumno = self.usuario_actual.get("id")
        if not id_alumno:
            return

        tree = self.tree_mis_insc
        for item in tree.get_children():
            tree.delete(item)

        try:
            filas = listar_inscripciones_alumno(int(id_alumno))

            for row in filas:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("id", ""),
                        row.get("curso", ""),
                        row.get("fecha_inscripcion", ""),
                        row.get("estado", ""),
                        row.get("costo", ""),
                        row.get("estado_pago") or "",
                        row.get("metodo_pago") or "",
                        row.get("fecha_pago") or "",
                    )
                )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar tus inscripciones:\n{e}")


    def _cargar_mis_pagos_en_tree(self):
        if not hasattr(self, "tree_mis_pagos"):
            return

        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            return

        id_alumno = self.usuario_actual.get("id")
        if not id_alumno:
            return

        tree = self.tree_mis_pagos
        for item in tree.get_children():
            tree.delete(item)

        try:
            filas = listar_pagos_por_alumno(int(id_alumno))

            for row in filas:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("id_pago", ""),
                        row.get("curso", ""),
                        row.get("fecha_inscripcion", ""),
                        row.get("costo", ""),
                        row.get("estado_pago") or "",
                        row.get("metodo_pago") or "",
                        row.get("fecha_pago") or "",
                    )
                )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar tus pagos:\n{e}")




    def _mis_pagos(self):
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            messagebox.showwarning(
                "Permiso denegado",
                "Esta opción solo está disponible para alumnos."
            )
            self._mostrar_home()
            return

        id_alumno = self.usuario_actual.get("id")
        if not id_alumno:
            messagebox.showerror(
                "Error",
                "No se encontró el ID del alumno en la sesión."
            )
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Mis pagos",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        # ---- Frame para la tabla ----
        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = (
            "ID pago", "Curso", "Fecha inscripción",
            "Costo", "Estado pago", "Método pago", "Fecha pago"
        )

        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        tree.column("ID pago", width=70, anchor="center")
        tree.column("Curso", width=200)
        tree.column("Fecha inscripción", width=110, anchor="center")
        tree.column("Costo", width=80, anchor="e")
        tree.column("Estado pago", width=100, anchor="center")
        tree.column("Método pago", width=110, anchor="center")
        tree.column("Fecha pago", width=110, anchor="center")

        for col in columnas:
            tree.heading(col, text=col)

        tree.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        # Guardamos el tree para otros métodos
        self.tree_mis_pagos = tree

        # ---- Botones inferiores ----
        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        btn_detalle = ttk.Button(
            frame_botones,
            text="Ver detalle",
            style="Secondary.TButton",
            command=self._ver_detalle_mi_pago
        )
        btn_detalle.pack(side="left", padx=5)

        btn_recargar = ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_mis_pagos_en_tree
        )
        btn_recargar.pack(side="left", padx=5)

        # Cargamos los datos
        self._cargar_mis_pagos_en_tree()



    def _ver_detalle_mi_pago(self):
        if not hasattr(self, "tree_mis_pagos"):
            return

        seleccion = self.tree_mis_pagos.selection()
        if not seleccion:
            messagebox.showwarning(
                "Atención",
                "Seleccioná un pago para ver el detalle."
            )
            return

        item_id = seleccion[0]
        valores = self.tree_mis_pagos.item(item_id, "values")

        # columnas = (
        #   "ID pago", "Curso", "Fecha inscripción",
        #   "Costo", "Estado pago", "Método pago", "Fecha pago"
        # )
        (
            id_pago,
            curso,
            fecha_insc,
            costo,
            estado_pago,
            metodo_pago,
            fecha_pago
        ) = valores

        detalle = (
            f"ID pago: {id_pago}\n"
            f"Curso: {curso}\n"
            f"Fecha de inscripción: {fecha_insc}\n"
            f"Costo de la inscripción: {costo}\n"
            f"\n"
            f"Estado de pago: {estado_pago or 'SIN REGISTRAR'}\n"
            f"Método de pago: {metodo_pago or '—'}\n"
            f"Fecha de pago: {fecha_pago or '—'}\n"
        )

        messagebox.showinfo("Detalle del pago", detalle)


        # --- BOTÓN GUARDAR ---
    


    def _cancelar_mi_inscripcion(self):
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            messagebox.showwarning(
                "Permiso denegado",
                "Solo los alumnos pueden cancelar sus inscripciones."
            )
            return

        id_insc = self._obtener_id_mi_inscripcion()
        if id_insc is None:
            messagebox.showwarning(
                "Atención",
                "Seleccioná una inscripción para cancelar."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar cancelación",
            "¿Estás seguro de que querés cancelar esta inscripción?\n"
            "Esta acción no se puede deshacer."
        )
        if not confirmar:
            return

        ok = cancelar_inscripcion_alumno(id_inscripcion=id_insc)

        if not ok:
            messagebox.showwarning(
                "No permitido",
                "La inscripción no se pudo cancelar.\n"
                "Solo se pueden cancelar inscripciones en estado PENDIENTE."
            )
            return

        messagebox.showinfo(
            "Éxito",
            "Inscripción cancelada correctamente."
        )
        self._cargar_mis_inscripciones_en_tree()



    def _gestionar_pagos_admin(self):
        if not self._es_admin():
            messagebox.showwarning(
                "Permiso denegado",
                "Solo ADMIN puede gestionar pagos."
            )
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Gestión de pagos",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)
        # Aquí iría la implementación de la tabla y botones para gestionar pagos
        # Similar a la gestión de inscripciones

        columnas = (
            "ID pago", "ID Inscripción", "Alumno", "Curso",
            "Fecha inscripción", "Costo",
            "Estado pago", "Método pago", "Fecha pago", "Monto"
        )


        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        for col in columnas:
            tree.heading(col, text=col)

        tree.column("ID pago", width=70, anchor="center")
        tree.column("ID Inscripción", width=90, anchor="center")
        tree.column("Alumno", width=160)
        tree.column("Curso", width=160)
        tree.column("Fecha inscripción", width=110, anchor="center")
        tree.column("Costo", width=80, anchor="e")
        tree.column("Estado pago", width=100, anchor="center")
        tree.column("Método pago", width=100, anchor="center")
        tree.column("Fecha pago", width=110, anchor="center")

        tree.pack(side="left", fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        self.tree_pagos_admin = tree

        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        ttk.Button(
            frame_botones,
            text="Ver detalle",
            style="Secondary.TButton",
            command=self._ver_detalle_pago_admin
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Registrar/editar pago",
            style="Secondary.TButton",
            command=self._form_registrar_editar_pago_admin
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Eliminar pago",
            style="Secondary.TButton",
            command=self._eliminar_pago_admin
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_pagos_en_tree_admin
        ).pack(side="left", padx=5)

        self._cargar_pagos_en_tree_admin()

    def _cargar_pagos_en_tree_admin(self):
        if not hasattr(self, "tree_pagos_admin"):
            return

        tree = self.tree_pagos_admin
        for fila in tree.get_children():
            tree.delete(fila)

        try:
            filas = listar_pagos_admin()
            for row in filas:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row["id_pago"],
                        row["id_inscripcion"],
                        row["alumno"],
                        row["curso"],
                        row["fecha_inscripcion"],
                        row["costo"],
                        row.get("estado_pago") or "",
                        row.get("metodo_pago") or "",
                        row.get("fecha_pago") or "",
                        row.get("monto") if row.get("monto") is not None else "",
                    )
                )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los pagos:\n{e}")




    def _obtener_id_pago_admin(self):
                if not hasattr(self, "tree_pagos_admin"):
                    return None

                sel = self.tree_pagos_admin.selection()
                if not sel:
                    return None

                valores = self.tree_pagos_admin.item(sel[0], "values")
                try:
                    return int(valores[0])
                except Exception:
                    return None


    def _ver_detalle_pago_admin(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede ver este detalle.")
            return

        id_pago = self._obtener_id_pago_admin()
        if id_pago is None:
            messagebox.showwarning("Atención", "Seleccioná un pago para ver el detalle.")
            return

        row = obtener_pago_admin_detalle(id_pago)
        if not row:
            messagebox.showerror("Error", "No se encontró el pago seleccionado.")
            self._cargar_pagos_en_tree_admin()
            return

        alumno = f"{row.get('nombre_alumno','')} {row.get('apellido_alumno','')}".strip()

        monto = row.get("monto")
        monto_txt = f"${monto:.2f}" if isinstance(monto, (int, float)) else "—"

        detalle = (
            f"ID pago: {row.get('id')}\n"
            f"Alumno: {alumno}\n"
            f"Curso: {row.get('nombre_curso')}\n"
            f"ID inscripción: {row.get('id_inscripcion')}\n"
            f"Fecha inscripción: {row.get('fecha_inscripcion')}\n"
            f"Costo: {row.get('costo')}\n"
            f"\n"
            f"Estado de pago: {row.get('estado_pago') or 'SIN REGISTRAR'}\n"
            f"Método de pago: {row.get('metodo_pago') or '—'}\n"
            f"Fecha de pago: {row.get('fecha_pago') or '—'}\n"
            f"Monto: {monto_txt}\n"
        )

        messagebox.showinfo("Detalle del pago", detalle)



    def _form_registrar_editar_pago_admin(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede registrar pagos.")
            return

        id_pago = self._obtener_id_pago_admin()

        self._limpiar_contenedor()

        titulo = "Registrar pago" if id_pago is None else f"Editar pago (ID {id_pago})"
        ttk.Label(
            self.contenedor,
            text=titulo,
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        fila = 1

        # -------- ID INSCRIPCIÓN --------
        ttk.Label(self.contenedor, text="ID Inscripción:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_id_insc = ttk.Entry(self.contenedor, width=20)
        entry_id_insc.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # -------- ESTADO PAGO --------
        ttk.Label(self.contenedor, text="Estado pago:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_estado = ttk.Combobox(
            self.contenedor,
            values=["PENDIENTE", "PAGADO", "RECHAZADO"],
            state="readonly",
            width=20
        )
        combo_estado.set("PAGADO")
        combo_estado.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # -------- MÉTODO --------
        ttk.Label(self.contenedor, text="Método:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_metodo = ttk.Combobox(
            self.contenedor,
            values=["EFECTIVO", "TRANSFERENCIA", "TARJETA", "OTRO"],
            state="readonly",
            width=20
        )
        combo_metodo.set("TRANSFERENCIA")
        combo_metodo.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # -------- FECHA --------
        ttk.Label(self.contenedor, text="Fecha pago (YYYY-MM-DD):", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_fecha = ttk.Entry(self.contenedor, width=20)
        entry_fecha.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # -------- MONTO --------
        ttk.Label(self.contenedor, text="Monto:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_monto = ttk.Entry(self.contenedor, width=20)
        entry_monto.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # -------- PRECARGA SI EDITA --------
        if id_pago is not None:
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM pago WHERE id = ?", (id_pago,))
                row = cur.fetchone()
                if not row:
                    messagebox.showerror("Error", "El pago ya no existe.")
                    return self._gestionar_pagos_admin()

                entry_id_insc.insert(0, row["id_inscripcion"])
                entry_id_insc.config(state="disabled")
                combo_estado.set(row["estado_pago"] or "PENDIENTE")
                combo_metodo.set(row["metodo_pago"] or "OTRO")
                if row["fecha_pago"]:
                    entry_fecha.insert(0, row["fecha_pago"])
                if row["monto"] is not None:
                    entry_monto.insert(0, str(row["monto"]))
            finally:
                conn.close()

        # ================================
        # FUNCIÓN INTERNA GUARDAR (CORRECTA)
        # ================================
        def guardar(self=self):
            estado = combo_estado.get().strip()
            metodo = combo_metodo.get().strip()
            fecha = entry_fecha.get().strip()
            if not fecha:
                messagebox.showwarning("Atención", "La fecha de pago es obligatoria (YYYY-MM-DD).")
                return
            if len(fecha) != 10 or fecha[4] != "-" or fecha[7] != "-":
                messagebox.showwarning("Atención", "Formato de fecha inválido. Usá YYYY-MM-DD.")
                return
            monto_txt = entry_monto.get().strip()

            if not monto_txt:
                messagebox.showwarning("Atención", "El monto es obligatorio.")
                return

            try:
                monto = float(monto_txt.replace(",", "."))
            except ValueError:
                messagebox.showwarning("Atención", "Monto inválido.")
                return

            if id_pago is None:
                id_insc_txt = entry_id_insc.get().strip()
                if not id_insc_txt.isdigit():
                    messagebox.showwarning("Atención", "ID de inscripción inválido.")
                    return
                id_insc = int(id_insc_txt)
            else:
                id_insc = obtener_id_inscripcion_por_pago(id_pago)
                if id_insc is None:
                    messagebox.showerror("Error", "El pago ya no existe.")
                    return

            ok, error = guardar_o_actualizar_pago(
                id_inscripcion=id_insc,
                estado_pago=estado,
                metodo_pago=metodo,
                fecha_pago=fecha,
                monto=monto,
                id_pago=id_pago
            )

            if not ok:
                messagebox.showerror(
                    "Error",
                    f"No se pudo guardar el pago:\n{error}"
                )
                return

            messagebox.showinfo(
                "Éxito",
                "Pago guardado correctamente."
            )
            self._gestionar_pagos_admin()




        # -------- BOTONES --------
        ttk.Button(
            self.contenedor,
            text="Guardar",
            style="Accent.TButton",
            command=guardar
        ).grid(row=fila, column=0, columnspan=2, pady=(15, 5))

        ttk.Button(
            self.contenedor,
            text="Volver",
            style="Secondary.TButton",
            command=self._gestionar_pagos_admin
        ).grid(row=fila + 1, column=0, columnspan=2, pady=(5, 0))


        


    def _cargar_inscripciones_en_tree(self):
        if not hasattr(self, "tree_insc_admin"):
            return

        tree = self.tree_insc_admin

        for fila in tree.get_children():
            tree.delete(fila)

        try:
            filas = listar_inscripciones_admin()  # -> List[Dict]

            for row in filas:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["alumno"],
                        row["curso"],
                        row["fecha_inscripcion"],
                        row["estado"],                
                        row["costo"],
                        row.get("estado_pago") or "",
                        row.get("metodo_pago") or "",
                        row.get("fecha_pago") or "",
                    )
                )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las inscripciones:\n{e}")



    def _obtener_id_mi_inscripcion(self):
        """Devuelve el ID de la inscripción seleccionada en el tree de 'Mis inscripciones'."""
        if not hasattr(self, "tree_mis_insc"):
            return None

        seleccion = self.tree_mis_insc.selection()
        if not seleccion:
            return None

        item_id = seleccion[0]
        valores = self.tree_mis_insc.item(item_id, "values")
        # La primera columna es el ID de la inscripción
        try:
            return int(valores[0])
        except Exception:
            return None
        
    def _editar_curso_desde_table(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede editar cursos.")
            return

        # Asegura que exista el tree
        if not hasattr(self, "tree_cursos"):
            messagebox.showwarning("Atención", "No hay tabla de cursos cargada.")
            return

        sel = self.tree_cursos.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un curso para editar.")
            return

        valores = self.tree_cursos.item(sel[0], "values")
        try:
            id_curso = int(valores[0])  # la primera columna es el ID
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener el ID del curso.")
            return

        # Llama a tu form existente
        self._form_editar_curso(id_curso)    


    def _obtener_id_inscripcion_admin(self):
        if not hasattr(self, "tree_insc_admin"):
            return None

        seleccion = self.tree_insc_admin.selection()
        if not seleccion:
            return None

        item_id = seleccion[0]
        valores = self.tree_insc_admin.item(item_id, "values")
        try:
            return int(valores[0])
        except Exception:
            return None
        
    def _obtener_id_inscripcion_seleccionada(self, tree_attr: str) -> Optional[int]:
        if not hasattr(self, tree_attr):
            return None
        tree = getattr(self, tree_attr)

        sel = tree.selection()
        if not sel:
            return None

        values = tree.item(sel[0], "values")
        try:
            return int(values[0])
        except Exception:
            return None

    
    def _ver_detalle_inscripcion_admin(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede ver este detalle.")
            return

        id_insc = self._obtener_id_inscripcion_admin()
        if id_insc is None:
            messagebox.showwarning("Atención", "Seleccioná una inscripción para ver el detalle.")
            return

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            sql = """
            SELECT
                i.*,
                u.nombre AS nombre_alumno,
                u.apellido AS apellido_alumno,
                u.email AS email_alumno,
                c.nombre AS nombre_curso,
                c.fecha_inicio AS curso_fecha_inicio,
                c.fecha_fin AS curso_fecha_fin,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago
            FROM inscripcion i
            JOIN usuario u ON u.id = i.id_alumno
            JOIN curso c ON c.id = i.id_curso
            LEFT JOIN pago p ON p.id_inscripcion = i.id
            WHERE i.id = ?;
            """
            cur.execute(sql, (id_insc,))
            row = cur.fetchone()

            if not row:
                messagebox.showerror("Error", "No se encontró la inscripción seleccionada.")
                self._cargar_inscripciones_en_tree()
                return

            alumno = f"{row['nombre_alumno'] or ''} {row['apellido_alumno'] or ''}".strip()

            detalle = (
                f"ID inscripción: {row['id']}\n"
                f"Alumno: {alumno} (ID alumno {row['id_alumno']})\n"
                f"Email alumno: {row['email_alumno'] or ''}\n"
                f"\n"
                f"Curso: {row['nombre_curso']} (ID curso {row['id_curso']})\n"
                f"Fecha inicio curso: {row['curso_fecha_inicio']}\n"
                f"Fecha fin curso: {row['curso_fecha_fin'] or ''}\n"
                f"\n"
                f"Fecha de inscripción: {row['fecha_inscripcion']}\n"
                f"Estado de inscripción: {row['estado']}\n"
                f"Costo: ${row['costo']:.2f}\n"
                f"\n"
                f"Estado de pago: {row['estado_pago'] or 'SIN REGISTRAR'}\n"
                f"Método de pago: {row['metodo_pago'] or ''}\n"
                f"Fecha de pago: {row['fecha_pago'] or ''}\n"
            )

            messagebox.showinfo("Detalle de inscripción", detalle)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el detalle de la inscripción:\n{e}")
        finally:
            conn.close()

        
    def _cambiar_estado_inscripcion_admin(self):
        if not self._es_admin():
            messagebox.showwarning(
                "Permiso denegado",
                "Solo ADMIN puede modificar inscripciones."
            )
            return

        id_insc = self._obtener_id_inscripcion_admin()
        if id_insc is None:
            messagebox.showwarning(
                "Atención",
                "Seleccioná una inscripción."
            )
            return

        # obtenemos el estado actual desde el tree
        seleccion = self.tree_insc_admin.selection()
        valores = self.tree_insc_admin.item(seleccion[0], "values")
        estado_actual = valores[4]  # columna estado

        if estado_actual == "PENDIENTE":
            nuevo_estado = "CONFIRMADA"
        elif estado_actual == "CONFIRMADA":
            nuevo_estado = "CANCELADA"
        else:
            messagebox.showinfo(
                "Info",
                "La inscripción ya está cancelada."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Cambiar estado de {estado_actual} a {nuevo_estado}?"
        )
        if not confirmar:
            return

        ok = cambiar_estado_inscripcion_admin(id_inscripcion=id_insc, nuevo_estado=nuevo_estado)


        if not ok:
            messagebox.showerror(
                "Error",
                "No se pudo actualizar el estado de la inscripción."
            )
            return

        messagebox.showinfo(
            "Éxito",
            f"Estado actualizado a {nuevo_estado}."
        )
        self._cargar_inscripciones_en_tree()


    

    def _ver_detalle_mi_inscripcion(self):
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            messagebox.showwarning("Permiso denegado", "Solo alumnos pueden ver este detalle.")
            return

        insc_id = self._obtener_id_mi_inscripcion()
        if insc_id is None:
            messagebox.showwarning("Atención", "Seleccioná una inscripción para ver el detalle.")
            return

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            sql = """
            SELECT
                i.*,
                c.nombre AS nombre_curso,
                c.fecha_inicio AS curso_fecha_inicio,
                c.fecha_fin AS curso_fecha_fin,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago
            FROM inscripcion i
            JOIN curso c ON c.id = i.id_curso
            LEFT JOIN pago p ON p.id_inscripcion = i.id
            WHERE i.id = ?;
            """
            cur.execute(sql, (insc_id,))
            row = cur.fetchone()

            if not row:
                messagebox.showerror("Error", "No se encontró la inscripción seleccionada.")
                self._cargar_mis_inscripciones_en_tree()
                return

            detalle = (
                f"ID inscripción: {row['id']}\n"
                f"Curso: {row['nombre_curso']} (ID curso {row['id_curso']})\n"
                f"Fecha inicio curso: {row['curso_fecha_inicio']}\n"
                f"Fecha fin curso: {row['curso_fecha_fin'] or ''}\n"
                f"\n"
                f"Fecha de inscripción: {row['fecha_inscripcion']}\n"
                f"Estado de inscripción: {row['estado']}\n"
                f"Costo: ${row['costo']:.2f}\n"
                f"\n"
                f"Estado de pago: {row['estado_pago'] or 'SIN REGISTRAR'}\n"
                f"Método de pago: {row['metodo_pago'] or ''}\n"
                f"Fecha de pago: {row['fecha_pago'] or ''}\n"
            )

            messagebox.showinfo("Detalle de inscripción", detalle)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el detalle de la inscripción:\n{e}")
        finally:
            conn.close()


    def _eliminar_pago_admin(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede eliminar pagos.")
            return

        id_pago = self._obtener_id_pago_admin()
        if id_pago is None:
            messagebox.showwarning("Atención", "Seleccioná un pago para eliminar.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Seguro que querés eliminar este pago?\n"
            "Esta acción no se puede deshacer."
        )
        if not confirmar:
            return

        ok, error = eliminar_pago_admin(id_pago)
        if not ok:
            messagebox.showerror("Error", error or "No se pudo eliminar el pago.")
            return

        messagebox.showinfo("Éxito", "Pago eliminado correctamente.")
        self._cargar_pagos_en_tree_admin()




    def _mis_cursos_docente(self):
        if not self._es_docente():
            messagebox.showwarning(
                "Permiso denegado",
                "Solo los docentes pueden ver esta sección."
            )
            self._mostrar_home()
            return

        id_docente = self.usuario_actual.get("id")
        if not id_docente:
            messagebox.showerror("Error", "No se encontró el ID del docente en la sesión.")
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Mis cursos",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("ID", "Nombre", "Fecha inicio", "Fecha fin", "Estado", "Cupo máximo")

        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre", width=200)
        tree.column("Fecha inicio", width=100, anchor="center")
        tree.column("Fecha fin", width=100, anchor="center")
        tree.column("Estado", width=80, anchor="center")
        tree.column("Cupo máximo", width=100, anchor="center")

        for col in columnas:
            tree.heading(col, text=col)

        tree.pack(side="left", fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        self.tree_cursos_docente = tree

        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        btn_inscriptos = ttk.Button(
            frame_botones,
            text="Ver inscriptos",
            style="Secondary.TButton",
            command=self._ver_inscriptos_de_curso_docente
        )
        btn_inscriptos.pack(side="left", padx=5)

        btn_recargar = ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_cursos_docente_en_tree
        )
        btn_recargar.pack(side="left", padx=5)

        self._cargar_cursos_docente_en_tree()

    def _cargar_cursos_docente_en_tree(self):
        if not hasattr(self, "tree_cursos_docente"):
            return

        tree = self.tree_cursos_docente

        for fila in tree.get_children():
            tree.delete(fila)

        if not self.usuario_actual or self.usuario_actual.get("rol") != "DOCENTE":
            return

        id_docente = self.usuario_actual.get("id")
        if not id_docente:
            return

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    id,
                    nombre,
                    fecha_inicio,
                    fecha_fin,
                    estado,
                    cupo_maximo
                FROM curso
                WHERE id_docente = ?
                ORDER BY fecha_inicio DESC, nombre;
            """
            cur.execute(sql, (id_docente,))

            for row in cur.fetchall():
                tree.insert(
                    "",
                    "end",
                    values=(
                        row["id"],
                        row["nombre"],
                        row["fecha_inicio"],
                        row["fecha_fin"] or "",
                        row["estado"],
                        row["cupo_maximo"],
                    )
                )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar tus cursos:\n{e}")
        finally:
            conn.close()

    def _ver_inscriptos_de_curso_docente(self):
        if not hasattr(self, "tree_cursos_docente"):
            return

        seleccion = self.tree_cursos_docente.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná un curso.")
            return

        item_id = seleccion[0]
        valores = self.tree_cursos_docente.item(item_id, "values")

        try:
            id_curso = int(valores[0])
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener el ID del curso.")
            return

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            sql = """
                SELECT
                    u.nombre,
                    u.apellido,
                    i.fecha_inscripcion,
                    i.estado
                FROM inscripcion i
                JOIN usuario u ON u.id = i.id_alumno
                WHERE i.id_curso = ?
                ORDER BY u.apellido, u.nombre;
            """
            cur.execute(sql, (id_curso,))
            filas = cur.fetchall()

            if not filas:
                messagebox.showinfo(
                    "Inscriptos",
                    "No hay alumnos inscriptos en este curso."
                )
                return

            lineas = []
            for row in filas:
                alumno = f"{row['apellido']}, {row['nombre']}".strip()
                linea = (
                    f"{alumno} - "
                    f"Fecha insc: {row['fecha_inscripcion']} - "
                    f"Estado: {row['estado']}"
                )
                lineas.append(linea)

            texto = "\n".join(lineas)
            messagebox.showinfo("Alumnos inscriptos", texto)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudieron obtener los inscriptos:\n{e}"
            )
        finally:
            conn.close()






    def _gestionar_cursos(self):
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ADMIN":
            messagebox.showwarning(
                "Acceso denegado",
                "Solo los administradores pueden gestionar los cursos."
            )
            self._mostrar_home()
            return

        # Limpiamos el contenedor
        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Gestión de cursos",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        # Frame para Treeview
        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("ID", "Nombre", "Docente", "Fecha Inicio", "Fecha Fin", "Cupo Máximo", "Estado")
        tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        # ✅ HEADINGS (esto te faltaba)
        for col in columnas:
            tree.heading(col, text=col)

        tree.column("ID", width=50, anchor="center")
        tree.column("Nombre", width=160)
        tree.column("Docente", width=180)
        tree.column("Fecha Inicio", width=100, anchor="center")
        tree.column("Fecha Fin", width=100, anchor="center")
        tree.column("Cupo Máximo", width=100, anchor="center")
        tree.column("Estado", width=80, anchor="center")

        tree.pack(side="left", fill="both", expand=True)

        # ✅ doble click: abre detalle del seleccionado
        tree.bind("<Double-1>", lambda e: self._ver_detalle_curso())

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")

        # guardamos el tree
        self.tree_cursos = tree

        # Botones
        frame_botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_botones.pack(fill="x", pady=(10, 0))

        ttk.Button(
            frame_botones,
            text="Ver Detalle",
            style="Secondary.TButton",
            command=self._ver_detalle_curso
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Eliminar Curso",
            style="Secondary.TButton",
            command=self.eliminar_curso
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Recargar",
            style="Secondary.TButton",
            command=self._cargar_cursos_en_tree
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Cerrar Curso",
            style="Secondary.TButton",
            command=self._cerrar_curso
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Editar Curso",
            style="Secondary.TButton",
            command=self._editar_curso_desde_table
        ).pack(side="left", padx=5)

        # cargar datos
        self._cargar_cursos_en_tree()



    def _cargar_cursos_en_tree(self):
        if not hasattr(self, "tree_cursos"):
            return

        tree = self.tree_cursos
        for fila in tree.get_children():
            tree.delete(fila)

        try:
            filas = listar_cursos_admin()  # lista de dicts

            for row in filas:
                docente = row.get("docente") or f'{row.get("nombre_docente","")} {row.get("apellido_docente","")}'.strip()

                tree.insert(
                    "",
                    "end",
                    values=(
                        row.get("id", ""),
                        row.get("nombre", ""),
                        docente,
                        row.get("fecha_inicio") or "",
                        row.get("fecha_fin") or "",
                        row.get("cupo_maximo", ""),
                        row.get("estado", ""),
                    )
                )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los cursos:\n{e}")




    def _obtener_id_curso(self):
        if not hasattr(self, "tree_cursos"):
            return None
        
        seleccion = self.tree_cursos.selection()
        if not seleccion:
            return None
    
        item_id = seleccion[0]
        valores = self.tree_cursos.item(item_id, "values")

        try:
            return int (valores[0])
        except Exception:
            return None
        

        
    def _ver_detalle_curso(self):
        id_curso = self._obtener_id_curso()

        seleccion = self.tree_cursos.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná un curso para ver su detalle.")
            return
    
        if id_curso is None:
            messagebox.showwarning("Atención", "Seleccioná un curso para ver su detalle.")
            return
        
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        try:
            cur = conn.cursor()
            sql = """
            SELECT
                c.*,
                d.nombre AS nombre_docente,
                d.apellido AS apellido_docente,
                a.nombre AS nombre_admin,
                a.apellido AS apellido_admin
            FROM curso c
            LEFT JOIN usuario d ON d.id = c.id_docente
            LEFT JOIN usuario a ON a.id = c.id_administrador
            WHERE c.id = ?;
            """

            cur.execute(sql, (id_curso,))
            row = cur.fetchone()


            if not row:
                messagebox.showerror("Error", "No se encontró el curso seleccionado.")
                self._cargar_cursos_en_tree()
                return
            
            Docente = f'{row["nombre_docente"] or ""} {row["apellido_docente"] or ""}'.strip()
            Administrador = f'{row["nombre_admin"] or ""} {row["apellido_admin"] or ""}'.strip()

            detalle = (f"ID: {row['id']}\n"
                f"Nombre: {row['nombre']}\n"
                f"Descripción: {row['descripcion'] or ''}\n"
                f"Duración (horas): {row['duracion_horas']}\n"
                f"Cupo máximo: {row['cupo_maximo']}\n"
                f"Fecha inicio: {row['fecha_inicio']}\n"
                f"Fecha fin: {row['fecha_fin'] or ''}\n"
                f"Docente: {Docente} (ID {row['id_docente']})\n"
                f"Administrador: {Administrador} (ID {row['id_administrador']})\n"
            )

            messagebox.showinfo("Detalle del curso", detalle)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el detalle del curso:\n{e}")
        finally:
            conn.close()

            
    
    def _cerrar_curso(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede cerrar cursos.")
            return

        if not hasattr(self, "tree_cursos"):
            return

        seleccion = self.tree_cursos.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccioná un curso para cerrar.")
            return

        item_id = seleccion[0]
        valores = self.tree_cursos.item(item_id, "values")

        id_curso = int(valores[0])
        estado_actual = (valores[-1] or "").strip().upper()

        if estado_actual == "CERRADO":
            messagebox.showinfo("Info", "El curso ya está cerrado.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar cierre",
            "¿Estás seguro de que deseas cerrar el curso seleccionado?\n"
            "Esta acción no se puede deshacer."
        )
        if not confirmar:
            return

        ok, error = cerrar_curso_service(id_curso)
        if not ok:
            messagebox.showwarning("Atención", error or "No se pudo cerrar el curso.")
            return

        messagebox.showinfo("Éxito", "Curso cerrado correctamente.")
        self._cargar_cursos_en_tree()






    def eliminar_curso(self):
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede eliminar cursos.")
            return

        if not hasattr(self, "tree_cursos"):
            return

        sel = self.tree_cursos.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un curso para eliminar.")
            return

        valores = self.tree_cursos.item(sel[0], "values")
        try:
            id_curso = int(valores[0])
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener el ID del curso.")
            return

        # ✅ Estado está en la última columna de tu tabla ("Estado")
        estado = (valores[-1] or "").strip().upper()
        if estado != "CERRADO":
            messagebox.showwarning(
                "No permitido",
                "Solo se pueden eliminar cursos en estado CERRADO.\n"
                "Si querés, primero cerralo."
            )
            return

        # ✅ Chequeo extra: no permitir si tiene inscripciones
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT COUNT(*) AS cant FROM inscripcion WHERE id_curso = ?",
                (id_curso,)
            )
            cant = cur.fetchone()["cant"]
        finally:
            conn.close()

        if cant > 0:
            messagebox.showwarning(
                "No permitido",
                f"No se puede eliminar: el curso tiene {cant} inscripción/es vinculada/s.\n"
                "Recomendación: mantenerlo cerrado para conservar el historial."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Eliminar el curso seleccionado?\n"
            "Esta acción no se puede deshacer."
        )
        if not confirmar:
            return

        conn = get_connection()
        try:
            with conn:
                cur = conn.execute("DELETE FROM curso WHERE id = ?", (id_curso,))
                if cur.rowcount == 0:
                    messagebox.showinfo("Info", "No se eliminó ningún curso (quizás ya no existe).")
                else:
                    messagebox.showinfo("Éxito", f"Curso ID {id_curso} eliminado correctamente.")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error",
                "No se pudo eliminar el curso porque tiene registros vinculados."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el curso:\n{e}")
        finally:
            conn.close()

        self._cargar_cursos_en_tree()


    
    def _form_editar_curso(self, id_curso: int):
        self._limpiar_contenedor()

        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM curso WHERE id = ?", (id_curso,))
            row = cur.fetchone()
            if row is None:
                messagebox.showerror("Error", "El curso ya no existe.")
                self._gestionar_cursos()
                return
        finally:
            conn.close()

        docentes, admins = self._get_docentes_y_admins()

        # ✅ Si faltan docentes/admins, no tiene sentido editar
        if not docentes:
            messagebox.showwarning("Atención", "No hay docentes cargados.")
            self._gestionar_cursos()
            return

        if not admins:
            messagebox.showwarning("Atención", "No hay administradores cargados.")
            self._gestionar_cursos()
            return

        ttk.Label(
            self.contenedor,
            text=f"Editar Curso (ID {id_curso})",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        fila = 1

        # --- NOMBRE ---
        ttk.Label(
            self.contenedor,
            text="Nombre del curso:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_nombre = ttk.Entry(self.contenedor, width=40)
        entry_nombre.insert(0, row["nombre"])
        entry_nombre.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DESCRIPCIÓN ---
        ttk.Label(
            self.contenedor,
            text="Descripción:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_descripcion = ttk.Entry(self.contenedor, width=40)
        if row["descripcion"]:
            entry_descripcion.insert(0, row["descripcion"])
        entry_descripcion.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DURACIÓN HORAS ---
        ttk.Label(
            self.contenedor,
            text="Duración (horas):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_duracion = ttk.Entry(self.contenedor, width=15)
        entry_duracion.insert(0, str(row["duracion_horas"]))
        entry_duracion.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- CUPO MÁXIMO ---
        ttk.Label(
            self.contenedor,
            text="Cupo máximo:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_cupo = ttk.Entry(self.contenedor, width=15)
        entry_cupo.insert(0, str(row["cupo_maximo"]))
        entry_cupo.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- FECHA INICIO ---
        ttk.Label(
            self.contenedor,
            text="Fecha inicio (YYYY-MM-DD):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_fecha_inicio = ttk.Entry(self.contenedor, width=20)
        entry_fecha_inicio.insert(0, row["fecha_inicio"])
        entry_fecha_inicio.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- FECHA FIN ---
        ttk.Label(
            self.contenedor,
            text="Fecha fin (YYYY-MM-DD):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        entry_fecha_fin = ttk.Entry(self.contenedor, width=20)
        if row["fecha_fin"]:
            entry_fecha_fin.insert(0, row["fecha_fin"])
        entry_fecha_fin.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DOCENTE ---
        ttk.Label(
            self.contenedor,
            text="Docente:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        valores_docentes = [f"{id_} - {nombre}" for id_, nombre in docentes]
        combo_docente = ttk.Combobox(
            self.contenedor,
            values=valores_docentes,
            state="readonly",
            width=37
        )
        combo_docente.grid(row=fila, column=1, sticky="w", padx=5, pady=4)

        # preseleccionar el docente actual
        docente_actual = row["id_docente"]
        seleccionado = None
        for id_, nombre in docentes:
            if id_ == docente_actual:
                seleccionado = f"{id_} - {nombre}"
                break
        combo_docente.set(seleccionado if seleccionado else valores_docentes[0])
        fila += 1

        # --- ADMIN ---
        ttk.Label(
            self.contenedor,
            text="Administrador:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        valores_admins = [f"{id_} - {nombre}" for id_, nombre in admins]
        combo_admin = ttk.Combobox(
            self.contenedor,
            values=valores_admins,
            state="readonly",
            width=37
        )
        combo_admin.grid(row=fila, column=1, sticky="w", padx=5, pady=4)

        admin_actual = row["id_administrador"]
        seleccionado_admin = None
        for id_, nombre in admins:
            if id_ == admin_actual:
                seleccionado_admin = f"{id_} - {nombre}"
                break
        combo_admin.set(seleccionado_admin if seleccionado_admin else valores_admins[0])
        fila += 1

        # --- ESTADO ---
        ttk.Label(
            self.contenedor,
            text="Estado:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_estado = ttk.Combobox(
            self.contenedor,
            values=["ABIERTO", "CERRADO"],
            state="readonly",
            width=37
        )
        combo_estado.grid(row=fila, column=1, sticky="w", padx=5, pady=4)

        estado_actual = row["estado"] or "ABIERTO"
        if estado_actual not in ("ABIERTO", "CERRADO"):
            estado_actual = "ABIERTO"
        combo_estado.set(estado_actual)
        fila += 1

        # --- GUARDAR CAMBIOS ---
        def guardar_cambios():
            nombre = entry_nombre.get().strip()
            descripcion = entry_descripcion.get().strip() or None
            duracion_txt = entry_duracion.get().strip()
            cupo_txt = entry_cupo.get().strip()
            fecha_inicio = entry_fecha_inicio.get().strip()
            fecha_fin = entry_fecha_fin.get().strip() or None

            if not nombre:
                messagebox.showwarning("Atención", "El nombre del curso es obligatorio.")
                return
            if not duracion_txt.isdigit() or int(duracion_txt) <= 0:
                messagebox.showwarning("Atención", "La duración debe ser un número entero mayor a 0.")
                return
            if not cupo_txt.isdigit() or int(cupo_txt) <= 0:
                messagebox.showwarning("Atención", "El cupo máximo debe ser un número entero mayor a 0.")
                return
            if not fecha_inicio:
                messagebox.showwarning("Atención", "La fecha de inicio es obligatoria.")
                return

            # ✅ Validación de fechas
            try:
                date.fromisoformat(fecha_inicio)
                if fecha_fin:
                    date.fromisoformat(fecha_fin)
            except Exception:
                messagebox.showwarning("Atención", "Fechas inválidas. Usá YYYY-MM-DD.")
                return

            docente_sel = combo_docente.get()
            admin_sel = combo_admin.get()

            if not docente_sel or not docente_sel.split(" - ")[0].isdigit():
                messagebox.showwarning("Atención", "Seleccioná un docente válido.")
                return
            if not admin_sel or not admin_sel.split(" - ")[0].isdigit():
                messagebox.showwarning("Atención", "Seleccioná un administrador válido.")
                return

            id_docente = int(docente_sel.split(" - ")[0])
            id_admin = int(admin_sel.split(" - ")[0])
            estado = combo_estado.get().strip() or "ABIERTO"

            ok, error = editar_curso_service(
                id_curso=id_curso,
                nombre=nombre,
                descripcion=descripcion,
                duracion_horas=int(duracion_txt),
                cupo_maximo=int(cupo_txt),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_docente=id_docente,
                id_administrador=id_admin,
                estado=estado
            )

            if not ok:
                messagebox.showerror("Error", error or "No se pudo editar el curso.")
                return

            messagebox.showinfo("Éxito", "Curso actualizado correctamente.")
            # ✅ volvemos a gestión (ahí se recrea el tree y se recarga)
            self._gestionar_cursos()

        btn_guardar = ttk.Button(
            self.contenedor,
            text="Guardar cambios",
            style="Accent.TButton",
            command=guardar_cambios
        )
        btn_guardar.grid(row=fila, column=0, columnspan=2, pady=(15, 5))

        # --- VOLVER ---
        btn_volver = ttk.Button(
            self.contenedor,
            text="Volver",
            style="Secondary.TButton",
            command=self._gestionar_cursos
        )
        btn_volver.grid(row=fila + 1, column=0, columnspan=2, pady=(5, 5))

        



    def _limpiar_contenedor(self):
        for w in self.contenedor.winfo_children():
            w.destroy()
        self.entradas.clear()
        self.login_user_entry = None
        self.login_pass_entry = None

    def _mostrar_home(self):
        self._limpiar_contenedor()


        # Título
        texto_titulo = "Academy DevTuc"
        if self.usuario_actual:
            texto_titulo += f" - Sesión: {self.usuario_actual.get('username', '')}"

        titulo = ttk.Label(
            self.contenedor,
            text=texto_titulo,
            style="Title.TLabel"
        )
        titulo.pack(pady=(10, 5))

        # Si NO hay usuario logueado -> mostramos LOGIN + botón Crear usuario
        if self.usuario_actual is None:
            subtitulo = ttk.Label(
                self.contenedor,
                text="Iniciá sesión o creá un usuario nuevo para comenzar.",
                style="Subtitle.TLabel",
                wraplength=600,
                justify="center"
            )
            subtitulo.pack(pady=(0, 20))

            # Frame para el formulario de login
            frame_login = ttk.Frame(self.contenedor, style="Card.TFrame", padding=15)
            frame_login.pack(pady=10)

            # Usuario
            ttk.Label(
                frame_login,
                text="Usuario:",
                style="FormLabel.TLabel"
            ).grid(row=0, column=0, sticky="e", padx=5, pady=5)

            self.login_user_entry = ttk.Entry(frame_login, width=30)
            self.login_user_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

            # Contraseña
            ttk.Label(
                frame_login,
                text="Contraseña:",
                style="FormLabel.TLabel"
            ).grid(row=1, column=0, sticky="e", padx=5, pady=5)

            self.login_pass_entry = ttk.Entry(frame_login, width=30, show="*")
            self.login_pass_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

            # Botón Iniciar sesión
            btn_login = ttk.Button(
                frame_login,
                text="Iniciar sesión",
                style="Accent.TButton",
                command=self._do_login
            )
            btn_login.grid(row=2, column=0, columnspan=2, pady=(10, 5))

            # Enter también hace login
            self.login_pass_entry.bind("<Return>", lambda e: self._do_login())

            # Botón Crear usuario (abre el formulario grande)
            btn_registro = ttk.Button(
                self.contenedor,
                text="Crear nuevo usuario",
                style="Secondary.TButton",
                command=self._form_usuario
            )
            btn_registro.pack(pady=(15, 0))

        # Si hay usuario logueado -> mostramos home "normal"
        else:
            subtitulo = ttk.Label(
                self.contenedor,
                text="Sistema de gestión de alumnos, docentes, cursos e inscripciones.",
                style="Subtitle.TLabel",
                wraplength=600,
                justify="center"
            )
            subtitulo.pack(pady=(0, 20))

            info = ttk.Label(
                self.contenedor,
                text="Usá el menú superior para crear nuevos usuarios y administrar la academia.",
                style="Subtitle.TLabel",
                wraplength=600,
                justify="center"
            )
            info.pack(pady=(0, 10))
        
    

    def _mostrar_perfil_usuario(self):
        self._limpiar_contenedor()

        if not self.usuario_actual:
            messagebox.showinfo(
                "Sin sesión",
                "No hay ningún usuario logueado actualmente.\nIniciá sesión desde el inicio."
            )
            self._mostrar_home()
            return

        ttk.Label(
            self.contenedor,
            text="Mi perfil",
            style="Title.TLabel"
        ).pack(pady=(10, 15))

        datos = self.usuario_actual

        def fila(texto):
            lbl = ttk.Label(
                self.contenedor,
                text=texto,
                style="Subtitle.TLabel",
                wraplength=700,
                justify="left"
            )
            lbl.pack(anchor="w", pady=2)

        fila(f"ID: {datos.get('id', '')}")
        fila(f"Usuario: {datos.get('username', '')}")
        fila(f"Nombre: {datos.get('nombre', '')} {datos.get('apellido', '')}")
        fila(f"Email: {datos.get('email', '')}")
        fila(f"Rol: {datos.get('rol', '')}")
        fila(f"Estado: {datos.get('estado', '')}")

        # 📞 Teléfonos
        try:
            id_usuario = datos.get("id")
            tels = listar_telefonos_por_usuario(int(id_usuario)) if id_usuario else []
            numeros = [t.get("numero") for t in tels if t.get("numero")]
            if numeros:
                fila("Teléfonos: " + ", ".join(numeros))
            else:
                fila("Teléfonos: —")
        except Exception:
            fila("Teléfonos: —")


        calle = datos.get('direccion_calle', '')
        numero = datos.get('direccion_numero', '')
        ciudad = datos.get('direccion_ciudad', '')
        if calle or numero or ciudad:
            fila(f"Dirección: {calle} {numero} - {ciudad}")

        # ==========================
        # TELÉFONOS
        # ==========================
        ttk.Label(
            self.contenedor,
            text="Teléfonos",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(15, 6))

        frame_tel = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tel.pack(fill="x")

        self.tree_tel = ttk.Treeview(frame_tel, columns=("numero",), show="headings", height=4)
        self.tree_tel.heading("numero", text="Número")
        self.tree_tel.column("numero", width=250, anchor="w")
        self.tree_tel.pack(side="left", fill="x", expand=True)

        scroll = ttk.Scrollbar(frame_tel, orient="vertical", command=self.tree_tel.yview)
        self.tree_tel.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        frame_btn = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_btn.pack(fill="x", pady=(8, 0))

        ttk.Button(frame_btn, text="Agregar teléfono", style="Secondary.TButton",
                command=self._form_agregar_telefono).pack(side="left", padx=5)

        ttk.Button(frame_btn, text="Eliminar teléfono", style="Secondary.TButton",
                command=self._eliminar_telefono_seleccionado).pack(side="left", padx=5)

        ttk.Button(frame_btn, text="Recargar", style="Secondary.TButton",
                command=self._cargar_telefonos_usuario_actual).pack(side="left", padx=5)

        self._cargar_telefonos_usuario_actual()



    # ---------- LOGIN DESDE EL HOME ----------
    def _do_login(self):
        if not self.login_user_entry or not self.login_pass_entry:
            messagebox.showwarning("Atención", "No se encontró el formulario de login.")
            return

        usuario = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not usuario or not password:
            messagebox.showwarning("Atención", "Ingresá usuario y contraseña.")
            return

        ok, msg, datos_usuario = verificar_login(usuario, password)

        if not ok:
            messagebox.showerror("Login fallido", msg)
            return

        # ✅ Login OK: guardamos quién es
        self.usuario_actual = datos_usuario

        messagebox.showinfo(
            "Bienvenido",
            f"Hola {datos_usuario.get('nombre', '')} {datos_usuario.get('apellido', '')} "
            f"({datos_usuario.get('rol', '')})"
        )

        # 🔁 Regeneramos el menú según el rol
        self._crear_menu()

        # Y redibujamos el home
        self._mostrar_home()

    #----------- LOGOUT ----------
    def _do_logout(self):
        self.usuario_actual = None
        messagebox.showinfo("Logout", "Sesión cerrada correctamente.")
        self._crear_menu()
        self._mostrar_home()


    # ---------- FORMULARIO USUARIO ----------
    def _form_usuario(self):
        self._limpiar_contenedor()

        # Título del formulario
        ttk.Label(
            self.contenedor,
            text="Nuevo Usuario",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=3, pady=(5, 15))

        campos = [
            ("dni", "DNI"),
            ("username", "Usuario"),
            ("password", "Contraseña"),
            ("telefono", "Teléfono"),
            ("nombre", "Nombre"),
            ("apellido", "Apellido"),
            ("email", "Email"),
            ("direccion_calle", "Calle"),
            ("direccion_numero", "Número"),
            ("direccion_ciudad", "Ciudad"),
        ]

        fila = 1

        def toggle_password():
            # alterna visibilidad del campo password
            if hasattr(self, "password_entry") and hasattr(self, "password_button"):
                actual = self.password_entry.cget("show")
                if actual == "":
                    self.password_entry.config(show="*")
                    self.password_button.config(text="Mostrar")
                else:
                    self.password_entry.config(show="")
                    self.password_button.config(text="Ocultar")

        for (campo, etiqueta) in campos:
            ttk.Label(
                self.contenedor,
                text=f"{etiqueta}:",
                style="FormLabel.TLabel"
            ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

            if campo == "password":
                entry = ttk.Entry(self.contenedor, width=32, show="*")
                entry.grid(row=fila, column=1, padx=5, pady=4, sticky="w")

                btn = ttk.Button(
                    self.contenedor,
                    text="Mostrar",
                    style="Secondary.TButton",
                    command=toggle_password
                )
                btn.grid(row=fila, column=2, sticky="w", padx=(5, 0), pady=4)

                self.password_entry = entry
                self.password_button = btn
                self.entradas[campo] = entry
            else:
                entry = ttk.Entry(self.contenedor, width=40)
                entry.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
                self.entradas[campo] = entry

            fila += 1

        # ---- ROL ----
        ttk.Label(
            self.contenedor,
            text="Rol:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_rol = ttk.Combobox(
            self.contenedor,
            values=["ALUMNO", "DOCENTE", "ADMIN"],
            state="readonly",
            width=37
        )
        combo_rol.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
        combo_rol.set("ALUMNO")
        self.entradas["rol"] = combo_rol
        fila += 1

        # ---- NIVEL (ALUMNO) ----
        ttk.Label(
            self.contenedor,
            text="Nivel (SOLO ALUMNO):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_nivel = ttk.Combobox(
            self.contenedor,
            values=["Principiante", "Intermedio", "Avanzado"],
            state="readonly",
            width=37
        )
        combo_nivel.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
        combo_nivel.set("Principiante")
        self.entradas["Nivel"] = combo_nivel
        self.combo_nivel = combo_nivel
        fila += 1

        # ---- ESPECIALIDAD (DOCENTE) ----
        ttk.Label(
            self.contenedor,
            text="Especialidad (DOCENTE):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_especialidad = ttk.Combobox(
            self.contenedor,
            values=["Programación", "Bases de Datos", "Redes", "Ofimática"],
            state="disabled",
            width=37
        )
        combo_especialidad.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
        combo_especialidad.set("")
        self.entradas["especialidad"] = combo_especialidad
        self.combo_especialidad = combo_especialidad
        fila += 1

        # ---- CARGO (ADMIN) ----
        ttk.Label(
            self.contenedor,
            text="Cargo (ADMIN):",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        cargo_acceso = ttk.Combobox(
            self.contenedor,
            values=["BÁSICO", "INTERMEDIO", "TOTAL"],
            state="disabled",
            width=37
        )
        cargo_acceso.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
        cargo_acceso.set("")
        self.entradas["acceso"] = cargo_acceso
        self.combo_acceso = cargo_acceso
        fila += 1

        # ---- ESTADO ----
        ttk.Label(
            self.contenedor,
            text="Estado:",
            style="FormLabel.TLabel"
        ).grid(row=fila, column=0, sticky="e", padx=5, pady=4)

        combo_estado = ttk.Combobox(
            self.contenedor,
            values=["ACTIVO", "INACTIVO"],
            state="readonly",
            width=37
        )
        combo_estado.grid(row=fila, column=1, padx=5, pady=4, sticky="w")
        combo_estado.set("ACTIVO")
        self.entradas["estado"] = combo_estado
        fila += 1

        # ---- BOTÓN GUARDAR ----
        boton_guardar = ttk.Button(
            self.contenedor,
            text="Guardar Usuario",
            style="Accent.TButton",
            command=self._guardar_usuario
        )
        boton_guardar.grid(row=fila, column=0, columnspan=3, pady=(15, 5))

        # Evento cambio de rol
        combo_rol.bind("<<ComboboxSelected>>", self._on_cambio_rol)

    def _form_curso(self):
        # Permitir ADMIN y DOCENTE (tu menú deja DOCENTE crear curso)
        if not self._es_admin():
            messagebox.showwarning("Permiso denegado", "Solo ADMIN puede crear cursos.")
            self._mostrar_home()
            return

        self._limpiar_contenedor()

        ttk.Label(
            self.contenedor,
            text="Nuevo Curso",
            style="Title.TLabel"
        ).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        docentes, admins = self._get_docentes_y_admins()


        if not docentes:
            messagebox.showwarning("Atención", "No hay docentes disponibles.")
            self._mostrar_home()
            return

        if not admins:
            messagebox.showwarning("Atención", "No hay administradores cargados. Creá un ADMIN primero.")
            self._mostrar_home()
            return

        fila = 1

        # --- NOMBRE ---
        ttk.Label(self.contenedor, text="Nombre del curso:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_nombre = ttk.Entry(self.contenedor, width=40)
        entry_nombre.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DESCRIPCIÓN ---
        ttk.Label(self.contenedor, text="Descripción:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_descripcion = ttk.Entry(self.contenedor, width=40)
        entry_descripcion.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DURACIÓN ---
        ttk.Label(self.contenedor, text="Duración (horas):", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_duracion = ttk.Entry(self.contenedor, width=15)
        entry_duracion.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- CUPO ---
        ttk.Label(self.contenedor, text="Cupo máximo:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_cupo = ttk.Entry(self.contenedor, width=15)
        entry_cupo.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- FECHA INICIO ---
        ttk.Label(self.contenedor, text="Fecha inicio (YYYY-MM-DD):", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_fecha_inicio = ttk.Entry(self.contenedor, width=20)
        entry_fecha_inicio.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- FECHA FIN ---
        ttk.Label(self.contenedor, text="Fecha fin (YYYY-MM-DD):", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        entry_fecha_fin = ttk.Entry(self.contenedor, width=20)
        entry_fecha_fin.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        fila += 1

        # --- DOCENTE ---
        ttk.Label(self.contenedor, text="Docente:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        valores_docentes = [f"{id_} - {nombre}" for id_, nombre in docentes]
        combo_docente = ttk.Combobox(self.contenedor, values=valores_docentes, state="readonly", width=37)
        combo_docente.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        combo_docente.set(valores_docentes[0])
        fila += 1

        # --- ADMIN ---
        ttk.Label(self.contenedor, text="Administrador:", style="FormLabel.TLabel") \
            .grid(row=fila, column=0, sticky="e", padx=5, pady=4)
        valores_admins = [f"{id_} - {nombre}" for id_, nombre in admins]
        combo_admin = ttk.Combobox(self.contenedor, values=valores_admins, state="readonly", width=37)
        combo_admin.grid(row=fila, column=1, sticky="w", padx=5, pady=4)
        combo_admin.set(valores_admins[0])
        fila += 1

        def guardar_curso():
            nombre = entry_nombre.get().strip()
            descripcion = entry_descripcion.get().strip() or None
            duracion_txt = entry_duracion.get().strip()
            cupo_txt = entry_cupo.get().strip()
            fecha_inicio = entry_fecha_inicio.get().strip()
            fecha_fin = entry_fecha_fin.get().strip() or None

            if not nombre:
                messagebox.showwarning("Atención", "El nombre del curso es obligatorio.")
                return
            if not duracion_txt.isdigit() or int(duracion_txt) <= 0:
                messagebox.showwarning("Atención", "La duración debe ser un entero mayor a 0.")
                return
            if not cupo_txt.isdigit() or int(cupo_txt) <= 0:
                messagebox.showwarning("Atención", "El cupo máximo debe ser un entero mayor a 0.")
                return
            if not fecha_inicio:
                messagebox.showwarning("Atención", "La fecha de inicio es obligatoria.")
                return

            id_docente = int(combo_docente.get().split(" - ")[0])
            id_admin = int(combo_admin.get().split(" - ")[0])

            ok, error = crear_curso_service(
                nombre=nombre,
                descripcion=descripcion,
                duracion_horas=int(duracion_txt),
                cupo_maximo=int(cupo_txt),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                id_docente=id_docente,
                id_administrador=id_admin
            )

            if not ok:
                messagebox.showerror("Error", error or "No se pudo crear el curso.")
                return

            messagebox.showinfo("Éxito", f"Curso '{nombre}' creado.")
            # Si es ADMIN vuelve a gestión, si es DOCENTE vuelve a mis cursos
            if self._es_admin():
                self._gestionar_cursos()
            else:
                self._mis_cursos_docente()

        ttk.Button(
            self.contenedor,
            text="Guardar",
            style="Accent.TButton",
            command=guardar_curso
        ).grid(row=fila, column=0, columnspan=2, pady=(15, 5))

        ttk.Button(
            self.contenedor,
            text="Volver",
            style="Secondary.TButton",
            command=(self._gestionar_cursos if self._es_admin() else self._mis_cursos_docente)
        ).grid(row=fila + 1, column=0, columnspan=2, pady=(5, 0))


    def _on_cambio_rol(self, event=None):
        # Obtengo el rol desde el combobox
        if event is not None and hasattr(event, "widget"):
            rol = event.widget.get()
        else:
            rol = self.entradas.get("rol").get() if self.entradas.get("rol") else "ALUMNO"

        # Deshabilito todos los específicos
        self.combo_nivel.config(state="disabled")
        self.combo_especialidad.config(state="disabled")
        self.combo_acceso.config(state="disabled")

        # Limpio valores
        self.combo_nivel.set("")
        self.combo_especialidad.set("")
        self.combo_acceso.set("")

        if rol == "ALUMNO":
            self.combo_nivel.config(state="readonly")
            self.combo_nivel.set("Principiante")
        elif rol == "DOCENTE":
            self.combo_especialidad.config(state="readonly")
            self.combo_especialidad.set("Programación")
        elif rol == "ADMIN":
            self.combo_acceso.config(state="readonly")
            self.combo_acceso.set("BÁSICO")

    def _get_docentes_y_admins(self):
        """Devuelve (lista_docentes, lista_admins),
        cada uno es una lista de tuplas (id, 'Nombre Apellido')."""
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()

            cur.execute("SELECT id, nombre, apellido FROM usuario WHERE rol = 'DOCENTE' ORDER BY nombre, apellido")
            docentes = [(row["id"], f'{row["nombre"]} {row["apellido"]}') for row in cur.fetchall()]

            cur.execute("SELECT id, nombre, apellido FROM usuario WHERE rol = 'ADMIN' ORDER BY nombre, apellido")
            admins = [(row["id"], f'{row["nombre"]} {row["apellido"]}') for row in cur.fetchall()]

            return docentes, admins
        finally:
            conn.close()

    # ---------- ACCIÓN GUARDAR ----------
    def _guardar_usuario(self):
        d = {k: e.get().strip() for k, e in self.entradas.items()}

        telefono = (d.get("telefono") or "").strip()


        # Validación mínima
        if not d.get("nombre") or not d.get("apellido"):
            messagebox.showwarning("Atención", "Nombre y Apellido son obligatorios.")
            return

        if not d.get("username"):
            messagebox.showwarning("Atención", "Usuario (username) es obligatorio.")
            return

        password = d.get("password") or ""
        ok, msg = password_strength(password)
        if not ok:
            messagebox.showwarning("Contraseña débil", msg)
            return

        if d.get("rol") not in ("ALUMNO", "DOCENTE", "ADMIN"):
            messagebox.showwarning("Atención", "Rol debe ser ALUMNO, DOCENTE o ADMIN.")
            return

        usuario = Usuario(
            dni=d.get("dni") or None,
            username=d.get("username"),
            nombre=d["nombre"],
            apellido=d["apellido"],
            email=d.get("email") or None,
            estado=d.get("estado") or "ACTIVO",
            rol=d.get("rol") or "ALUMNO",
            direccion_calle=d.get("direccion_calle") or None,
            direccion_numero=d.get("direccion_numero") or None,
            direccion_ciudad=d.get("direccion_ciudad") or None,
            password=hash_password(password),
        )

        try:
            nuevo_id = crear_usuario(usuario)
            
            # --- TELÉFONO (opcional) ---
            tel = (d.get("telefono") or "").strip()
           

            # 📞 Guardar teléfono si vino cargado
            if telefono:
                ok_tel, err_tel = agregar_telefono(Telefono(id_usuario=nuevo_id, numero=telefono))
                if not ok_tel:
                    messagebox.showwarning(
                        "Atención",
                        f"Usuario creado (ID {nuevo_id}), pero no se pudo guardar el teléfono:\n{err_tel}"
        )


            # Rol específico (services maneja DB)
            if usuario.rol == "ALUMNO":
                nivel = d.get("nivel") or "Principiante"
                crear_rol_alumno(Alumno(id_usuario=nuevo_id, nivel=nivel))

            elif usuario.rol == "DOCENTE":
                especialidad = d.get("especialidad") or "Programación"
                crear_rol_docente(Docente(id_usuario=nuevo_id, especialidad=especialidad))

            elif usuario.rol == "ADMIN":
                acceso = d.get("acceso") or "BÁSICO"
                crear_rol_admin(Administrador(id_usuario=nuevo_id, cargo=acceso))

            # Limpio campos
            for e in self.entradas.values():
                try:
                    e.delete(0, tk.END)
                except Exception:
                    pass

            if "rol" in self.entradas:
                self.entradas["rol"].set("ALUMNO")
            if "estado" in self.entradas:
                self.entradas["estado"].set("ACTIVO")
            if "nivel" in self.entradas:
                self.entradas["nivel"].set("Principiante")

            messagebox.showinfo(
                "Usuario Registrado",
                f"Usuario creado.\nID: {nuevo_id}"
            )

        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "dni" in msg:
                messagebox.showerror("Error", "El DNI ya está registrado.")
            elif "username" in msg:
                messagebox.showerror("Error", "El nombre de usuario ya existe.")
            elif "email" in msg:
                messagebox.showerror("Error", "El correo electrónico ya está registrado.")
            else:
                messagebox.showerror("Error", f"Error de datos duplicados:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado:\n{e}")

#===============================================
# TELEFONO
#===============================================
    def _cargar_telefonos_usuario_actual(self):
        if not self.usuario_actual or not hasattr(self, "tree_tel"):
            return

        for item in self.tree_tel.get_children():
            self.tree_tel.delete(item)

        try:
            id_usuario = int(self.usuario_actual.get("id"))
            telefonos = listar_telefonos_por_usuario(id_usuario)  # [{'numero': '...'}]
            for t in telefonos:
                self.tree_tel.insert("", "end", values=(t.get("numero", ""),))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los teléfonos:\n{e}")


    def _form_agregar_telefono(self):
        if not self.usuario_actual:
            return

        win = tk.Toplevel(self.root)
        win.title("Agregar teléfono")
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)

        ttk.Label(frm, text="Número:", style="FormLabel.TLabel").grid(row=0, column=0, sticky="w")
        var_num = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=var_num, width=30)
        ent.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        ent.focus()

        def guardar():
            numero = (var_num.get() or "").strip()
            if not numero:
                messagebox.showwarning("Atención", "Ingresá un número.")
                return

            try:
                tel = Telefono(id_usuario=int(self.usuario_actual["id"]), numero=numero)
                ok, err = agregar_telefono(tel)
                if not ok:
                    messagebox.showerror("Error", err or "No se pudo agregar el teléfono.")
                    return

                messagebox.showinfo("Éxito", "Teléfono agregado.")
                win.destroy()
                self._cargar_telefonos_usuario_actual()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el teléfono:\n{e}")

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, sticky="e")

        ttk.Button(btns, text="Cancelar", command=win.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="Guardar", style="Accent.TButton", command=guardar).grid(row=0, column=1)

        frm.columnconfigure(0, weight=1)


    def _eliminar_telefono_seleccionado(self):
        if not self.usuario_actual or not hasattr(self, "tree_tel"):
            return

        sel = self.tree_tel.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccioná un teléfono.")
            return

        numero = self.tree_tel.item(sel[0], "values")[0]
        if not numero:
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar el teléfono '{numero}'?"
        )
        if not confirmar:
            return

        try:
            ok, err = eliminar_telefono(int(self.usuario_actual["id"]), str(numero))
            if not ok:
                messagebox.showerror("Error", err or "No se pudo eliminar.")
                return

            messagebox.showinfo("Éxito", "Teléfono eliminado.")
            self._cargar_telefonos_usuario_actual()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")

    def _form_examen_docente(self):
        if not self._es_docente():
            messagebox.showwarning("Permiso denegado", "Solo DOCENTE.")
            return

        self._limpiar_contenedor()
        ttk.Label(self.contenedor, text="Crear examen", style="Title.TLabel").pack(pady=(10, 15))

        
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT id, nombre FROM curso WHERE id_docente = ? ORDER BY nombre;",
                (int(self.usuario_actual["id"]),)
            )
            cursos = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        if not cursos:
            messagebox.showinfo("Info", "No tenés cursos asignados.")
            return

        map_curso = {c["nombre"]: c["id"] for c in cursos}

        frm = ttk.Frame(self.contenedor, style="Card.TFrame", padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="Curso:", style="FormLabel.TLabel").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        cb_curso = ttk.Combobox(frm, state="readonly", values=list(map_curso.keys()), width=40)
        cb_curso.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        cb_curso.set(list(map_curso.keys())[0])

        ttk.Label(frm, text="Nombre examen:", style="FormLabel.TLabel").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        ent_nombre = ttk.Entry(frm, width=42)
        ent_nombre.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(frm, text="Tipo:", style="FormLabel.TLabel").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        cb_tipo = ttk.Combobox(frm, state="readonly", values=["PARCIAL", "FINAL", "TP"], width=15)
        cb_tipo.grid(row=2, column=1, sticky="w", padx=5, pady=4)
        cb_tipo.set("PARCIAL")

        ttk.Label(frm, text="Fecha (YYYY-MM-DD):", style="FormLabel.TLabel").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        ent_fecha = ttk.Entry(frm, width=20)
        ent_fecha.grid(row=3, column=1, sticky="w", padx=5, pady=4)
        ent_fecha.insert(0, str(date.today()))

        def guardar():
            id_curso = map_curso.get(cb_curso.get())
            ex = Examen(
                id=None,
                id_curso=int(id_curso),
                nombre=ent_nombre.get().strip(),
                tipo=cb_tipo.get().strip(),
                fecha_examen=ent_fecha.get().strip(),
            )
            ok, err = crear_examen_service(ex)
            if not ok:
                messagebox.showerror("Error", err or "No se pudo crear el examen.")
                return
            messagebox.showinfo("Éxito", "Examen creado.")
            ent_nombre.delete(0, tk.END)

        btns = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Guardar", style="Accent.TButton", command=guardar).pack(side="left", padx=5)
        ttk.Button(btns, text="Volver", style="Secondary.TButton", command=self._mostrar_home).pack(side="left", padx=5)

    def _form_examen_docente(self):
        if not self._es_docente():
            messagebox.showwarning("Permiso denegado", "Solo DOCENTE.")
            return

        self._limpiar_contenedor()
        ttk.Label(self.contenedor, text="Crear examen", style="Title.TLabel").pack(pady=(10, 15))

        # cursos del docente (simple: query directo)
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT id, nombre FROM curso WHERE id_docente = ? ORDER BY nombre;",
                (int(self.usuario_actual["id"]),)
            )
            cursos = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        if not cursos:
            messagebox.showinfo("Info", "No tenés cursos asignados.")
            return

        map_curso = {c["nombre"]: c["id"] for c in cursos}

        frm = ttk.Frame(self.contenedor, style="Card.TFrame", padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="Curso:", style="FormLabel.TLabel").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        cb_curso = ttk.Combobox(frm, state="readonly", values=list(map_curso.keys()), width=40)
        cb_curso.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        cb_curso.set(list(map_curso.keys())[0])

        ttk.Label(frm, text="Nombre examen:", style="FormLabel.TLabel").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        ent_nombre = ttk.Entry(frm, width=42)
        ent_nombre.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(frm, text="Tipo:", style="FormLabel.TLabel").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        cb_tipo = ttk.Combobox(frm, state="readonly", values=["PARCIAL", "FINAL", "TP"], width=15)
        cb_tipo.grid(row=2, column=1, sticky="w", padx=5, pady=4)
        cb_tipo.set("PARCIAL")

        ttk.Label(frm, text="Fecha (YYYY-MM-DD):", style="FormLabel.TLabel").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        ent_fecha = ttk.Entry(frm, width=20)
        ent_fecha.grid(row=3, column=1, sticky="w", padx=5, pady=4)
        ent_fecha.insert(0, str(date.today()))

        def guardar():
            id_curso = map_curso.get(cb_curso.get())
            ex = Examen(
                id=None,
                id_curso=int(id_curso),
                nombre=ent_nombre.get().strip(),
                tipo=cb_tipo.get().strip(),
                fecha_examen=ent_fecha.get().strip(),
            )
            ok, err = crear_examen_service(ex)
            if not ok:
                messagebox.showerror("Error", err or "No se pudo crear el examen.")
                return
            messagebox.showinfo("Éxito", "Examen creado.")
            ent_nombre.delete(0, tk.END)

        btns = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Guardar", style="Accent.TButton", command=guardar).pack(side="left", padx=5)
        ttk.Button(btns, text="Volver", style="Secondary.TButton", command=self._mostrar_home).pack(side="left", padx=5)

    

    def _mis_notas_alumno(self):
        if not self.usuario_actual or self.usuario_actual.get("rol") != "ALUMNO":
            messagebox.showwarning("Permiso denegado", "Solo ALUMNO.")
            return

        self._limpiar_contenedor()
        ttk.Label(self.contenedor, text="Mis notas", style="Title.TLabel").pack(pady=(10, 15))

        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("Curso", "Examen", "Tipo", "Fecha examen", "Nota", "Obs")
        tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=12)
        for c in columnas:
            tree.heading(c, text=c)

        tree.column("Curso", width=160)
        tree.column("Examen", width=200)
        tree.column("Tipo", width=80, anchor="center")
        tree.column("Fecha examen", width=110, anchor="center")
        tree.column("Nota", width=70, anchor="center")
        tree.column("Obs", width=220)

        tree.pack(side="left", fill="both", expand=True)

        sy = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")

        def cargar():
            for it in tree.get_children():
                tree.delete(it)

            filas = listar_notas_por_alumno(int(self.usuario_actual["id"]))
            for r in filas:
                tree.insert(
                    "",
                    "end",
                    values=(
                        r.get("curso",""),
                        r.get("examen",""),
                        r.get("tipo",""),
                        r.get("fecha_examen",""),
                        r.get("nota",""),
                        r.get("observacion") or "",
                    )
                )

        btns = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Recargar", style="Secondary.TButton", command=cargar).pack(side="left", padx=5)

        cargar()

    def _cargar_notas_docente(self):
        if not self._es_docente():
            messagebox.showwarning("Permiso denegado", "Solo DOCENTE.")
            return

        self._limpiar_contenedor()
        ttk.Label(self.contenedor, text="Cargar notas", style="Title.TLabel").pack(pady=(10, 15))

        # cursos del docente
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT id, nombre FROM curso WHERE id_docente = ? ORDER BY nombre;",
                (int(self.usuario_actual["id"]),)
            )
            cursos = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        if not cursos:
            messagebox.showinfo("Info", "No tenés cursos asignados.")
            return

        map_curso = {c["nombre"]: c["id"] for c in cursos}

        top = ttk.Frame(self.contenedor, style="Card.TFrame", padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Curso:", style="FormLabel.TLabel").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        cb_curso = ttk.Combobox(top, state="readonly", values=list(map_curso.keys()), width=40)
        cb_curso.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        cb_curso.set(list(map_curso.keys())[0])

        ttk.Label(top, text="Examen:", style="FormLabel.TLabel").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        cb_examen = ttk.Combobox(top, state="readonly", values=[], width=40)
        cb_examen.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        self.cb_curso = cb_curso
        self.cb_examen = cb_examen

        self.map_examen = {}

    

        # tabla alumnos
        frame_tabla = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        frame_tabla.pack(fill="both", expand=True, pady=(10, 0))

        columnas = ("ID Alumno", "Alumno", "Estado", "Nota", "Obs")
        tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)
        for c in columnas:
            tree.heading(c, text=c)
        tree.column("ID Alumno", width=80, anchor="center")
        tree.column("Alumno", width=220)
        tree.column("Estado", width=110, anchor="center")
        tree.column("Nota", width=80, anchor="center")
        tree.column("Obs", width=220)
        tree.pack(side="left", fill="both", expand=True)

        sy = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")


        self.tree_notas = tree  

        self.tree_notas.bind("<Double-1>", self._editar_celda_nota)
        
        

        def recargar_examenes_y_alumnos():
            id_curso = int(map_curso[cb_curso.get()])

            # 1) cargar exámenes
            exs = listar_examenes_por_curso(id_curso)

            visibles = []
            self.map_examen = {}

            for e in exs:
                # si viene como dict
                if isinstance(e, dict):
                    ex_id = e.get("id")
                    fecha = e.get("fecha_examen", "")
                    tipo = e.get("tipo", "")
                    nombre = e.get("nombre", "")
                else:
                    # si viene como tupla: (id, id_curso, nombre, tipo, fecha_examen)
                    ex_id = e[0]
                    nombre = e[2]
                    tipo = e[3]
                    fecha = e[4]

                txt = f"{fecha} - {tipo} - {nombre}"
                visibles.append(txt)
                self.map_examen[txt] = int(ex_id)

            cb_examen["values"] = visibles
            cb_examen.set(visibles[0] if visibles else "")

            # 2) cargar alumnos inscriptos
            for it in tree.get_children():
                tree.delete(it)

            alumnos = listar_inscriptos_por_curso(id_curso)
            for a in alumnos:
                tree.insert("", "end", values=(a["id_alumno"], a["alumno"], a["estado_insc"], "", ""))

        cb_curso.bind("<<ComboboxSelected>>", lambda e: recargar_examenes_y_alumnos())
        recargar_examenes_y_alumnos()  

        def guardar_nota_seleccion():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Atención", "Seleccioná un alumno en la tabla.")
                return
            if not cb_examen.get():
                messagebox.showwarning("Atención", "No hay examen seleccionado.")
                return

            values = tree.item(sel[0], "values")
            id_alumno = int(values[0])

            # pedimos nota y obs
            win = tk.Toplevel(self.root)
            win.title("Guardar nota")
            win.transient(self.root)
            win.grab_set()

            frm = ttk.Frame(win, padding=12)
            frm.grid(row=0, column=0, sticky="nsew")

            ttk.Label(frm, text="Nota (0-10):").grid(row=0, column=0, sticky="w")
            var_nota = tk.StringVar()
            ent_nota = ttk.Entry(frm, textvariable=var_nota, width=10)
            ent_nota.grid(row=0, column=1, sticky="w", padx=(8, 0))

            ttk.Label(frm, text="Observación:").grid(row=1, column=0, sticky="w", pady=(8, 0))
            var_obs = tk.StringVar()
            ent_obs = ttk.Entry(frm, textvariable=var_obs, width=35)
            ent_obs.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

            def ok():
                try:
                    nota_val = float(var_nota.get().replace(",", "."))
                except Exception:
                    messagebox.showwarning("Atención", "Nota inválida.")
                    return

                id_examen = self.map_examen.get(cb_examen.get())
                if not id_examen:
                    messagebox.showwarning("Atención", "Examen inválido.")
                    return
                id_examen = int(id_examen)
                n = Nota(
                    id=None,
                    id_examen=id_examen,
                    id_alumno=id_alumno,
                    nota=nota_val,
                    fecha_registro=str(date.today()),
                    observacion=var_obs.get().strip() or None
                )
                ok_, err = guardar_nota_service(n)
                if not ok_:
                    messagebox.showerror("Error", err or "No se pudo guardar la nota.")
                    return

                # reflejar en la fila
                tree.item(sel[0], values=(values[0], values[1], values[2], nota_val, var_obs.get().strip()))
                messagebox.showinfo("Éxito", "Nota guardada.")
                win.destroy()

            btns = ttk.Frame(frm)
            btns.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
            ttk.Button(btns, text="Cancelar", command=win.destroy).grid(row=0, column=0, padx=(0, 8))
            ttk.Button(btns, text="Guardar", style="Accent.TButton", command=ok).grid(row=0, column=1)

        botones = ttk.Frame(self.contenedor, style="Card.TFrame", padding=10)
        botones.pack(fill="x", pady=(10, 0))
        ttk.Button(botones, text="Guardar nota", style="Accent.TButton", command=guardar_nota_seleccion).pack(side="left", padx=5)
        ttk.Button(botones, text="Recargar", style="Secondary.TButton", command=recargar_examenes_y_alumnos).pack(side="left", padx=5)

    def _editar_celda_nota(self, event):
        tree = self.tree_notas
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)  # '#1', '#2', etc.

        if not item:
            return

        # Ajustá este número según el orden real de tus columnas:
        # Ejemplo columnas: ("ID Alumno","Alumno","Estado","Nota","Obs")
        # entonces Nota = #4
        if col != "#4":
            return

        x, y, w, h = tree.bbox(item, col)
        valor_actual = tree.set(item, col)

        entry = ttk.Entry(tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, valor_actual)
        entry.focus()

        def guardar_evento(e=None):
            nuevo_valor = entry.get().strip()
            entry.destroy()
            self._guardar_nota_desde_tree(item, nuevo_valor)

        entry.bind("<Return>", guardar_evento)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.bind("<FocusOut>", guardar_evento)


    def _guardar_nota_desde_tree(self, item_id, nota_str: str):
        tree = self.tree_notas
        values = tree.item(item_id, "values")

        # columnas: ("ID Alumno","Alumno","Estado","Nota","Obs")
        try:
            id_alumno = int(values[0])
        except Exception:
            messagebox.showerror("Error", "No se pudo leer el ID del alumno.")
            return

        # 1) validar nota
        try:
            nota_val = float((nota_str or "").replace(",", "."))
            if not (0 <= nota_val <= 10):
                raise ValueError
        except Exception:
            messagebox.showwarning("Atención", "La nota debe ser un número entre 0 y 10.")
            return

        # 2) examen seleccionado
        examen_txt = (self.cb_examen.get() or "").strip()
        if not examen_txt:
            messagebox.showwarning("Atención", "Seleccioná un examen.")
            return

        id_examen = self.map_examen.get(examen_txt)
        if not id_examen:
            messagebox.showwarning("Atención", "Examen inválido.")
            return

        # 3) guardar en DB (service)
        try:
            from datetime import date
            from models import Nota
            from services import guardar_nota_service

            n = Nota(
                id_examen=int(id_examen),
                id_alumno=int(id_alumno),
                nota=float(nota_val),
                fecha_registro=str(date.today()),
                observacion=None
            )

            ok, err = guardar_nota_service(n)
            if not ok:
                messagebox.showerror("Error", err or "No se pudo guardar la nota.")
                return

            # 4) reflejar en el tree
            tree.set(item_id, "Nota", f"{nota_val:.2f}".rstrip("0").rstrip("."))
            tree.set(item_id, "Estado", "CARGADA")
            messagebox.showinfo("Éxito", "Nota guardada.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la nota:\n{e}")







    def _no_implementado(self):
        self._limpiar_contenedor()
        ttk.Label(
            self.contenedor,
            text="Función en desarrollo.",
            style="Subtitle.TLabel"
        ).pack(pady=20)



# =========================
#   ARRANQUE DE LA APP
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = AppAcademia(root)
    root.mainloop()
