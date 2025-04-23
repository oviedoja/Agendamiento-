import firebase_admin
from firebase_admin import credentials, firestore
import tkinter as tk
import tkcalendar
from tkinter import messagebox, simpledialog, ttk
from tkcalendar import Calendar
from datetime import datetime
from PIL import Image, ImageTk  # Importar Pillow para manejar imágenes
from query google firestore import FieldFilter
import os
import sys

# Detectar si el script está corriendo como .exe (PyInstaller lo almacena en _MEIPASS)
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS  # Carpeta temporal donde PyInstaller extrae archivos
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Ruta del JSON dentro del ejecutable
cred_path = os.path.join(base_dir, "json de firestore")

# Verificar que el archivo existe
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Error: No se encontró el archivo: {cred_path}")

# Inicializar Firebase
cred = credentials.Certificate("json de firestore")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Referencia a la base de datos en Firestore  
users_ref = db.collection('users')  # Referencia a la colección 'users'
appointments_ref = db.collection('appointments')  # Referencia a la colección 'appointments'


# Contraseña del administrador
ADMIN_PASSWORD = "admin123"

# Función para borrar todas las citas (solo admin)
def delete_all_appointments():
    password = simpledialog.askstring("Acceso Admin", "Ingrese la contraseña para borrar todas las citas:", show='*')
    if password == ADMIN_PASSWORD:
        confirm = messagebox.askyesno("Confirmación", "¿Está seguro de que desea borrar todas las citas?")
        if confirm:
            # Obtener todas las citas de la colección 'appointments'
            appointments_ref = db.collection('appointments')
            docs = appointments_ref.stream()
            
            # Eliminar cada documento de la colección
            for doc in docs:
                doc.reference.delete()
                
            messagebox.showinfo("Éxito", "Todas las citas han sido eliminadas.")
    else:
        messagebox.showerror("Error", "Contraseña incorrecta")

# Función para crear un usuario
def create_user():
    password = simpledialog.askstring("Admin", "Ingrese la contraseña de administrador:", show='*')
    if password != ADMIN_PASSWORD:
        messagebox.showerror("Error", "Contraseña incorrecta")
        return

    name = simpledialog.askstring("Nuevo Usuario", "Ingrese el nombre de usuario:")
    user_password = simpledialog.askstring("Nuevo Usuario", "Ingrese la contraseña:", show='*')

    if not name or not user_password:
        messagebox.showerror("Error", "El nombre y la contraseña son obligatorios")
        return
    
    # Verificar si el nombre de usuario ya existe en Firestore
    users_ref = db.collection('users')
    query = users_ref.where('name', '==', name)
    docs = list(query.stream())  # Convertir el generador a una lista para poder comprobar si hay documentos

    try:
        users_ref.add({
            'name': name,
            'password': user_password,
            })
        messagebox.showinfo("Éxito", f"Usuario '{name}' creado correctamente")

    except Exception as e: 
        messagebox.showerror("Error", f"Ha ocurrido un error: {str(e)}")
    # Verificar si se encontraron documentos
    if docs:
        messagebox.showerror("Error", "Ese nombre de usuario ya existe")
    return
# Si el usuario no existe, lo creamos

# Función para iniciar sesión
def user_login():
    global user_id, current_user_name
    name = simpledialog.askstring("Inicio de Sesión", "Ingrese su usuario:")
    password = simpledialog.askstring("Inicio de Sesión", "Ingrese su contraseña:", show='*')

    # Referencia a la colección 'users' en Firestore
    users_ref = db.collection('users')

    # Consulta para obtener el usuario con el nombre ingresado
    query = users_ref.where('name', '==', name)
    docs = query.stream()

    # Verificar si el usuario existe
    user_found = False
    for doc in docs:
        user_data = doc.to_dict()
        # Comparar la contraseña
        if user_data['password'] == password:
            user_id = doc.id  # Usamos el ID del documento como user_id
            current_user_name = user_data['name']
            messagebox.showinfo("Éxito", "Inicio de sesión exitoso")
            refresh_ui()  # Refrescar la interfaz para mostrar el nombre del usuario
            user_found = True
            break

    if not user_found:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")


