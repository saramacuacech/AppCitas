import flet as ft
import httpx
import random
import datetime
import time

import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

class ModernTextField(ft.Container):
    def __init__(self, label, hint, icon, keyboard_type=ft.KeyboardType.TEXT, password=False):
        super().__init__()
        self.text_field = ft.TextField(
            hint_text=hint,
            label_style=ft.TextStyle(color="#1a5276", size=12),
            border=ft.InputBorder.NONE,
            password=password,
            can_reveal_password=password,
            keyboard_type=keyboard_type,
            cursor_color="#1a5276",
            text_style=ft.TextStyle(color="#1a5276"),
            expand=True,
        )
        self.content = ft.Row(
            [
                ft.Icon(icon, color="#1a5276", size=20),
                ft.Column(
                    [
                        ft.Text(label, size=12, color="#1a5276", weight=ft.FontWeight.W_600),
                        self.text_field,
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        self.bgcolor = ft.Colors.WHITE
        self.padding = 12
        self.border_radius = 10
        self.shadow = ft.BoxShadow(
            blur_radius=15,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        )
        self.width = 300

    @property
    def value(self):
        return self.text_field.value

    @value.setter
    def value(self, val):
        self.text_field.value = val

    @property
    def error_text(self):
        return self.text_field.error_text

    @error_text.setter
    def error_text(self, val):
        self.text_field.error_text = val

def main(page: ft.Page):
    # Variable global para almacenar el usr_id
    usr_id = None
    usr_name = None
    
    # Variable para la respuesta del CAPTCHA
    captcha_answer = 0

    # Contador de intentos fallidos
    failed_attempts = 0
    
    page.title = "App Citas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#e8f4f8" # Fondo azul muy suave
    
    # --- Componentes para Login ---
    txt_usuario = ft.TextField(
        label="Usuario",
        hint_text="Ingrese su usuario",
        text_align=ft.TextAlign.CENTER,
        width=280,
        border_radius=10,
    )

    txt_password = ft.TextField(
        label="Contraseña",
        hint_text="Ingrese su contraseña",
        password=True,
        can_reveal_password=True,
        text_align=ft.TextAlign.CENTER,
        width=280,
        border_radius=10,
    )
    
    # Componentes del CAPTCHA
    captcha_text = ft.Text(
        "",
        size=18,
        weight=ft.FontWeight.BOLD,
        color="#005288",
        text_align=ft.TextAlign.CENTER,
    )
    
    txt_captcha = ft.TextField(
        label="Resultado",
        hint_text="Ingrese el resultado",
        text_align=ft.TextAlign.CENTER,
        width=280,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
    )
    
    captcha_container = ft.Container(
        content=ft.Column(
            [
                captcha_text,
                txt_captcha,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )
    
    def generate_captcha():
        """Genera un CAPTCHA matemático simple"""
        nonlocal captcha_answer
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        captcha_answer = num1 + num2
        captcha_text.value = f"CAPTCHA: ¿Cuánto es {num1} + {num2}?"
        return captcha_answer

    loading = ft.ProgressRing(visible=False, color="#005288")

    async def login_task():
        nonlocal usr_id, usr_name, failed_attempts
        
        loading.visible = True
        btn_login.disabled = True
        page.update()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/login", 
                    json={
                        "usuario": txt_usuario.value,
                        "password": txt_password.value
                    },
                    timeout=10.0
                )
            
            loading.visible = False
            btn_login.disabled = False
            
            if response.status_code == 200:
                data = response.json()

                usr_id = data["usr_id"]
                usr_name = data["usr_name"]
                user_role = data["r_name"]

                failed_attempts = 0
                txt_captcha.value = ""
                txt_usuario.value = ""
                txt_password.value = ""

                if user_role == "Admin":
                    show_home_admin()
                elif user_role == "Agente":
                    show_home_agente()
                else:
                    show_home()  # Paciente
            else:
                failed_attempts += 1
                error_msg = response.json().get("detail", "Error")
                
                if failed_attempts >= 5:
                    txt_usuario.disabled = True
                    txt_password.disabled = True
                    txt_captcha.disabled = True
                    btn_login.disabled = True
                    error_msg = "Demasiados intentos fallidos. El acceso ha sido bloqueado."
                
                sn = ft.SnackBar(ft.Text(error_msg), bgcolor=ft.Colors.RED)
                page.overlay.append(sn)
                sn.open = True
                
        except Exception as ex:
            failed_attempts += 1
            loading.visible = False
            btn_login.disabled = False
            
            error_text = f"Error: {ex}"
            if failed_attempts >= 5:
                txt_usuario.disabled = True
                txt_password.disabled = True
                txt_captcha.disabled = True
                btn_login.disabled = True
                error_text = "Demasiados intentos fallidos. El acceso ha sido bloqueado."

            sn = ft.SnackBar(ft.Text(error_text), bgcolor=ft.Colors.RED)
            page.overlay.append(sn)
            sn.open = True
        
        page.update()

    def login_click(e):
        if not txt_usuario.value:
            txt_usuario.error_text = "Por favor ingrese su usuario"
            page.update()
            return

        if not txt_password.value:
            txt_password.error_text = "Por favor ingrese su contraseña"
            page.update()
            return
        
        # Verificar CAPTCHA (siempre requerido)
        if True:
            if not txt_captcha.value:
                txt_captcha.error_text = "Por favor resuelva el CAPTCHA"
                page.update()
                return
            
            try:
                user_answer = int(txt_captcha.value)
                if user_answer != captcha_answer:
                    sn = ft.SnackBar(
                        ft.Text("CAPTCHA incorrecto. Intente nuevamente."),
                        bgcolor=ft.Colors.RED
                    )
                    page.overlay.append(sn)
                    sn.open = True
                    # Generar nuevo CAPTCHA
                    generate_captcha()
                    txt_captcha.value = ""
                    page.update()
                    return
                else:
                    # CAPTCHA correcto: limpiar campo y regenerar para el próximo intento
                    txt_captcha.value = ""
                    generate_captcha()
            except ValueError:
                txt_captcha.error_text = "Ingrese un número válido"
                page.update()
                return
        
        page.run_task(login_task)

    btn_login = ft.Container(
        content=ft.Text("Iniciar Sesión", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        alignment=ft.Alignment(0, 0),
        bgcolor="#005288",
        width=250,
        height=45,
        border_radius=25,
        on_click=login_click,
    )

    # --- Componentes para Registro ---
    txt_reg_usuario = ModernTextField(
        label="Usuario",
        hint="Elija un nombre de usuario",
        icon=ft.Icons.PERSON_ADD,
    )

    txt_reg_password = ModernTextField(
        label="Contraseña",
        hint="Elija una contraseña",
        icon=ft.Icons.LOCK,
        password=True,
    )

    async def register_task(e):
        loading.visible = True
        page.update()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/register",
                    json={
                        "usuario": txt_reg_usuario.value,
                        "password": txt_reg_password.value
                    },
                    timeout=10.0
                )
            
            loading.visible = False
            
            if response.status_code == 200:
                sn = ft.SnackBar(ft.Text("Registro exitoso. Por favor inicie sesión."), bgcolor=ft.Colors.GREEN)
                page.overlay.append(sn)
                sn.open = True
                txt_reg_usuario.value = ""
                txt_reg_password.value = ""
                show_login()
            else:
                error_msg = response.json().get("detail", "Error en el registro")
                sn = ft.SnackBar(ft.Text(error_msg), bgcolor=ft.Colors.RED)
                page.overlay.append(sn)
                sn.open = True
                
        except Exception as ex:
            loading.visible = False
            sn = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
            page.overlay.append(sn)
            sn.open = True
        
        page.update()

    def show_register(e=None):
        page.controls.clear()
        
        # Decoraciones de fondo (Círculos) - Diseño diferente al login
        reg_bg_elements = [
             # Círculo grande inferior derecha
            ft.Container(
                width=200,
                height=200,
                bgcolor="#005288",
                border_radius=125,
                bottom=-120,
                right=-60,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
            ),
             # Círculo mediano superior izquierda
            ft.Container(
                width=180,
                height=180,
                bgcolor="#005288",
                border_radius=90,
                top=-60,
                left=-60,
            ),
             # Círculo pequeño superior derecha
            ft.Container(
                width=100,
                height=100,
                bgcolor="#1a5276",
                border_radius=50,
                top=40,
                right=20,
            ),
            # Círculo pequeño inferior izquierda
            ft.Container(
                width=80,
                height=80,
                bgcolor="#1a5276",
                border_radius=40,
                bottom=50,
                left=20,
            ),
        ]

        register_form = ft.Column(
            [
                ft.Container(
                    content=ft.Image(
                        src="/Logo.png",
                        width=210,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    margin=ft.margin.only(bottom=-50),
                ),
                ft.Container(height=50),
                ft.Text(
                    "Crear nueva cuenta",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color="#005288",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=5),
                txt_reg_usuario,
                ft.Container(height=10),
                txt_reg_password,
                ft.Container(height=20),
                loading,
                ft.Container(
                    content=ft.Text("Registrarse", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    alignment=ft.Alignment(0, 0),
                    bgcolor="#005288",
                    width=250,
                    height=45,
                    border_radius=25,
                    on_click=register_task,
                ),
                ft.TextButton(
                    "Volver al inicio de sesión",
                    on_click=lambda _: show_login(),
                    style=ft.ButtonStyle(color="#005288"),
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        page.add(
            ft.Stack(
                [
                    *reg_bg_elements,
                    ft.Container(
                        content=register_form,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    )
                ],
                expand=True,
            )
        )
        page.update()

    def show_login():
        page.controls.clear()
        
        # Decoraciones de fondo (Círculos)
        bg_elements = [
            # Círculo grande superior derecha
            ft.Container(
                width=250,
                height=250,
                bgcolor="#005288",
                border_radius=125,
                top=-150,
                right=-80,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK))
            ),
            # Círculo pequeño superior izquierda
            ft.Container(
                width=150,
                height=150,
                bgcolor="#005288",
                border_radius=90,
                top=-80,
                left=-50,
            ),
            # Círculos inferiores
            ft.Container(
                width=200,
                height=200,
                bgcolor="#005288",
                border_radius=100,
                bottom=-100,
                left=-80,
            ),
            ft.Container(
                width=84,
                height=84,
                bgcolor="#0062AD",
                border_radius=50,
                bottom=90,
                left=60,
            ),
        ]

        login_form = ft.Column(
            [
                # Logo de Clinizad
                ft.Container(
                    content=ft.Image(
                        src="/Logo.png",
                        width=250,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    margin=ft.margin.only(bottom=-50),
                ),
                ft.Container(height=60),
                txt_usuario,
                ft.Container(height=5),
                txt_password,
                captcha_container,
                ft.Container(height=5),
                loading,
                btn_login,
                ft.TextButton(
                    "¿No tienes cuenta? Regístrate",
                    on_click=show_register,
                    style=ft.ButtonStyle(color="#005288"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        page.add(
            ft.Stack(
                [
                    *bg_elements,
                    ft.Container(
                        content=login_form,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    )
                ],
                expand=True,
            )
        )
        # Generar el primer CAPTCHA
        generate_captcha()
        page.update()

    def show_home():
        nonlocal usr_id, usr_name
        page.controls.clear()
        
        # Card para Agendar Cita
        card_agendar = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=60, color="#005288"),
                    ft.Text("Agendar Cita", size=20, weight=ft.FontWeight.BOLD, color="#005288"),
                    ft.Text("Programa tu próxima cita", size=12, color="#666666", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=15,
            width=280,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            ),
            on_click=lambda _: show_agendar_cita(),
            ink=True,
        )
        
        
        # Contenedor principal con el contenido
        main_content = ft.Column(
            [
                # Sección de bienvenida
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"¡Hola {usr_name}!",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color="#005288",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=30),
                            ft.Text(
                                "Bienvenido a tu portal de citas",
                                size=16,
                                color="#666666",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    padding=ft.padding.only(top=40, bottom=30),
                ),
                
                # Cards de acciones principales
                ft.Row(
                    [card_agendar],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    wrap=True,  # Para que se adapta en pantallas pequeñas
                ),
                
                # Botón de cerrar sesión
                ft.Container(
                    content=ft.TextButton(
                        "Cerrar Sesión",
                        icon=ft.Icons.LOGOUT,
                        on_click=lambda _: show_login(),
                        style=ft.ButtonStyle(
                            color=ft.Colors.RED_400,
                        ),
                    ),
                    padding=ft.padding.only(top=40),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,  # Para permitir scroll en pantallas pequeñas
        )
        
        page.add(
            ft.AppBar(
                title=ft.Text("Inicio"),
                bgcolor="#005288",
                color=ft.Colors.WHITE,
                center_title=True,
            ),
            ft.Container(
                content=main_content,
                expand=True,
                alignment=ft.Alignment(0, -0.2),  # Centrado con ligero desplazamiento hacia arriba
            )
        )
        page.update()

        def handle_confirmar_sede(e, dropdown, lab_field, nombre_field, cedula_field, empresa_field, fecha_field):
            print("Confirming appointment with:", nombre_field.value, cedula_field.value, empresa_field.value, dropdown.value, lab_field.value, fecha_field.value)
            if not nombre_field.value:
                sn = ft.SnackBar(ft.Text("Por favor ingrese su nombre completo"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return

            if not cedula_field.value:
                sn = ft.SnackBar(ft.Text("Por favor ingrese su cédula"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return
            if not empresa_field.value:
                sn = ft.SnackBar(ft.Text("Por favor ingrese su empresa"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return

            if not dropdown.value:
                sn = ft.SnackBar(ft.Text("Por favor seleccione una sede"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return

            if not lab_field.value:
                sn = ft.SnackBar(ft.Text("Por favor ingrese el nombre del laboratorio"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return
                
            if not fecha_field.value:
                sn = ft.SnackBar(ft.Text("Por favor seleccione una fecha"), bgcolor=ft.Colors.ORANGE)
                page.overlay.append(sn)
                sn.open = True
                page.update()
                return
            
            # Enviar datos al backend
            try:
                response = httpx.post(
                    f"{API_URL}/citas", 
                    json={
                        "nombre_paciente": nombre_field.value,
                        "cedula_paciente": cedula_field.value,
                        "sede": dropdown.value,
                        "laboratorio": lab_field.value,
                        "fecha": fecha_field.value,
                        "empresa_paciente": empresa_field.value
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    sn = ft.SnackBar(ft.Text("Cita agendada con éxito"), bgcolor=ft.Colors.GREEN)
                    page.overlay.append(sn)
                    sn.open = True
                    show_home()
                else:
                    error_msg = response.json().get("detail", "Error al agendar cita")
                    sn = ft.SnackBar(ft.Text(error_msg), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True

            except Exception as ex:
                sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)
                page.overlay.append(sn)
                sn.open = True
                
            page.update()

        def show_agendar_cita():
            page.controls.clear()
            
            # Variable para almacenar los días disponibles de la sede seleccionada
            dias_disponibles_sede = {"dias": None} # Usamos dict para poder modificar en funciones anidadas
            turnos_info = {"disponibles": None, "totales": None} # Almacenar info de turnos de sede
            turnos_empresa_info = {"disponibles": None, "totales": None} # Almacenar info de turnos de empresa
            sedes_data = {} # Diccionario para almacenar información de todas las sedes
            empresas_data = {} # Diccionario para almacenar información de todas las empresas
        
            txt_nombre = ft.TextField(
                label="Nombre Completo",
                hint_text="Ingrese su nombre completo",
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            txt_cedula = ft.TextField(
                label="Cédula",
                hint_text="Ingrese su número de documento",
                width=300,
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            empresa_dropdown = ft.Dropdown(
                label="Seleccione su EPS",
                hint_text="Cargando empresas...",
                options=[],
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            def on_sede_change(e):
                """Cuando se selecciona una sede, actualizar los días disponibles"""
                if sede_dropdown.value and sede_dropdown.value in sedes_data:
                    dias_disponibles_sede["dias"] = sedes_data[sede_dropdown.value]["dias_atencion"]
                    # Limpiar la fecha seleccionada cuando cambia la sede
                    txt_fecha.value = ""
                    txt_turnos_count.value = "" # Limpiar info de turnos
                    txt_turnos_empresa_count.value = "" # Limpiar info de turnos de empresa
                    page.update()
            
            sede_dropdown = ft.Dropdown(
                label="Seleccione su Sede",
                hint_text="Cargando sedes...",
                options=[],
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            # Asignar el evento después de crear el dropdown
            sede_dropdown.on_change = on_sede_change

            def load_empresas():
                try:
                    response = httpx.get(f"{API_URL}/empresas", timeout=5.0)
                    if response.status_code == 200:
                        empresas = response.json()
                        for e in empresas:
                            empresas_data[e["nombre"]] = e # Almacenar datos completos de la empresa
                        empresa_dropdown.options = [ft.dropdown.Option(e["nombre"]) for e in empresas]
                        empresa_dropdown.hint_text = "Escoja una empresa"
                        empresa_dropdown.update()
                except Exception as e:
                    print(f"Error loading empresas: {e}")
                    empresa_dropdown.hint_text = "Error al cargar empresas"
                    empresa_dropdown.update()



            def load_sedes():
                try:
                    response = httpx.get(f"{API_URL}/sedes", timeout=5.0)
                    if response.status_code == 200:
                        sedes = response.json()
                        # Almacenar información completa de las sedes
                        for s in sedes:
                            sedes_data[s["nombre"]] = {
                                "id": s["id"],
                                "dias_atencion": s.get("dias_atencion", "")
                            }
                        sede_dropdown.options = [ft.dropdown.Option(s["nombre"]) for s in sedes]
                        sede_dropdown.hint_text = "Escoja una sede para sus laboratorios"
                        sede_dropdown.update()
                except Exception as e:
                    print(f"Error loading sedes: {e}")
                    sede_dropdown.hint_text = "Error al cargar sedes"
                    sede_dropdown.update()
            
            lab_field = ft.TextField(
                label="Nombre del Laboratorio",
                hint_text="Ej: Hemograma, Glucosa, etc.",
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            txt_fecha = ft.TextField(
                label="Fecha de la Cita",
                hint_text="Seleccione una fecha",
                width=250,
                read_only=True,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
            )
            
            txt_turnos_count = ft.Text(
                "",
                size=14,
                color="#005288",
                weight=ft.FontWeight.W_500,
                italic=True
            )

            txt_turnos_empresa_count = ft.Text(
                "",
                size=14,
                color="#005288",
                weight=ft.FontWeight.W_500,
                italic=True
            )

            async def verificar_disponibilidad_turnos(sede_nombre, fecha_str):
                """Consulta al backend la disponibilidad de turnos"""
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{API_URL}/sedes/{sede_nombre}/turnos-disponibles",
                            params={"fecha": fecha_str},
                            timeout=5.0
                        )
                    if response.status_code == 200:
                        data = response.json()
                        turnos_info["disponibles"] = data["turnos_disponibles"]
                        turnos_info["totales"] = data["turnos_totales"]
                        
                        if data["turnos_totales"] is None:
                            txt_turnos_count.value = "✓ Cupos ilimitados disponibles"
                            txt_turnos_count.color = ft.Colors.GREEN_600
                        else:
                            txt_turnos_count.value = f"Cupos disponibles: {data['turnos_disponibles']} de {data['turnos_totales']}"
                            if data["turnos_disponibles"] > 3:
                                txt_turnos_count.color = ft.Colors.GREEN_600
                            elif data["turnos_disponibles"] > 0:
                                txt_turnos_count.color = ft.Colors.ORANGE_600
                            else:
                                txt_turnos_count.value = "⚠ No hay cupos para esta fecha"
                                txt_turnos_count.color = ft.Colors.RED_600
                        
                        txt_turnos_count.update()
                except Exception as ex:
                    print(f"Error verificando turnos: {ex}")

            async def verificar_disponibilidad_turnos_empresa(empresa_nombre, fecha_str):
                """Consulta al backend la disponibilidad de turnos por empresa"""
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{API_URL}/empresas/{empresa_nombre}/turnos-disponibles",
                            params={"fecha": fecha_str},
                            timeout=5.0
                        )
                    if response.status_code == 200:
                        data = response.json()
                        turnos_empresa_info["disponibles"] = data["turnos_disponibles"]
                        turnos_empresa_info["totales"] = data["turnos_totales"]
                        
                        if data["turnos_totales"] is None:
                            txt_turnos_empresa_count.value = "✓ Convenio: Cupos ilimitados"
                            txt_turnos_empresa_count.color = ft.Colors.GREEN_600
                        else:
                            txt_turnos_empresa_count.value = f"Empresa: {data['turnos_disponibles']} de {data['turnos_totales']} cupos"
                            if data["turnos_disponibles"] > 2:
                                txt_turnos_empresa_count.color = ft.Colors.GREEN_600
                            elif data["turnos_disponibles"] > 0:
                                txt_turnos_empresa_count.color = ft.Colors.ORANGE_600
                            else:
                                txt_turnos_empresa_count.value = "⚠ Sin cupos por convenio hoy"
                                txt_turnos_empresa_count.color = ft.Colors.RED_600
                        
                        txt_turnos_empresa_count.update()
                except Exception as ex:
                    print(f"Error verificando turnos empresa: {ex}")
            
            def es_dia_disponible(fecha):
                """Verifica si una fecha está en un día disponible según la configuración de la sede"""
                print(f"DEBUG es_dia_disponible: dias_disponibles_sede = {dias_disponibles_sede['dias']}")
                
                if not dias_disponibles_sede["dias"]:
                    # Si no hay días configurados, permitir todos
                    print("DEBUG: No hay días configurados, permitiendo todos")
                    return True
                
                # Mapeo de días en español
                dias_semana = {
                    0: "Lunes",
                    1: "Martes",
                    2: "Miércoles",
                    3: "Jueves",
                    4: "Viernes",
                    5: "Sábado",
                    6: "Domingo"
                }
                
                # Obtener el día de la semana de la fecha seleccionada
                dia_semana = dias_semana[fecha.weekday()]
                
                # Verificar si el día está en la lista de días disponibles
                dias_config = [d.strip() for d in dias_disponibles_sede["dias"].split(",")]       
                return dia_semana in dias_config

            def change_date(e):
                if date_picker.value:
                    fecha_str = date_picker.value.strftime("%Y-%m-%d")
                    
                    # Verificar si el día está disponible
                    if es_dia_disponible(date_picker.value):
                        
                        txt_fecha.value = fecha_str
                        txt_fecha.error_text = None
                        # Verificar disponibilidad de turnos si hay sede seleccionada
                        if sede_dropdown.value:
                            page.run_task(verificar_disponibilidad_turnos, sede_dropdown.value, fecha_str)
                        
                        if empresa_dropdown.value:
                            page.run_task(verificar_disponibilidad_turnos_empresa, empresa_dropdown.value, fecha_str)
                    else:
                        txt_fecha.value = ""
                        txt_fecha.error_text = "Este día no está disponible para la sede seleccionada"
                        txt_turnos_count.value = ""
                        txt_turnos_empresa_count.value = ""
                        
                        # Mostrar mensaje al usuario
                        dias_config = dias_disponibles_sede["dias"] if dias_disponibles_sede["dias"] else "No configurados"
                        sn = ft.SnackBar(
                            ft.Text(f"Día no disponible. Días permitidos: {dias_config}"),
                            bgcolor=ft.Colors.ORANGE
                        )
                        page.overlay.append(sn)
                        sn.open = True
                    
                    page.update()

            date_picker = ft.DatePicker(
                on_change=change_date,
                first_date=datetime.datetime.now(),
            )
            
            page.overlay.append(date_picker)
            
            def abrir_calendario(e):
                # Verificar que se haya seleccionado una sede primero
                if not sede_dropdown.value:
                    sn = ft.SnackBar(
                        ft.Text("Por favor seleccione una sede primero"),
                        bgcolor=ft.Colors.ORANGE
                    )
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return
                
                # Cargar los días disponibles de la sede seleccionada
                if sede_dropdown.value in sedes_data:
                    dias_disponibles_sede["dias"] = sedes_data[sede_dropdown.value]["dias_atencion"]
                    print(f"DEBUG abrir_calendario: Sede seleccionada: {sede_dropdown.value}")
                    print(f"DEBUG abrir_calendario: Días disponibles cargados: {dias_disponibles_sede['dias']}")
                else:
                    print(f"DEBUG abrir_calendario: Sede '{sede_dropdown.value}' no encontrada en sedes_data")
                
                date_picker.open = True
                page.update()

            btn_fecha = ft.IconButton(
                icon=ft.Icons.CALENDAR_TODAY,
                on_click=abrir_calendario,
                tooltip="Seleccionar Fecha"
            )
            
            fecha_container = ft.Row(
            [txt_fecha, btn_fecha],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
            )

            content = ft.Column(
                [
                    ft.Icon(ft.Icons.LOCAL_HOSPITAL_ROUNDED, size=70, color="#005288"),
                    ft.Text(
                        "Agendar Laboratorios",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color="#005288",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Diligencie el formulario para agendar su cita",
                        size=14,
                        color="#666666",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=5),
                    txt_nombre,
                    txt_cedula,
                    empresa_dropdown,
                    sede_dropdown,
                    lab_field,
                    ft.Column(
                        [
                            fecha_container,
                            txt_turnos_count,
                            txt_turnos_empresa_count
                        ],
                        spacing=5
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Confirmar Cita",
                        color=ft.Colors.WHITE,
                        bgcolor="#005288",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        width=250,
                        height=50,
                        on_click=lambda e: handle_confirmar_sede(e, sede_dropdown, lab_field, txt_nombre, txt_cedula, empresa_dropdown, txt_fecha),
                    ),
                    ft.TextButton(
                        "Volver al Inicio",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: show_home(),
                        style=ft.ButtonStyle(color="#666666"),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )

            page.add(
                ft.Container(
                    content=content,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    padding=20,
                )
            )
            page.update()
            
            # Cargar datos después de que los controles estén en la página
            load_empresas()
            load_sedes()

    def show_home_admin():
        nonlocal usr_id, usr_name
        page.controls.clear()

        def admin_card(icon, title, description, action):
            return ft.Container(
                content=ft.Column(
                [
                    ft.Icon(icon, size=60, color="#005288"),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="#005288"),
                    ft.Text(
                        description,
                        size=12,
                        color="#666666",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=15,
            width=260,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            ),
            ink=True,
            on_click=action,
        )

        # Cards del administrador
        card_dias = admin_card(
            ft.Icons.CALENDAR_TODAY,
            "Días Disponibles",
            "Configurar días habilitados para citas",
            lambda _: show_config_dias(),  
        )

        card_turnos_sede = admin_card(
            ft.Icons.LOCATION_CITY,
            "Turnos por Sede",
            "Definir cupos por sede",
            lambda _: show_turnos_sede(),
        )

        card_turnos_empresa = admin_card(
            ft.Icons.BUSINESS,
            "Turnos por Empresa",
            "Asignar cupos por empresa",
            lambda _: show_turnos_empresa(),
        )

        card_config = admin_card(
            ft.Icons.SETTINGS,
            "Configuración",
            "Parámetros generales del sistema",
            lambda _: show_configuracion(),
        )

        main_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"¡Hola {usr_name}!",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color="#005288",
                        ),
                        ft.Text(
                            "Bienvenido al panel de administración",
                            size=16,
                            color="#666666",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(top=40, bottom=30),
            ),

            ft.Row(
                [
                    card_dias,
                    card_turnos_sede,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                wrap=True,
            ),

            ft.Row(
                [
                    card_turnos_empresa,
                    card_config,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                wrap=True,
            ),

            ft.Container(
                content=ft.TextButton(
                    "Cerrar Sesión",
                    icon=ft.Icons.LOGOUT,
                    on_click=lambda _: show_login(),
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                ),
                padding=ft.padding.only(top=10),
            ),
        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

        page.add(
            ft.AppBar(
                title=ft.Text("Inicio"),
                bgcolor="#005288",
                color=ft.Colors.WHITE,
                center_title=True,
            ),
            ft.Container(
                content=main_content,
                expand=True,
                alignment=ft.Alignment(0, -0.2),
            ),
        )
        page.update()
    
        def show_config_dias():
            page.controls.clear()

            dias_semana = [
                "Lunes", "Martes", "Miércoles",
                "Jueves", "Viernes", "Sábado", "Domingo"
            ]

            checkboxes = {
                dia: ft.Checkbox(label=dia) for dia in dias_semana
            }
            
            # Diccionario para almacenar la información de las sedes (nombre -> id)
            sedes_map = {}

            sede_dropdown = ft.Dropdown(
                label="Seleccione la sede",
                width=300,
            )

            async def load_sedes():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{API_URL}/sedes", timeout=5.0)
                    if response.status_code == 200:
                        sedes = response.json()
                        # Almacenar mapeo de nombre a ID y datos completos
                        for s in sedes:
                            sedes_map[s["nombre"]] = {
                                "id": s["id"],
                                "dias_atencion": s.get("dias_atencion", "")
                            }
                        sede_dropdown.options = [ft.dropdown.Option(s["nombre"]) for s in sedes]
                        sede_dropdown.hint_text = "Seleccione una sede"
                        sede_dropdown.update()
                except Exception as e:
                    print(f"Error loading sedes: {e}")
                    sede_dropdown.hint_text = "Error al cargar sedes"
                    sede_dropdown.update()

            async def load_dias_sede(e):
                sede_nombre = sede_dropdown.value
                if not sede_nombre or sede_nombre not in sedes_map:
                    return

                try:
                    # Obtener los días guardados del mapeo
                    dias_guardados = sedes_map[sede_nombre]["dias_atencion"]
                    dias_activos = [d.strip() for d in dias_guardados.split(",")] if dias_guardados else []

                    for dia, cb in checkboxes.items():
                        cb.value = dia in dias_activos

                    page.update()
                except Exception as e:
                    print("Error cargando días:", e)

            async def guardar_dias(e):
                sede_nombre = sede_dropdown.value
                if not sede_nombre or sede_nombre not in sedes_map:
                    sn = ft.SnackBar(ft.Text("Seleccione una sede"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                dias_seleccionados = [
                    dia for dia, cb in checkboxes.items() if cb.value
                ]

                dias_string = ",".join(dias_seleccionados)
                sede_id = sedes_map[sede_nombre]["id"]

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.put(
                            f"{API_URL}/sedes/{sede_id}",
                            json={"dias_atencion": dias_string}, 
                            timeout=5
                        )

                    if response.status_code == 200:
                        # Actualizar el mapeo local
                        sedes_map[sede_nombre]["dias_atencion"] = dias_string
                        sn = ft.SnackBar(ft.Text("Días actualizados correctamente"), bgcolor=ft.Colors.GREEN)
                        # Limpiar los campos
                        sede_dropdown.value = ""
                        for cb in checkboxes.values():
                            cb.value = False
                    else:
                        error_detail = response.json().get("detail", "Error desconocido")
                        sn = ft.SnackBar(ft.Text(f"Error al guardar: {error_detail}"), bgcolor=ft.Colors.RED)

                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

                except Exception as e:
                    sn = ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

            sede_dropdown.on_change = lambda e: page.run_task(load_dias_sede, e)

            page.add(
                ft.AppBar(
                    title=ft.Text("Días de Atención"),
                    bgcolor="#005288",
                    color=ft.Colors.WHITE,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Seleccione los días habilitados para atención",
                                size=16,
                                color="#666666",
                            ),
                            sede_dropdown,
                            ft.Divider(),
                            ft.Column(list(checkboxes.values())),
                            ft.Container(height=20),
                            ft.ElevatedButton(
                                "Guardar cambios",
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                on_click=guardar_dias,
                                width=250,
                            ),
                            ft.TextButton(
                                "Volver al panel",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: show_home_admin(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=20,
                )
            )
            page.update()
            
            page.run_task(load_sedes)

        def show_turnos_sede():
            page.controls.clear()

            sede_dropdown = ft.Dropdown(
                label="Seleccione la sede",
                width=300,
            )

            txt_turnos = ft.TextField(
                label="Cantidad de turnos disponibles",
                width=300,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            # Diccionario para almacenar la información de las sedes (nombre -> dato)
            sedes_map = {}

            async def load_sedes():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{API_URL}/sedes", timeout=5.0)
                    if response.status_code == 200:
                        sedes = response.json()
                        # Almacenar mapeo de nombre a datos completos para acceso fácil
                        for s in sedes:
                            sedes_map[s["nombre"]] = {
                                "id": s["id"],
                                "cant_turnos": s.get("sd_cant_turnos")
                            }
                        sede_dropdown.options = [ft.dropdown.Option(s["nombre"]) for s in sedes]
                        sede_dropdown.hint_text = "Seleccione la sede"
                        sede_dropdown.update()
                except Exception as e:
                    print("Error cargando sedes:", e)

            async def load_turnos_sede(e):
                sede_nombre = sede_dropdown.value
                if not sede_nombre or sede_nombre not in sedes_map:
                    return

                try:
                    # Usar el valor almacenado localmente
                    cant = sedes_map[sede_nombre]["cant_turnos"]
                    txt_turnos.value = str(cant) if cant is not None else "0"
                    txt_turnos.update()
                except Exception as e:
                    print("Error cargando turnos:", e)

            async def guardar_turnos(e):
                sede_nombre = sede_dropdown.value
                if not sede_nombre or sede_nombre not in sedes_map or not txt_turnos.value:
                    sn = ft.SnackBar(ft.Text("Seleccione sede y cantidad"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                sede_id = sedes_map[sede_nombre]["id"]

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.put(
                            f"{API_URL}/sedes/{sede_id}",
                            json={"cant_turnos": int(txt_turnos.value)},
                            timeout=5
                        )

                    if response.status_code == 200:
                        # Actualizar mapa local
                        sedes_map[sede_nombre]["cant_turnos"] = int(txt_turnos.value)
                        sn = ft.SnackBar(ft.Text("Turnos actualizados correctamente"), bgcolor=ft.Colors.GREEN)
                        sede_dropdown.value = ""
                        txt_turnos.value = ""
                    else:
                        error_detail = response.json().get("detail", "Error desconocido")
                        sn = ft.SnackBar(ft.Text(f"Error al guardar: {error_detail}"), bgcolor=ft.Colors.RED)

                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

                except Exception as e:
                    sn = ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

            sede_dropdown.on_change = lambda e: page.run_task(load_turnos_sede, e)

            page.add(
                ft.AppBar(
                    title=ft.Text("Turnos por Sede"),
                    bgcolor="#005288",
                    color=ft.Colors.WHITE,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LOCATION_CITY, size=80, color="#005288"),
                            ft.Text(
                                "Turnos por Sede",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#005288",
                            ),
                            ft.Text(
                                "Configure la cantidad de turnos disponibles por sede",
                                size=16,
                                color="#666666",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=10),
                            sede_dropdown,
                            txt_turnos,
                            ft.ElevatedButton(
                                "Guardar",
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=200,
                                on_click=guardar_turnos,
                            ),
                            ft.TextButton(
                                "Volver al panel",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: show_home_admin(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                )
            )
            page.update()
            page.run_task(load_sedes)

        def show_turnos_empresa():
            page.controls.clear()

            empresa_dropdown = ft.Dropdown(
                label="Seleccione la empresa",
                width=300,
            )

            txt_turnos = ft.TextField(
                label="Cantidad máxima de turnos",
                width=300,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            # Mapeo local
            empresas_map = {}

            async def load_empresas():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{API_URL}/empresas", timeout=5.0)
                    if response.status_code == 200:
                        empresas = response.json()
                        for e in empresas:
                            empresas_map[e["nombre"]] = {
                                "id": e["id"],
                                "cant_turnos": e.get("cant_turnos")
                            }
                        empresa_dropdown.options = [ft.dropdown.Option(e["nombre"]) for e in empresas]
                        empresa_dropdown.hint_text = "Escoja una empresa"
                        empresa_dropdown.update()
                except Exception as e:
                    print(f"Error loading empresas: {e}")

            async def load_turnos_empresa(e):
                emp_nombre = empresa_dropdown.value
                if not emp_nombre or emp_nombre not in empresas_map:
                    return

                cant = empresas_map[emp_nombre]["cant_turnos"]
                txt_turnos.value = str(cant) if cant is not None else "0"
                txt_turnos.update()

            async def guardar_turnos(e):
                emp_nombre = empresa_dropdown.value
                if not emp_nombre or emp_nombre not in empresas_map or not txt_turnos.value:
                    sn = ft.SnackBar(ft.Text("Seleccione empresa y cantidad"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                emp_id = empresas_map[emp_nombre]["id"]

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.put(
                            f"{API_URL}/empresas/{emp_id}",
                            json={"cant_turnos": int(txt_turnos.value)},
                            timeout=5
                        )

                    if response.status_code == 200:
                        empresas_map[emp_nombre]["cant_turnos"] = int(txt_turnos.value)
                        sn = ft.SnackBar(ft.Text("Turnos actualizados correctamente"), bgcolor=ft.Colors.GREEN)
                        empresa_dropdown.value = ""
                        txt_turnos.value = ""
                    else:
                        sn = ft.SnackBar(ft.Text("Error al guardar"), bgcolor=ft.Colors.RED)

                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

            empresa_dropdown.on_change = lambda e: page.run_task(load_turnos_empresa, e)

            page.add(
                ft.AppBar(
                    title=ft.Text("Turnos por Empresa"),
                    bgcolor="#005288",
                    color=ft.Colors.WHITE,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.BUSINESS, size=80, color="#005288"),
                            ft.Text(
                                "Turnos por Empresa",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#005288",
                            ),
                            ft.Text(
                                "Configure la cantidad de turnos por empresa",
                                size=16,
                                color="#666666",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=10),
                            empresa_dropdown,
                            txt_turnos,
                            ft.ElevatedButton(
                                "Guardar",
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=200,
                                on_click=guardar_turnos,
                            ),
                            ft.TextButton(
                                "Volver al panel",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: show_home_admin(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                )
            )

            page.update()
            page.run_task(load_empresas)

        def show_configuracion():
            page.controls.clear()

            txt_username = ft.TextField(
                label="Nuevo nombre de usuario",
                width=300,
            )

            txt_password = ft.TextField(
                label="Nueva contraseña",
                password=True,
                can_reveal_password=True,
                width=300,
            )

            txt_password_confirm = ft.TextField(
                label="Confirmar contraseña",
                password=True,
                can_reveal_password=True,
                width=300,
            )

            def guardar_username(e):
                if not txt_username.value:
                    sn = ft.SnackBar(ft.Text("Ingrese un nombre de usuario"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                try:
                    response = httpx.put(
                        f"{API_URL}/usuarios/{usr_id}/username",
                        json={"username": txt_username.value},
                        timeout=5
                    )

                    if response.status_code == 200:
                        sn = ft.SnackBar(ft.Text("Nombre de usuario actualizado"), bgcolor=ft.Colors.GREEN)
                    else:
                        sn = ft.SnackBar(ft.Text("Error al actualizar"), bgcolor=ft.Colors.RED)
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)

                page.overlay.append(sn)
                sn.open = True
                page.update()

            def guardar_password(e):
                if not txt_password.value or not txt_password_confirm.value:
                    sn = ft.SnackBar(ft.Text("Complete ambos campos"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                if txt_password.value != txt_password_confirm.value:
                    sn = ft.SnackBar(ft.Text("Las contraseñas no coinciden"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                try:
                    response = httpx.put(
                        f"{API_URL}/usuarios/{usr_id}/password",
                        json={"password": txt_password.value},
                        timeout=5
                    )
                    if response.status_code == 200:
                        sn = ft.SnackBar(ft.Text("Contraseña actualizada"), bgcolor=ft.Colors.GREEN)
                        txt_password.value = ""
                        txt_password_confirm.value = ""
                    else:
                        sn = ft.SnackBar(ft.Text("Error al actualizar contraseña"), bgcolor=ft.Colors.RED)
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)

                page.overlay.append(sn)
                sn.open = True
                page.update()

            page.add(
                ft.AppBar(
                    title=ft.Text("Configuración"),
                    bgcolor="#005288",
                    color=ft.Colors.WHITE,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Configuración de cuenta",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#005288",
                            ),

                            ft.Divider(),

                            ft.Text("Cambiar nombre de usuario", weight=ft.FontWeight.BOLD),
                            txt_username,
                            ft.ElevatedButton(
                                "Guardar nombre",
                                on_click=lambda e: page.run_task(guardar_username, e),
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=250,
                            ),

                            ft.Divider(),

                            ft.Text("Cambiar contraseña", weight=ft.FontWeight.BOLD),
                            txt_password,
                            txt_password_confirm,
                            ft.ElevatedButton(
                                "Cambiar contraseña",
                                on_click=lambda e: page.run_task(guardar_password, e),
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=250,
                            ),

                            ft.TextButton(
                                "Volver al panel",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: show_home_admin(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    padding=20,
                ),
            )
            page.update()

    def show_home_agente():
        page.controls.clear()

        def agente_card(icon, title, description, action):
            return ft.Container(
                content=ft.Column(
                [
                    ft.Icon(icon, size=60, color="#005288"),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="#005288"),
                    ft.Text(
                        description,
                        size=12,
                        color="#666666",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=15,
            width=260,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            ),
            ink=True,
            on_click=action,
        )

        card_citas = agente_card(
            ft.Icons.CALENDAR_TODAY,
            "Gestión de Citas",
            "Gestione las citas programadas",
            lambda e: agente_citas_view()
        )

        card_config = agente_card(
            ft.Icons.SETTINGS,
            "Configuración",
            "Administre su cuenta",
            lambda e: agente_configuracion_view()
        )

        main_content = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"¡Hola {usr_name}!",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color="#005288",
                        ),
                        ft.Text(
                            "Bienvenido al panel de agente",
                            size=16,
                            color="#666666",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(top=40, bottom=30),
            ),

            ft.Row(
                [
                    card_citas,
                    card_config,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                wrap=True,
            ),

            ft.Container(
                content=ft.TextButton(
                    "Cerrar Sesión",
                    icon=ft.Icons.LOGOUT,
                    on_click=lambda _: show_login(),
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                ),
                padding=ft.padding.only(top=10),
            ),
        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

        page.add(
            ft.AppBar(
                title=ft.Text("Inicio"),
                bgcolor="#005288",
                color=ft.Colors.WHITE,
                center_title=True,
            ),
            ft.Container(
                content=main_content,
                expand=True,
                alignment=ft.Alignment(0, -0.2),
            ),
        )
        page.update()
        
        # =========================
        # GESTIÓN DE CITAS
        # =========================
        def show_crear_cita_agente_view():
            page.controls.clear()
        
            txt_nombre = ft.TextField(
                label="Nombre Completo",
                hint_text="Ingrese nombre del paciente",
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )
            
            txt_cedula = ft.TextField(
                label="Cédula",
                hint_text="Ingrese documento del paciente",
                width=300,
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )
            
            empresa_dropdown = ft.Dropdown(
                label="Seleccione Empresa",
                hint_text="Cargando empresas...",
                options=[],
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )
            
            sede_dropdown = ft.Dropdown(
                label="Seleccione Sede",
                hint_text="Cargando sedes...",
                options=[],
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )

            def load_empresas():
                try:
                    response = httpx.get(f"{API_URL}/empresas", timeout=5.0)
                    if response.status_code == 200:
                        empresas = response.json()
                        empresa_dropdown.options = [ft.dropdown.Option(e["nombre"]) for e in empresas]
                        empresa_dropdown.hint_text = "Escoja una empresa"
                        empresa_dropdown.update()
                except Exception as e:
                    print(f"Error loading empresas: {e}")
                    empresa_dropdown.hint_text = "Error al cargar empresas"
                    empresa_dropdown.update()

            def load_sedes():
                try:
                    response = httpx.get(f"{API_URL}/sedes", timeout=5.0)
                    if response.status_code == 200:
                        sedes = response.json()
                        sede_dropdown.options = [ft.dropdown.Option(s["nombre"]) for s in sedes]
                        sede_dropdown.hint_text = "Escoja una sede"
                        sede_dropdown.update()
                except Exception as e:
                    print(f"Error loading sedes: {e}")
                    sede_dropdown.hint_text = "Error al cargar sedes"
                    sede_dropdown.update()

            lab_field = ft.TextField(
                label="Nombre del Laboratorio",
                hint_text="Ej: Hemograma, Glucosa, etc.",
                width=300,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )
            
            txt_fecha = ft.TextField(
                label="Fecha de la Cita",
                hint_text="Seleccione una fecha",
                width=250,
                read_only=True,
                border_radius=10,
                border_color="#005288",
                focused_border_color="#1a5276",
                text_style=ft.TextStyle(color="black"),
            )

            def change_date(e):
                if date_picker.value:
                    txt_fecha.value = date_picker.value.strftime("%Y-%m-%d")
                    page.update()

            date_picker = ft.DatePicker(
                on_change=change_date,
                first_date=datetime.datetime.now(),
            )
            
            page.overlay.append(date_picker)
            
            def abrir_calendario(e):
                date_picker.open = True
                page.update()

            btn_fecha = ft.IconButton(
                icon=ft.Icons.CALENDAR_TODAY,
                on_click=abrir_calendario,
                tooltip="Seleccionar Fecha",
                icon_color="#005288"
            )
            
            fecha_container = ft.Row(
                [txt_fecha, btn_fecha],
                alignment=ft.MainAxisAlignment.CENTER,
            )

            def handle_crear_cita(e):
                if not txt_nombre.value or not txt_cedula.value or not empresa_dropdown.value or not sede_dropdown.value or not lab_field.value or not txt_fecha.value:
                    sn = ft.SnackBar(ft.Text("Por favor complete todos los campos"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                try:
                    response = httpx.post(
                        f"{API_URL}/citas", 
                        json={
                            "nombre_paciente": txt_nombre.value,
                            "cedula_paciente": txt_cedula.value,
                            "sede": sede_dropdown.value,
                            "laboratorio": lab_field.value,
                            "fecha": txt_fecha.value,
                            "empresa_paciente": empresa_dropdown.value
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        sn = ft.SnackBar(ft.Text("Cita creada con éxito"), bgcolor=ft.Colors.GREEN)
                        page.overlay.append(sn)
                        sn.open = True
                        agente_citas_view()
                    else:
                        error_msg = response.json().get("detail", "Error al crear cita")
                        sn = ft.SnackBar(ft.Text(error_msg), bgcolor=ft.Colors.RED)
                        page.overlay.append(sn)
                        sn.open = True
                        page.update()

                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

            content = ft.Column(
                [
                    ft.Icon(ft.Icons.NOTE_ADD_ROUNDED, size=70, color="#005288"),
                    ft.Text(
                        "Crear Nueva Cita",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color="#005288",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=5),
                    txt_nombre,
                    txt_cedula,
                    empresa_dropdown,
                    sede_dropdown,
                    lab_field,
                    fecha_container,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Crear Cita",
                        color=ft.Colors.WHITE,
                        bgcolor="#005288",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        width=250,
                        height=50,
                        on_click=handle_crear_cita,
                    ),
                    ft.TextButton(
                        "Cancelar",
                        icon=ft.Icons.CLOSE,
                        on_click=lambda _: agente_citas_view(),
                        style=ft.ButtonStyle(color=ft.Colors.RED),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )

            page.add(
                ft.Container(
                    content=content,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    padding=20,
                    bgcolor="#f0f4f7"
                )
            )
            page.update()
            
            load_empresas()
            load_sedes()

        def agente_citas_view():
            page.controls.clear()
            
            # Contenedor principal para las tarjetas, con espaciado
            citas_column = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

            def cargar_citas():
                citas_column.controls.clear()
                try:
                    response = httpx.get(f"{API_URL}/citas")
                    if response.status_code == 200:
                        citas = response.json()
                        if not citas:
                            citas_column.controls.append(
                                ft.Container(
                                    content=ft.Text("No hay citas programadas", color="#666666", size=16),
                                    alignment=ft.Alignment(0, 0),
                                    padding=40
                                )
                            )
                        else:
                            for c in citas:
                                citas_column.controls.append(cita_card(c))
                    else:
                        citas_column.controls.append(ft.Text(f"Error cargando citas: {response.text}", color="red"))
                except Exception as ex:
                    citas_column.controls.append(ft.Text(f"Error de conexión: {ex}", color="red"))

                page.update()

            def eliminar_cita(cita_id):
                try:
                    httpx.delete(f"{API_URL}/citas/{cita_id}")
                    # Mostrar confirmación visual (SnackBar)
                    sn = ft.SnackBar(ft.Text("Cita eliminada correctamente"), bgcolor=ft.Colors.GREEN)
                    page.overlay.append(sn)
                    sn.open = True
                    # Volver a la lista tras eliminar
                    agente_citas_view()
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error al eliminar: {ex}"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()

            def show_confirm_delete_view(cita_id):
                page.controls.clear()

                content = ft.Column(
                    [
                        ft.Icon(ft.Icons.WARNING_ROUNDED, size=80, color=ft.Colors.ORANGE),
                        ft.Text(
                            "¿Confirmar Eliminación?",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="#005288",
                        ),
                        ft.Text(
                            "¿Estás seguro de que deseas eliminar esta cita?\nEsta acción no se puede deshacer.",
                            size=16,
                            color="#666666",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Cancelar",
                                    bgcolor="#999999",
                                    color=ft.Colors.WHITE,
                                    on_click=lambda _: agente_citas_view(),
                                    width=150,
                                ),
                                ft.ElevatedButton(
                                    "Eliminar",
                                    bgcolor=ft.Colors.RED,
                                    color=ft.Colors.WHITE,
                                    on_click=lambda _: eliminar_cita(cita_id),
                                    width=150,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                )

                page.add(
                    ft.Container(
                        content=content,
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        padding=20,
                    )
                )
                page.update()

            def show_editar_cita_view(cita):
                page.controls.clear()

                fecha = ft.TextField(
                    label="Fecha de la Cita", 
                    value=cita["fecha"], 
                    border_radius=8,
                    border_color="#005288",
                    width=250,
                    read_only=True
                )

                def change_date(e):
                    if date_picker.value:
                        fecha.value = date_picker.value.strftime("%Y-%m-%d")
                        fecha.update()

                date_picker = ft.DatePicker(
                    on_change=change_date,
                    first_date=datetime.datetime(2023, 1, 1),
                )
                
                page.overlay.append(date_picker)

                def open_date_picker(e):
                    date_picker.open = True
                    page.update()

                btn_fecha = ft.IconButton(
                    icon=ft.Icons.CALENDAR_MONTH,
                    tooltip="Seleccionar fecha",
                    on_click=open_date_picker,
                    icon_color="#005288"
                )

                fecha_container = ft.Row(
                    [fecha, btn_fecha],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                )
                
                estado = ft.Dropdown(
                    label="Estado de la Cita",
                    value=cita.get("estado", "Pendiente"),
                    border_radius=8,
                    border_color="#005288",
                    width=300,
                    options=[
                        ft.dropdown.Option("Pendiente"),
                        ft.dropdown.Option("Confirmada"),
                        ft.dropdown.Option("Cancelada"),
                        ft.dropdown.Option("No asistió")
                    ]
                )

                def guardar(e):
                    if not fecha.value or not estado.value:
                        sn = ft.SnackBar(ft.Text("Todos los campos son obligatorios"), bgcolor=ft.Colors.ORANGE)
                        page.overlay.append(sn)
                        sn.open = True
                        page.update()
                        return

                    try:
                        response = httpx.put(
                            f"{API_URL}/citas/{cita['id']}",
                            json={
                                "fecha": fecha.value,
                                "estado": estado.value
                            },
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            sn = ft.SnackBar(ft.Text("Cita actualizada correctamente"), bgcolor=ft.Colors.GREEN)
                            page.overlay.append(sn)
                            sn.open = True
                            
                            # Volver a la lista
                            agente_citas_view()
                        else:
                            sn = ft.SnackBar(ft.Text(f"Error al guardar: {response.text}"), bgcolor=ft.Colors.RED)
                            page.overlay.append(sn)
                            sn.open = True
                            page.update()

                    except Exception as ex:
                        print(f"Error: {ex}")
                        sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)
                        page.overlay.append(sn)
                        sn.open = True
                        page.update()

                content = ft.Column(
                    [
                        ft.Icon(ft.Icons.EDIT_CALENDAR_ROUNDED, size=70, color="#005288"),
                        ft.Text(
                            "Editar Cita",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="#005288",
                        ),
                        ft.Text(f"Paciente: {cita['paciente_nombre']}", size=16, color="#666666"),
                        ft.Container(height=10),
                        fecha_container,
                        estado,
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "Guardar Cambios",
                            bgcolor="#005288",
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            width=250,
                            height=50,
                            on_click=guardar,
                        ),
                        ft.TextButton(
                            "Cancelar",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: agente_citas_view(),
                            style=ft.ButtonStyle(color=ft.Colors.RED),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                )

                page.add(
                    ft.Container(
                        content=content,
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        padding=20,
                    )
                )
                page.update()

            def cita_card(cita):
                estado_text = cita.get("estado", "Pendiente")
                
                # Colores según estado
                if estado_text == "Cancelada":
                    badge_color = ft.Colors.RED_100
                    text_color = ft.Colors.RED_900
                    icon_status = ft.Icons.CANCEL
                elif estado_text == "Confirmada":
                    badge_color = ft.Colors.GREEN_100
                    text_color = ft.Colors.GREEN_900
                    icon_status = ft.Icons.CHECK_CIRCLE
                elif estado_text == "No asistió":
                    badge_color = ft.Colors.ORANGE_100
                    text_color = ft.Colors.ORANGE_900
                    icon_status = ft.Icons.HIGHLIGHT_OFF
                else: # Pendiente
                    badge_color = ft.Colors.BLUE_100
                    text_color = ft.Colors.BLUE_900
                    icon_status = ft.Icons.SCHEDULE

                return ft.Container(
                    content=ft.Column(
                        [
                            # Header de la tarjeta: Nombre y Estado
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.PERSON, color="#005288"),
                                            ft.Text(
                                                cita['paciente_nombre'], 
                                                weight=ft.FontWeight.BOLD, 
                                                size=16,
                                                color="#1a5276"
                                            ),
                                        ],
                                        spacing=10
                                    ),
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(icon_status, size=14, color=text_color),
                                            ft.Text(estado_text, size=12, color=text_color, weight=ft.FontWeight.BOLD)
                                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                                        bgcolor=badge_color,
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        border_radius=20,
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            ft.Divider(height=1, color="#eeeeee"),
                            
                            # Detalles de la cita
                            ft.Row(
                                [
                                    ft.Column([
                                        ft.Row([ft.Icon(ft.Icons.BADGE_OUTLINED, size=16, color="#005288"), ft.Text(f"Cédula: {cita['paciente_cedula']}", size=13)]),
                                        ft.Row([ft.Icon(ft.Icons.BUSINESS, size=16, color="#005288"), ft.Text(f"Sede: {cita['sede']}", size=13)]),
                                        ft.Row([ft.Icon(ft.Icons.CORPORATE_FARE, size=16, color="#005288"), ft.Text(f"Empresa: {cita.get('empresa', 'Particular')}", size=13)]),
                                    ], spacing=5),
                                    
                                    ft.Column([
                                        ft.Row([ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED, size=16, color="#005288"), ft.Text(f"Lab: {cita['laboratorio']}", size=13)]),
                                        ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color="#005288"), ft.Text(f"Fecha: {cita['fecha']}", weight=ft.FontWeight.W_500, size=13)]),
                                    ], spacing=5),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            
                            ft.Container(height=5),
                            
                            # Botones de acción
                            ft.Row(
                                [
                                    ft.OutlinedButton(
                                        "Editar",
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda e, c=cita: show_editar_cita_view(c),
                                        style=ft.ButtonStyle(
                                            color="#005288",
                                            side=ft.BorderSide(1, "#005288")
                                        )
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED,
                                        tooltip="Eliminar cita",
                                        on_click=lambda e, cid=cita['id']: show_confirm_delete_view(cid)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            )
                        ],
                        spacing=10
                    ),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        blur_radius=10,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 4),
                    ),
                    margin=ft.margin.only(bottom=10, left=5, right=5)
                )

            # Estructura principal de la vista
            page.add(
                ft.Container(
                    expand=True,
                    bgcolor="#f0f4f7", # Fondo general suave
                    content=ft.Column(
                        [
                            # Barra superior personalizada
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK,
                                            icon_color=ft.Colors.WHITE,
                                            on_click=lambda e: show_home_agente()
                                        ),
                                        ft.Text("Gestión de Citas", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.IconButton(
                                            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                            icon_size=30,
                                            icon_color=ft.Colors.WHITE,
                                            tooltip="Crear Nueva Cita",
                                            on_click=lambda e: show_crear_cita_agente_view()
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                bgcolor="#005288",
                                padding=ft.padding.symmetric(horizontal=10, vertical=15),
                                border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
                            ),
                            
                            # Contenido con scroll
                            ft.Container(
                                content=citas_column,
                                padding=ft.padding.all(20),
                                expand=True
                            )
                        ],
                        spacing=0,
                        expand=True
                    )
                )
            )
            cargar_citas()

        # =========================
        # CONFIGURACIÓN AGENTE
        # =========================
        def agente_configuracion_view():
            page.controls.clear()

            txt_username = ft.TextField(
                label="Nuevo nombre de usuario",
                width=300,
            )

            txt_password = ft.TextField(
                label="Nueva contraseña",
                password=True,
                can_reveal_password=True,
                width=300,
            )

            txt_password_confirm = ft.TextField(
                label="Confirmar contraseña",
                password=True,
                can_reveal_password=True,
                width=300,
            )

            def guardar_username(e):
                if not txt_username.value:
                    sn = ft.SnackBar(ft.Text("Ingrese un nombre de usuario"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                try:
                    response = httpx.put(
                        f"{API_URL}/usuarios/{usr_id}/username",
                        json={"username": txt_username.value},
                        timeout=5
                    )

                    if response.status_code == 200:
                        sn = ft.SnackBar(ft.Text("Nombre de usuario actualizado"), bgcolor=ft.Colors.GREEN)
                        txt_username.value = ""
                    else:
                        sn = ft.SnackBar(ft.Text("Error al actualizar"), bgcolor=ft.Colors.RED)
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)

                page.overlay.append(sn)
                sn.open = True
                page.update()

            def guardar_password(e):
                if not txt_password.value or not txt_password_confirm.value:
                    sn = ft.SnackBar(ft.Text("Complete ambos campos"), bgcolor=ft.Colors.ORANGE)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                if txt_password.value != txt_password_confirm.value:
                    sn = ft.SnackBar(ft.Text("Las contraseñas no coinciden"), bgcolor=ft.Colors.RED)
                    page.overlay.append(sn)
                    sn.open = True
                    page.update()
                    return

                try:
                    response = httpx.put(
                        f"{API_URL}/usuarios/{usr_id}/password",
                        json={"password": txt_password.value},
                        timeout=5
                    )
                    if response.status_code == 200:
                        sn = ft.SnackBar(ft.Text("Contraseña actualizada"), bgcolor=ft.Colors.GREEN)
                        txt_password.value = ""
                        txt_password_confirm.value = ""
                    else:
                        sn = ft.SnackBar(ft.Text("Error al actualizar contraseña"), bgcolor=ft.Colors.RED)
                except Exception as ex:
                    sn = ft.SnackBar(ft.Text(f"Error de conexión: {ex}"), bgcolor=ft.Colors.RED)

                page.overlay.append(sn)
                sn.open = True
                page.update()

            page.add(
                ft.AppBar(
                    title=ft.Text("Configuración"),
                    bgcolor="#005288",
                    color=ft.Colors.WHITE,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Configuración de cuenta",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color="#005288",
                            ),

                            ft.Divider(),

                            ft.Text("Cambiar nombre de usuario", weight=ft.FontWeight.BOLD),
                            txt_username,
                            ft.ElevatedButton(
                                "Guardar nombre",
                                on_click=guardar_username,
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=250,
                            ),

                            ft.Divider(),

                            ft.Text("Cambiar contraseña", weight=ft.FontWeight.BOLD),
                            txt_password,
                            txt_password_confirm,
                            ft.ElevatedButton(
                                "Cambiar contraseña",
                                on_click=guardar_password,
                                bgcolor="#005288",
                                color=ft.Colors.WHITE,
                                width=250,
                            ),

                            ft.TextButton(
                                "Volver al panel",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=lambda _: show_home_agente(),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    padding=20,
                ),
            )
            page.update()

    show_login()

if __name__ == "__main__":
    ft.app(main, view=ft.AppView.WEB_BROWSER, port=8599, assets_dir="../imagenes")
