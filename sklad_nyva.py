import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import datetime


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def fetch_all(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            return []

    def fetch_one(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            return None

    def close(self):
        self.connection.close()

class DatabaseSetup:
    def __init__(self, db):
        self.connection = db.connection
        self.cursor = self.connection.cursor()
        self.db = db
        self.create_tables()
        

    def create_tables(self):
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS Shelves (
            shelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shelf_number INTEGER UNIQUE,
            description TEXT
        )
        """)
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """)
        
       
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS Materials (
            material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            shelf_id INTEGER,
            material_type TEXT,
            purpose INTEGER,
            date_registered TEXT,
            status TEXT,
            FOREIGN KEY (shelf_id) REFERENCES Shelves(shelf_id)
        )
        """)
       
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS DeletedMaterials (
            material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            shelf_id INTEGER,
            material_type TEXT,
            purpose INTEGER,
            date_registered TEXT,
            status TEXT,
            date_deleted TEXT,
            FOREIGN KEY (shelf_id) REFERENCES Shelves(shelf_id)
        )
        """)

       
class User:
    def __init__(self, db, username, password):
        self.db = db
        self.username = username
        self.password = password
        self.role = None

    def login(self):
        query = "SELECT role FROM Users WHERE username = ? AND password = ?"
        result = self.db.fetch_all(query, (self.username, self.password))
        if result:
            self.role = result[0][0]
            return True
        return False

    def register(self, role):
        query = "INSERT INTO Users (username, password, role) VALUES (?, ?, ?)"
        try:
            self.db.execute_query(query, (self.username, self.password, role))
            return True
        except sqlite3.IntegrityError:
            return False

    def is_admin(self):
        return self.role == "admin"

    def is_worker(self):
        return self.role == "worker"

    def is_guest(self):
        return self.role == "guest"