# Función para refrescar la interfaz con el nombre del usuario y el botón de borrar citas
'''def refresh_ui():
    global user_name_label, delete_appointment_button
    # Actualizar la etiqueta de nombre de usuario en la interfaz
    user_name_label.config(text=f"Usuario: {current_user_name}")
    
    # Hacer visible el botón de borrar cita
    delete_appointment_button.grid(row=5, column=0, columnspan=2, pady=5)
'''  
# Agregar cita
def add_appointment():

    global user_id
    if user_id is None:
        messagebox.showerror("Error", "Debe iniciar sesión para agendar una cita")
        return
    
    date = calendar.get_date()
    time = time_combobox.get()

    if not date or not time:
        messagebox.showwarning("Error", "Debe seleccionar fecha y hora")
        return

    appointments_ref = db.collection('appointments')


    # Consultar las citas con la misma fecha y hora
    query = appointments_ref.where('date', '==', date).where('time', '==', time)
    docs = query.stream()

    #Si existe la hora salir
    for _ in docs:
        messagebox.showinfo("Error",f"Ya existe una cita agendada a las {time} para el día {date}")
        return

    appointments_ref.add({  # Se generará un ID único
        'user_id': user_id,
        'date': date,
        'time': time
    })
    messagebox.showinfo("Éxito", "Cita agendada correctamente")

# Función para ver las citas agendadas (solo admin)
def view_appointments():
    admin_window = tk.Toplevel(root)
    admin_window.title("Citas Agendadas")
    
    # Obtener todas las citas de Firebase
    appointments_ref = db.collection('appointments')
    appointments_data = appointments_ref.get()

    # Si no hay citas, muestra un mensaje
    if not appointments_data:
        messagebox.showinfo("No hay citas", "No hay citas agendadas.")
        return

    text = tk.Text(admin_window, width=50, height=20, font=("Comic Sans MS", 12), wrap=tk.WORD)
    text.pack(padx=10, pady=10)

    # Recorremos las citas obtenidas
    for appointment in appointments_data:
        appointments_data = appointment.to_dict()
        
        user_id = appointment.get('user_id')
        date = appointment.get('date')
        time = appointment.get('time')

        # Asegúrate de que las claves existen antes de usarlas
        if not user_id or not date or not time:
            text.insert(tk.END, f"ID: {appointment.id} - Datos incompletos.\n")
            continue

        # Consulta para obtener el nombre del usuario asociado
        user_ref = db.collection('users').document(user_id)
        user_data = user_ref.get()

        if user_data.exists:
            user_name = user_data.to_dict().get('name', 'Nombre no disponible')
            text.insert(tk.END, f"Usuario: {user_name}, Fecha: {date}, Hora: {time}\n")
        else:
            text.insert(tk.END, f"Usuario: Desconocido, Fecha: {date}, Hora: {time}\n")

# Nueva función para ver la base de datos de usuarios (solo admin)
def view_users():
    password = simpledialog.askstring("Acceso Admin", "Ingrese la contraseña:", show='*')
    if password != ADMIN_PASSWORD:
        messagebox.showerror("Error", "Contraseña incorrecta")
        return
    
    admin_window = tk.Toplevel(root)
    admin_window.title("Usuarios Registrados")
    
    # Obtener referencia a la colección 'users' en Firestore
    users_ref = db.collection('users')
    
    # Obtener todos los documentos en la colección 'users'
    docs = users_ref.stream()
    
    text = tk.Text(admin_window, width=50, height=20, font=("Comic Sans MS", 12), wrap=tk.WORD)
    text.pack(padx=10, pady=10)
    
    if docs:
        for doc in docs:
            user_data = doc.to_dict()  # Convertir documento a diccionario
            text.insert(tk.END, f"Nombre: {user_data['name']}, Contraseña: {user_data['password']}\n")
    else:
        text.insert(tk.END, "No hay usuarios registrados.")

# Función para ver y eliminar citas
def view_user_appointments():
    global user_id

    user_appointments_window = tk.Toplevel(root)
    user_appointments_window.title("Mis Citas")
    
    # Obtener las citas del usuario desde Firestore
    appointments_ref = db.collection('appointments').where('user_id', '==', user_id).stream()
    appointments_data = {doc.id: doc.to_dict() for doc in appointments_ref}

    # Si no hay citas, muestra un mensaje
    if not appointments_data:
        messagebox.showinfo("No hay citas", "No tienes citas agendadas.")
        user_appointments_window.destroy()
        return

    # Mostrar las citas en una lista
    appointment_listbox = tk.Listbox(user_appointments_window, width=50, height=10, font=("Comic Sans MS", 12))
    appointment_listbox.pack(padx=10, pady=10)

    # Agregar citas al Listbox
    for appointment_id, appointment in appointments_data.items():
        date = appointment.get('date', 'Fecha no disponible')
        time = appointment.get('time', 'Hora no disponible')
        appointment_listbox.insert(tk.END, f"{appointment_id} - Fecha: {date}, Hora: {time}")
    
    # Función para seleccionar y borrar la cita
    def delete_selected_appointment():
        try:
            selected_appointment = appointment_listbox.get(appointment_listbox.curselection())
            appointment_id = selected_appointment.split(' - ')[0]  # Obtener el ID de la cita seleccionada

            # Confirmación antes de eliminar
            confirm = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas eliminar esta cita?")
            if confirm:
                db.collection('appointments').document(appointment_id).delete()
                messagebox.showinfo("Éxito", "Cita eliminada correctamente.")
                user_appointments_window.destroy()
            else:
                messagebox.showinfo("Cancelado", "La cita no fue eliminada.")
        except IndexError:
            messagebox.showerror("Error", "Por favor, selecciona una cita para eliminar.")
    
    # Botón para borrar la cita seleccionada
    delete_button = tk.Button(user_appointments_window, text="Borrar Cita", font=("Comic Sans MS", 12), bg="#E74C3C", fg="white", command=delete_selected_appointment)
    delete_button.pack(pady=5)