class WarehouseApp:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.db_setup = DatabaseSetup(self.db)
        self.show_login_screen()

    def show_login_screen(self):
        self.clear_window()
        login_window = tk.Frame(self.root)
        login_window.pack(pady=40)

        # Перевірка наявності користувачів у базі
        users_exist = self.db.fetch_one("SELECT COUNT(*) FROM Users")[0] > 0

        if not users_exist:
            tk.Label(login_window, text="Реєстрація першого адміністратора", font=("Arial", 18, "bold"), fg="red").pack(pady=20)
            tk.Button(login_window, text="Зареєструвати адміністратора", font=("Arial", 18), command=self.show_first_admin_registration, width=30, height=2, ).pack(pady=20)
        else:
            tk.Label(login_window, text="Вхід", font=("Arial", 32, "bold")).pack(pady=20)
            
            tk.Label(login_window, text="Ім'я користувача:", font=("Arial", 18)).pack(pady=10)
            self.login_username_entry = tk.Entry(login_window, font=("Arial", 18), width=40)
            self.login_username_entry.pack(pady=10)

            tk.Label(login_window, text="Пароль:", font=("Arial", 18)).pack(pady=10)
            self.login_password_entry = tk.Entry(login_window, show="*", font=("Arial", 18), width=40)
            self.login_password_entry.pack(pady=10)

            button_frame = tk.Frame(login_window)
            button_frame.pack(pady=30)

            tk.Button(button_frame, text="Вхід", font=("Arial", 18), command=self.login_user, width=15, height=2).grid(row=0, column=0, padx=20, pady=10)
            tk.Button(button_frame, text="Вхід у режимі гостя", font=("Arial", 18), 
                    command=lambda: self.guest_login(), width=22, height=2).grid(row=1, column=0, padx=20, pady=10)

        self.root.geometry("900x800")

    def show_first_admin_registration(self):
        self.clear_window()
        registration_window = tk.Frame(self.root)
        registration_window.pack(pady=40)

        tk.Label(registration_window, text="Реєстрація адміністратора", font=("Arial", 32, "bold")).pack(pady=20)

        tk.Label(registration_window, text="Ім'я користувача:", font=("Arial", 18)).pack(pady=10)
        self.first_admin_username_entry = tk.Entry(registration_window, font=("Arial", 18), width=40)
        self.first_admin_username_entry.pack(pady=10)

        tk.Label(registration_window, text="Пароль:", font=("Arial", 18)).pack(pady=10)
        self.first_admin_password_entry = tk.Entry(registration_window, show="*", font=("Arial", 18), width=40)
        self.first_admin_password_entry.pack(pady=10)

        tk.Label(registration_window, text="Роль: Адміністратор", font=("Arial", 18, "bold"), fg="blue").pack(pady=10)

        def submit_first_admin():
            username = self.first_admin_username_entry.get()
            password = self.first_admin_password_entry.get()

            if not username or not password:
                messagebox.showerror("Помилка", "Усі поля повинні бути заповнені.")
                return

            if len(password) < 8:
                messagebox.showerror("Помилка", "Пароль повинен містити мінімум 8 символів.")
                return

            try:
                self.db.execute_query(
                    "INSERT INTO Users (username, password, role) VALUES (?, ?, ?)",
                    (username, password, "admin"),
                )
                messagebox.showinfo("Успішна реєстрація", "Адміністратор успішно зареєстрований!")
                self.show_login_screen()  # Повертаємось на екран входу після реєстрації
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зареєструвати адміністратора: {e}")

        tk.Button(
            registration_window,
            text="Зареєструвати",
            font=("Arial", 18),
            command=submit_first_admin,
            width=22,
            height=2,
        ).pack(pady=20)

        tk.Label(
            registration_window,
            text="Реєстрація першого адміністратора є обов'язковою.",
            font=("Arial", 14, "bold"),
            fg="red",
        ).pack(pady=10)

        self.root.geometry("900x800")


    def show_registration_screen(self, is_first_admin=False):
        self.clear_window()
        registration_window = tk.Frame(self.root)
        registration_window.pack(pady=40)

        tk.Label(registration_window, text="Реєстрація", font=("Arial", 32, "bold")).pack(pady=20)

        tk.Label(registration_window, text="Ім'я користувача:", font=("Arial", 18)).pack(pady=10)
        self.reg_username_entry = tk.Entry(registration_window, font=("Arial", 18), width=40)
        self.reg_username_entry.pack(pady=10)

        tk.Label(registration_window, text="Пароль:", font=("Arial", 18)).pack(pady=10)
        self.reg_password_entry = tk.Entry(registration_window, show="*", font=("Arial", 18), width=40)
        self.reg_password_entry.pack(pady=10)

        if is_first_admin:
            tk.Label(registration_window, text="Роль: Адміністратор", font=("Arial", 18, "bold"), fg="blue").pack(pady=10)
        else:
            tk.Label(registration_window, text="Роль:", font=("Arial", 18)).pack(pady=10)
            self.reg_role_combo = ttk.Combobox(
                registration_window, 
                values=["Адміністратор", "Працівник"], 
                font=("Arial", 18), 
                state="readonly", 
                width=38
            )
            self.reg_role_combo.pack(pady=10)

        button_frame = tk.Frame(registration_window)
        button_frame.pack(pady=30)

        register_command = lambda: self.register_user(is_first_admin=is_first_admin)
        tk.Button(button_frame, text="Реєстрація", font=("Arial", 18), command=register_command, width=22, height=2).grid(row=0, column=0, padx=20, pady=10)

        if is_first_admin:
            tk.Button(button_frame, text="Повернутися до входу", font=("Arial", 18), command=self.show_login_screen, width=22, height=2).grid(row=0, column=1, padx=20, pady=10)
        else:
            tk.Button(button_frame, text="Повернутися в меню", font=("Arial", 18), command=self.show_main_menu, width=22, height=2).grid(row=0, column=1, padx=20, pady=10)

        self.root.geometry("900x800")


    def guest_login(self):
        self.user = User(self.db, "Гість", None)
        self.user.role = "guest"
        messagebox.showinfo("Режим гостя", "Ви ввійшли в програму як гість. Доступ лише для перегляду.")
        self.show_main_menu()

 
    def login_user(self):
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()
        self.user = User(self.db, username, password)

        if self.user.login():
            self.show_main_menu()
        else:
            messagebox.showerror("Невірні дані", "Невірне ім'я користувача або пароль.")

    def register_user(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        role = self.reg_role_combo.get()

        role_map = {
            "Адміністратор": "admin",
            "Працівник": "worker",
            "Гість": "guest"
        }
        role = role_map.get(role)  

        if not username or not password or not role:
            messagebox.showerror("Реєстрація не вдалася", "Усі поля повинні бути заповнені.")
            return

        if len(password) < 8: 
            messagebox.showerror("Реєстрація не вдалася", "Пароль повинен містити мінімум 8 символів.")
            return

        existing_user = self.db.fetch_one("SELECT * FROM Users WHERE username = ?", (username,))
        if existing_user:
            messagebox.showerror("Реєстрація не вдалася", "Ім'я користувача вже існує.")
            return

        self.user = User(self.db, username, password)
        if self.user.register(role):
            self.user.role = role 
            self.show_login_screen()
        else:
            messagebox.showerror("Реєстрація не вдалася", "Сталася помилка під час реєстрації.")


    def show_main_menu(self):
        self.clear_window()

        main_frame = tk.Frame(self.root, padx=50, pady=50)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1, minsize=400)
        main_frame.grid_columnconfigure(1, weight=1, minsize=400)

        shelf_frame = tk.Frame(main_frame)
        shelf_frame.grid(row=1, column=0, columnspan=2, pady=20)

        tk.Label(shelf_frame, text="Оберіть стелаж:", font=("Arial", 24)).grid(row=0, column=0, sticky="e", padx=20)
        self.selected_shelf_id = None
        self.selected_shelf = tk.StringVar(value="Оберіть стелаж")
        self.shelf_dropdown = ttk.Combobox(
            shelf_frame,
            textvariable=self.selected_shelf,
            font=("Arial", 20),
            state="readonly",
            width=40  
        )
        self.shelf_dropdown.grid(row=0, column=1, sticky="w", padx=20)
        self.update_shelf_list()
        self.shelf_dropdown.bind("<<ComboboxSelected>>", self.set_selected_shelf)

        self.shelf_dropdown.option_add("*TCombobox*Listbox.font", ("Arial", 16))  
        self.shelf_dropdown.option_add("*TCombobox*Listbox.height", 10)  

        button_frame = tk.Frame(main_frame, pady=30)
        button_frame.grid(row=2, column=0, columnspan=2)

        button_font = ("Arial", 20)
        button_width = 30

        tk.Button(
            button_frame,
            text="Редактор вмісту",
            font=button_font,
            width=button_width,
            command=lambda: self.open_shelf_editor(self.selected_shelf_id),
        ).grid(row=0, column=0, padx=30, pady=15)

        tk.Button(
            button_frame,
            text="Додати стелаж",
            font=button_font,
            width=button_width,
            command=self.add_shelf,
            state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED,
        ).grid(row=1, column=0, padx=30, pady=15)

        tk.Button(
            button_frame,
            text="Видалити стелаж",
            font=button_font,
            width=button_width,
            command=self.delete_shelf,
            state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED,
        ).grid(row=2, column=0, padx=30, pady=15)

        if self.user.role == "admin":
            tk.Button(
                button_frame,
                text="Зареєструвати працівника",
                font=button_font,
                width=button_width,
                command=self.show_registration_screen,
            ).grid(row=3, column=0, padx=30, pady=15)

        tk.Button(
            button_frame,
            text="Вийти з акаунту",
            font=button_font,
            width=button_width,
            command=self.show_login_screen,
        ).grid(row=4, column=0, padx=30, pady=15)

        self.root.state('zoomed') 




    def add_shelf(self):
        if not (self.user.is_admin()):
            messagebox.showwarning("Доступ заборонено", "Ця функція доступна лише для адміністратора.")
            return
        add_shelf_window = tk.Toplevel(self.root)
        add_shelf_window.title("Додати стелаж")
        add_shelf_window.geometry("600x450")  

        main_frame = tk.Frame(add_shelf_window, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Назва стелажу:", font=("Arial", 14)).pack(pady=10)
        
        shelf_name_entry = tk.Entry(main_frame, font=("Arial", 12), width=30)
        shelf_name_entry.pack(pady=10)

        def submit_shelf():
            shelf_name = shelf_name_entry.get()
            try:
                self.db.execute_query("INSERT INTO Shelves (description) VALUES (?)", (shelf_name,))
                self.update_shelf_list()
                add_shelf_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Помилка", "Стелаж з такою назвою вже існує.")

        tk.Button(main_frame, text="Підтвердити", command=submit_shelf, font=("Arial", 14), width=15).pack(pady=20)



    def select_shelf(self):
        select_shelf_window = tk.Toplevel(self.root)
        select_shelf_window.title("Вибір стелажу")

        shelves = self.db.fetch_all("SELECT shelf_id, shelf_number FROM Shelves")
        shelf_options = [f"Стелаж {shelf[1]}" for shelf in shelves]
        selected_shelf = tk.StringVar()
        selected_shelf.set(shelf_options[0])  

        tk.Label(select_shelf_window, text="Оберіть стелаж:").pack()
        tk.OptionMenu(select_shelf_window, selected_shelf, *shelf_options).pack()

        tk.Button(select_shelf_window, text="Оберіть", command=lambda: self.set_selected_shelf(selected_shelf.get())).pack()

    def delete_shelf(self):
        if not (self.user.is_admin()):
            messagebox.showwarning("Доступ заборонено", "Ця функція доступна лише для адміністратора")
            return
        if self.selected_shelf_id is None:
            messagebox.showwarning("Не обрано стелаж", "Будь ласка, оберіть стелаж для видалення.")
            return

        confirm = messagebox.askyesno("Підтвердження видалення", "Ви впевнені, що хочете видалити цей стелаж та всі дані на ньому?")
        if confirm:
            self.db.execute_query("DELETE FROM Materials WHERE shelf_id = ?", (self.selected_shelf_id,))
            self.db.execute_query("DELETE FROM Shelves WHERE shelf_id = ?", (self.selected_shelf_id,))
            self.update_shelf_list()
            self.selected_shelf_id = None
            messagebox.showinfo("Успіх", "Стелаж та його дані видалено успішно.")

            

    def update_shelf_list(self):
        shelves = self.db.fetch_all("SELECT shelf_id, description FROM Shelves")
        self.shelf_options = [shelf[1] for shelf in shelves]
        self.shelf_dropdown['values'] = self.shelf_options


    def set_selected_shelf(self, event):
        shelf_name = self.selected_shelf.get()
        result = self.db.fetch_one("SELECT shelf_id FROM Shelves WHERE description = ?", (shelf_name,))
        self.selected_shelf_id = result[0] if result else None
        

        
    def open_shelf_editor(self, shelf_id):
        editor_window = tk.Toplevel(self.root)
        editor_window.title(f"Shelf Editor - Shelf {shelf_id}")
        editor_window.geometry("1920x1020")  
        editor_window.state("zoomed") 

        top_frame = tk.Frame(editor_window)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        table_frame = tk.Frame(editor_window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("ID", "Назва", "Кількість", "Каталоговий номер", "Дата реєстру", "Статус")
        treeview = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=150, anchor="center")
        treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=treeview.yview)
        treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        view_buttons_frame = tk.Frame(top_frame)
        view_buttons_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        view_buttons_frame.grid_columnconfigure(0, weight=1, uniform="equal")
        view_buttons_frame.grid_columnconfigure(1, weight=1, uniform="equal")
        view_buttons_frame.grid_columnconfigure(2, weight=0)
        view_buttons_frame.grid_columnconfigure(3, weight=1, uniform="equal")
        view_buttons_frame.grid_columnconfigure(4, weight=0)

        search_label = tk.Label(view_buttons_frame, text="Пошук деталі:", font=("Arial", 14))
        search_label.grid(row=0, column=0, padx=10, sticky="w")
        search_entry = tk.Entry(view_buttons_frame, font=("Arial", 14))
        search_entry.grid(row=1, column=0, padx=10, sticky="ew")
        
        status_label = tk.Label(view_buttons_frame, text="Статус:", font=("Arial", 14))
        status_label.grid(row=0, column=1, padx=10, sticky="w")
        status_combobox = ttk.Combobox(view_buttons_frame, values=["Всі", "Справний", "Несправний", "Підлягає ремонту", "Очікує діагностики", "В очікуванні списання", "Списаний"], state="readonly", font=("Arial", 12))
        status_combobox.set("Всі")
        status_combobox.grid(row=1, column=1, padx=10, sticky="ew")
        
        # Розташування кнопки пошуку
        search_button = tk.Button(view_buttons_frame, text="Пошук:", command=lambda: apply_search(), font=("Arial", 14))
        search_button.grid(row=1, column=2, padx=10, sticky="ew")

        sort_label = tk.Label(view_buttons_frame, text="Сортувати за:", font=("Arial", 14))
        sort_label.grid(row=0, column=3, padx=10, sticky="w")
        sort_combobox = ttk.Combobox(view_buttons_frame, values=["Назвою", "Датою", "Статусом"], state="readonly", font=("Arial", 12))
        sort_combobox.set("Назвою")
        sort_combobox.grid(row=1, column=3, padx=10, sticky="ew")

        status_combobox.option_add("*TCombobox*Listbox.font", ("Arial", 16))  
        status_combobox.option_add("*TCombobox*Listbox.height", 10) 
        sort_combobox.option_add("*TCombobox*Listbox.font", ("Arial", 16)) 
        sort_combobox.option_add("*TCombobox*Listbox.height", 10)  

        sort_button = tk.Button(view_buttons_frame, text="Сортувати за:", command=lambda: apply_sort(), font=("Arial", 14))
        sort_button.grid(row=1, column=4, padx=10, sticky="ew")

        

        def apply_sort():
            sort_by = sort_combobox.get()

            sort_map = {
                "Назвою": "Sort by Name",
                "Датою": "Sort by Date",
                "Статусом": "Sort by Status"
            }

            sort_by = sort_map.get(sort_by)
            if sort_by is None:  
                messagebox.showerror("Помилка", "Некоректне значення для сортування.")
                return

            query = ("SELECT material_id, name, material_type, purpose, date_registered, status "
                    "FROM Materials WHERE shelf_id = ? ORDER BY ")
            query += {"Sort by Name": "name", "Sort by Date": "date_registered", "Sort by Status": "status"}[sort_by]

            try:
                materials = self.db.fetch_all(query, (shelf_id,))
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка при виконанні сортування: {e}")
                return
            for row in treeview.get_children():
                treeview.delete(row)
            for material in materials:
                treeview.insert("", tk.END, values=material)


        def apply_search():
            search_text = search_entry.get().lower()
            status_filter = status_combobox.get()

            query = "SELECT material_id, name, material_type, purpose, date_registered, status FROM Materials WHERE shelf_id = ?"
            params = [shelf_id]

            if search_text:
                query += " AND (name LIKE ? OR CAST(material_type AS TEXT) LIKE ? OR purpose LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

            if status_filter != "Всі":
                query += " AND status = ?"
                params.append(status_filter)

            materials = self.db.fetch_all(query, tuple(params))

            for row in treeview.get_children():
                treeview.delete(row)

            for material in materials:
                treeview.insert("", tk.END, values=material)

        editing_mode = tk.BooleanVar(value=False)

        def toggle_edit_mode():
            nonlocal editing_mode, edit_button
            editing_mode.set(not editing_mode.get())
            if editing_mode.get():
                edit_button.config(text="Змінити на ОГЛЯД")
                treeview.bind("<Double-1>", on_item_double_click)
            else:
                edit_button.config(text="Змінити на РЕДАГУВАННЯ")

        def on_item_double_click(event):
            if not editing_mode.get():
                return
            selected_item = treeview.selection()
            if not selected_item:
                return

            selected_item = selected_item[0]
            column = treeview.identify_column(event.x)
            col_index = int(column[1:]) - 1

            if col_index == 5: 
                status_values = ["Справний", "Несправний", "Підлягає ремонту", "Очікує діагностики", "В очікуванні списання", "Списаний"]
                combobox = ttk.Combobox(treeview, values=status_values, state="readonly")
                combobox.set(treeview.item(selected_item, "values")[col_index])

                def save_status(event):
                    new_value = combobox.get()
                    if not treeview.exists(selected_item):
                        messagebox.showerror("Помилка", "Вибраний елемент не знайдено.")
                        return

                    treeview.set(selected_item, column=column, value=new_value)
                    combobox.destroy()
                    self.changes_made = True
                    save_button.config(state=tk.NORMAL)

                combobox.bind("<Return>", save_status)
                bbox = treeview.bbox(selected_item, column)
                combobox.place(x=bbox[0], y=bbox[1], width=bbox[2])
                combobox.focus()
            else:
                entry = tk.Entry(treeview)
                entry.insert(0, treeview.item(selected_item, "values")[col_index])

                def save_entry(event):
                    new_value = entry.get()
                    treeview.set(selected_item, column=column, value=new_value)
                    entry.destroy()
                    self.changes_made = True
                    save_button.config(state=tk.NORMAL)

                entry.bind("<Return>", save_entry)
                bbox = treeview.bbox(selected_item, column)
                entry.place(x=bbox[0], y=bbox[1], width=bbox[2])
                entry.focus()

        button_frame = tk.Frame(editor_window)
        button_frame.pack(pady=20)

        left_frame = tk.Frame(button_frame)
        left_frame.grid(row=0, column=0, padx=(10, 20))  
        add_button = tk.Button(left_frame, text="Додати", state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED, font=("Arial", 14), command=lambda: self.add_material(editor_window, treeview, shelf_id))
        add_button.pack(fill=tk.X, pady=5)
        delete_button = tk.Button(left_frame, text="Видалити", state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED, font=("Arial", 14), command=lambda: delete_material())
        delete_button.pack(fill=tk.X, pady=5)

        center_frame = tk.Frame(button_frame)
        center_frame.grid(row=0, column=1, padx=(20, 20))
        edit_button = tk.Button(center_frame, text="Змінити на РЕДАГУВАННЯ", state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED, font=("Arial", 14), command=toggle_edit_mode)
        edit_button.pack(fill=tk.X, pady=5)
        save_button = tk.Button(center_frame, text="Зберегти", state=tk.DISABLED, font=("Arial", 14), command=lambda: self.save_changes(treeview))
        save_button.pack(fill=tk.X, pady=5)

        right_frame = tk.Frame(button_frame)
        right_frame.grid(row=0, column=2, padx=(20, 10))
        move_button = tk.Button(right_frame, text="Перемістити деталь", state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED, font=("Arial", 14), command=lambda: move_material())
        move_button.pack(fill=tk.X, pady=5)
        view_deleted_button = tk.Button(right_frame, text="Видалені деталі", font=("Arial", 14), command=lambda:view_deleted_materials())
        view_deleted_button.pack(fill=tk.X, pady=5)

        apply_search()




        def delete_material():
            selected_item = treeview.selection()
            if not selected_item:
                return
            material_id = treeview.item(selected_item, "values")[0]
            material = self.db.fetch_one("SELECT * FROM Materials WHERE material_id = ?", (material_id,))
            if material:
                self.db.execute_query(
                    "INSERT INTO DeletedMaterials (material_id, name, shelf_id, material_type, purpose, date_registered, status, date_deleted) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (material[0], material[1], material[2], material[3], material[4], material[5], material[6], 
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                self.db.execute_query("DELETE FROM Materials WHERE material_id = ?", (material_id,))
                
                apply_search()



       
        def move_material():
            selected_item = treeview.selection()
            if not selected_item:
                messagebox.showwarning("Помилка", "Будь ласка, виберіть деталь для переміщення.")
                return

            material_id = treeview.item(selected_item, "values")[0]

            move_window = tk.Toplevel(editor_window)
            move_window.title("Перемістити деталь")
            move_window.geometry("400x300")

            tk.Label(move_window, text="Оберіть новий стелаж:", font=("Arial", 12)).pack(pady=10)

            shelves = self.db.fetch_all("SELECT shelf_id, description FROM Shelves")
            if not shelves:
                messagebox.showerror("Помилка", "Немає доступних стелажів для переміщення.")
                move_window.destroy()
                return

            shelf_options = [f"{shelf[0]}: {shelf[1]}" for shelf in shelves]
            selected_shelf = tk.StringVar()
            selected_shelf.set(shelf_options[0]) 

            shelf_dropdown = ttk.Combobox(move_window, textvariable=selected_shelf, values=shelf_options, state="readonly")
            shelf_dropdown.pack(pady=10)

            def confirm_move():
                target_shelf_id = int(selected_shelf.get().split(":")[0])

                if target_shelf_id == shelf_id:
                    messagebox.showwarning("Помилка", "Деталь вже знаходиться на обраному стелажі.")
                    return

                try:
                    self.db.execute_query("UPDATE Materials SET shelf_id = ? WHERE material_id = ?", (target_shelf_id, material_id))
                    messagebox.showinfo("Успіх", "Деталь успішно переміщено.")
                    apply_search()  
                    move_window.destroy()
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося перемістити деталь: {e}")

            tk.Button(move_window, text="Перемістити", command=confirm_move, font=("Arial", 12)).pack(pady=20)
            tk.Button(move_window, text="Скасувати", command=move_window.destroy, font=("Arial", 12)).pack()

        

        

        def view_deleted_materials():
            deleted_window = tk.Toplevel(self.root)
            deleted_window.title("Видалені деталі")
            deleted_window.geometry("900x600")
            
            treeview_deleted = ttk.Treeview(deleted_window, columns=columns, show="headings")
            for col in columns:
                treeview_deleted.heading(col, text=col)
                treeview_deleted.column(col, width=150, anchor="center")
            treeview_deleted.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            scrollbar = ttk.Scrollbar(deleted_window, orient="vertical", command=treeview_deleted.yview)
            treeview_deleted.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            materials = self.db.fetch_all("SELECT material_id, name, material_type, purpose, date_registered, status, date_deleted FROM DeletedMaterials WHERE shelf_id = ?", (shelf_id,))
            
            for material in materials:
                treeview_deleted.insert("", tk.END, values=material)

            def restore_material():
                selected_item = treeview_deleted.selection()
                if not selected_item:
                    return

                material_id = treeview_deleted.item(selected_item, "values")[0]
                material = self.db.fetch_one("SELECT * FROM DeletedMaterials WHERE material_id = ?", (material_id,))
                if material:
                    self.db.execute_query(
                        "INSERT INTO Materials (material_id, name, shelf_id, material_type, purpose, date_registered, status) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (material[0], material[1], material[2], material[3], material[4], material[5], material[6])
                    )
                    self.db.execute_query("DELETE FROM DeletedMaterials WHERE material_id = ?", (material_id,))
                    apply_search()

            restore_button = tk.Button(deleted_window, text="Повернути деталь", state=tk.NORMAL if self.user.role in ["admin", "worker"] else tk.DISABLED, command=restore_material)
            restore_button.pack(pady=5)

        


    def save_changes(self, treeview):
        changes_made = False
        for item in treeview.get_children():
            item_values = treeview.item(item, "values")
            material_id = item_values[0]

            current_values = self.db.fetch_one(
                "SELECT name, material_type, purpose, date_registered, status FROM Materials WHERE material_id = ?",
                (material_id,)
            )

            if not current_values:
                messagebox.showwarning("Увага", f"Деталь із ID {material_id} не знайдено в базі даних. Пропускаємо.")
                continue

            changes = []
            fields = ["name", "material_type", "purpose", "date_registered", "status"]
            for idx, field in enumerate(fields):
                if current_values[idx] != item_values[idx + 1]: 
                    changes.append(f"{field}: {current_values[idx]} -> {item_values[idx + 1]}")

            if changes:
                try:
                    self.db.execute_query(
                        """
                        UPDATE Materials 
                        SET name = ?, material_type = ?, purpose = ?, date_registered = ?, status = ? 
                        WHERE material_id = ?
                        """,
                        (item_values[1], item_values[2], item_values[3], item_values[4], item_values[5], material_id),
                    )
                    changes_made = True
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося зберегти зміни для матеріалу з ID {material_id}: {e}")

    


    def add_material(self, parent_window, treeview, shelf_id):
        add_material_window = tk.Toplevel(parent_window)
        add_material_window.title("Додати деталь")
        add_material_window.geometry("800x700")

        main_frame = tk.Frame(add_material_window, padx=40, pady=40)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_columnconfigure(0, weight=1, minsize=200)
        main_frame.grid_columnconfigure(1, weight=1, minsize=300)

        tk.Label(main_frame, text="Назва:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", pady=10)
        name_entry = tk.Entry(main_frame, font=("Arial", 12), width=30)
        name_entry.grid(row=0, column=1, sticky="w", pady=10)

        tk.Label(main_frame, text="Кількість:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", pady=10)
        quantity_entry = tk.Entry(main_frame, font=("Arial", 12), width=30)
        quantity_entry.grid(row=1, column=1, sticky="w", pady=10)

        tk.Label(main_frame, text="Каталожний номер:", font=("Arial", 12)).grid(row=2, column=0, sticky="e", pady=10)
        catalog_number_entry = tk.Entry(main_frame, font=("Arial", 12), width=30)
        catalog_number_entry.grid(row=2, column=1, sticky="w", pady=10)

        tk.Label(main_frame, text="Статус:", font=("Arial", 12)).grid(row=3, column=0, sticky="e", pady=10)
        status_options = ["Справний", "Несправний", "Підлягає ремонту", "Очікує діагностики", "В очікуванні списання", "Списаний"]
        
        status_entry = ttk.Combobox(main_frame, values=status_options, font=("Arial", 12), state="readonly")
        status_entry.set(status_options[0])
        status_entry.option_add("*TCombobox*Listbox.font", ("Arial", 14)) 
        status_entry.option_add("*TCombobox*Listbox.height", 10)  
        status_entry.grid(row=3, column=1, sticky="w", pady=10)

        def submit_material():
            material_name = name_entry.get()
            quantity = quantity_entry.get()
            catalog_number = catalog_number_entry.get()
            material_status = status_entry.get()
            date_registered = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if not quantity.isdigit():
                messagebox.showwarning("Помилка", "Кількість має бути числом.")
                return
            
            if not material_name or not quantity or not catalog_number:
                messagebox.showwarning("Відсутні дані", "Будь ласка, заповніть усі поля.")
                return

            try:
                self.db.execute_query(""" 
                    INSERT INTO Materials (name, shelf_id, material_type, purpose, date_registered, status) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (material_name, shelf_id, quantity, catalog_number, date_registered, material_status))

                material_id = self.db.fetch_one("SELECT last_insert_rowid()")[0]
                treeview.insert("", tk.END, values=(material_id, material_name, quantity, catalog_number, date_registered, material_status))

                add_material_window.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Помилка", f"Не вдалося додати деталь: {e}")

        submit_button = tk.Button(main_frame, text="Додати", font=("Arial", 12), command=submit_material)
        submit_button.grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")
        

        close_button = tk.Button(main_frame, text="Закрити", font=("Arial", 12), command=add_material_window.destroy)
        close_button.grid(row=5, column=0, columnspan=2, pady=20, sticky="ew")



    


    def update_material_list(self, material_dropdown):
            materials = self.db.fetch_all("SELECT material_id, name FROM Materials")
            material_options = [f"{material[0]} {material[1]}" for material in materials]
            material_dropdown['values'] = material_options


    def clear_window(self):
            for widget in self.root.winfo_children():
                widget.destroy()

def main():
    root = tk.Tk()  
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Skald Nyva")
    db = Database("sklad_nyva.db")  
    app = WarehouseApp(root, db)  
    root.mainloop()