# Agregar el botón de "Ver Mis Citas" para que el usuario vea sus citas
def create_ui():
    global root, calendar, time_combobox, user_name_label, delete_appointment_button

    root = tk.Tk()
    root.title("Agendamiento de Citas")
    root.configure(bg="#89CFF0")  # Fondo gris claro para la ventana principal

    # Titulo de la aplicación
    title_label = tk.Label(root, text="Sistema de Agendamiento de Citas", font=("Comic Sans MS", 16, "bold"), bg="#f0f0f0", fg="#4A90E2")
    title_label.grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(root, text="Fecha:", font=("Comic Sans MS", 12), bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    calendar = Calendar(root, date_pattern="yyyy-mm-dd", font=("Comic Sans MS", 12))
    calendar.grid(row=1, column=1, padx=10, pady=5)
# Interfaz gráfica
def create_ui():
    global root, calendar, time_combobox, user_name_label, delete_appointment_button, view_appointments_button, view_users_button, delete_all_appointments_button, create_user_button,add_appointment_button

    root = tk.Tk()
    root.title("Agendamiento de Citas")
    root.configure(bg="#89CFF0")

    # Cargar imagen
    image_path = "logo.png"  # Ruta de tu imagen
    image = Image.open(image_path)
    image = image.resize((80, 80), Image.Resampling.LANCZOS)  # Ajustar tamaño si es necesario
    photo = ImageTk.PhotoImage(image)

    # Agregar imagen en la esquina superior izquierda
    image_label = tk.Label(root, image=photo, bg="#89CFF0")
    image_label.grid(row=0, column=0, padx=5, pady=5, sticky="nw")  # Se posiciona en la esquina superior izquierda

    # Titulo de la aplicación
    title_label = tk.Label(root, text="Sistema de Agendamiento de Citas", font=("Comic Sans MS", 16, "bold"), bg="#89CFF0", fg="#4A90E2")
    title_label.grid(row=0, column=0, columnspan=2, pady=10)

    # Crear los botones pero no mostrarlos
    tk.Label(root, text="Fecha:", font=("Comic Sans MS", 12), bg="#4A90E2").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    calendar = Calendar(root, date_pattern="yyyy-mm-dd", font=("Comic Sans MS", 12))
    calendar.grid(row=1, column=1, padx=10, pady=5)

    hours = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]]
    tk.Label(root, text="Hora (HH:MM):", font=("Comic Sans MS", 12), bg="#4A90E2").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    time_combobox = ttk.Combobox(root, values=hours, font=("Comic Sans MS", 12))
    time_combobox.grid(row=2, column=1, padx=10, pady=5)
    time_combobox.set("08:00")

    # Etiqueta para mostrar el nombre del usuario
    user_name_label = tk.Label(root, text="Usuario: No has iniciado sesión", font=("Comic Sans MS", 12), bg="#f0f0f0")
    user_name_label.grid(row=3, column=0, columnspan=2, pady=10)
    
    # Botón de inicio de sesión
    login_button = tk.Button(root, text="Iniciar Sesión", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=user_login)
    login_button.grid(row=4, column=0, columnspan=2, pady=10)

    # Los botones que se deben ocultar inicialmente
    add_appointment_button = tk.Button(root, text="Agregar Cita", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=add_appointment)
    add_appointment_button.grid(row=5, column=0, padx=10, pady=5)
    add_appointment_button.grid_forget()  # Ocultar el botón al principio

    delete_appointment_button = tk.Button(root, text="Borrar Cita", font=("Comic Sans MS", 12), bg="#E74C3C", fg="white", command=view_user_appointments)
    delete_appointment_button.grid(row=5, column=1, padx=10, pady=5)
    delete_appointment_button.grid_forget()  # Ocultar el botón al principio

    view_appointments_button = tk.Button(root, text="Ver Citas Agendadas", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=view_appointments)
    view_appointments_button.grid(row=6, column=0, padx=10, pady=5)
    view_appointments_button.grid_forget()  # Ocultar el botón al principio

    view_users_button = tk.Button(root, text="Ver Usuarios (Admin)", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=view_users)
    view_users_button.grid(row=6, column=1, padx=10, pady=5)
    view_users_button.grid_forget()  # Ocultar el botón al principio

    delete_all_appointments_button = tk.Button(root, text="Borrar Citas (Admin)", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=delete_all_appointments)
    delete_all_appointments_button.grid(row=7, column=0, padx=10, pady=5)
    delete_all_appointments_button.grid_forget()  # Ocultar el botón al principio

    create_user_button = tk.Button(root, text="Crear Usuario (Admin)", font=("Comic Sans MS", 12), bg="#4A90E2", fg="white", command=create_user)
    create_user_button.grid(row=7, column=1, padx=10, pady=5)
    create_user_button.grid_forget()  # Ocultar el botón al principio

# Este botón de borrar solo será visible después de iniciar sesión
    delete_appointment_button = tk.Button(root, text="Borrar Cita", font=("Comic Sans MS", 12), bg="#E74C3C", fg="white", command=view_user_appointments)
    delete_appointment_button.grid(row=7, column=0, columnspan=2, pady=5)
    delete_appointment_button.grid_forget()  # Escondemos el botón hasta que el usuario inicie sesión
    

    root.mainloop()
# Función que se llama cuando el usuario inicia sesión correctamente

def refresh_ui():
    global user_name_label, delete_appointment_button, view_appointments_button, view_users_button, delete_all_appointments_button, create_user_button,add_appointment_button

    # Mostrar el nombre del usuario
    user_name_label.config(text=f"Usuario: {current_user_name}")

    # Mostrar los botones ahora que el usuario ha iniciado sesión
    add_appointment_button.grid(row=5, column=0, padx=10, pady=5)
    delete_appointment_button.grid(row=5, column=1, padx=10, pady=5)
    view_appointments_button.grid(row=6, column=0, padx=10, pady=5)
    view_users_button.grid(row=6, column=1, padx=10, pady=5)
    delete_all_appointments_button.grid(row=7, column=0, padx=10, pady=5)
    create_user_button.grid(row=7, column=1, padx=10, pady=5)

# Variable global para almacenar el ID del usuario logueado
user_id = None
current_user_name = ""

# Ejecutar UI
create_ui()
