import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
import re
from datetime import datetime, timedelta

try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

from logic import ScheduleSystem

class ExamSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Examtable Manager - Pro UI")
        self.root.geometry("1280x850")

        self.colors = {
            "primary": "#546e7a",
            "primary_light": "#78909c",
            "bg_main": "#eceff1",
            "bg_white": "#ffffff",
            "text_header": "#37474f",
            "text_body": "#455a64",
            "selection": "#cfd8dc",
            "accent_line": "#b0bec5",
            "success": "#27ae60",
            "danger": "#e74c3c"
        }

        self.root.configure(bg=self.colors["bg_main"])
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.system = ScheduleSystem()
        self.start_date = datetime.now().date()
        self.slot_times = []
        self.full_data = []

        self.build_layout()

    def configure_styles(self):
        self.style.configure("Treeview", background=self.colors["bg_white"],
                             fieldbackground=self.colors["bg_white"], foreground=self.colors["text_body"],
                             rowheight=35, font=('Segoe UI', 10))
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'),
                             background=self.colors["primary"], foreground=self.colors["bg_white"], relief="flat")
        self.style.map("Treeview", background=[('selected', self.colors["primary_light"])],
                       foreground=[('selected', self.colors["bg_white"])])
        self.style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'),
                             background=self.colors["primary"], foreground=self.colors["bg_white"], borderwidth=0)
        self.style.map("Accent.TButton", background=[('active', self.colors["primary_light"])])
        self.style.configure("Danger.TButton", font=('Segoe UI', 9, 'bold'),
                             background=self.colors["danger"], foreground="white", borderwidth=0)
        self.style.configure("TButton", font=('Segoe UI', 9))
        self.style.configure("TNotebook", background=self.colors["bg_main"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=('Segoe UI', 10, 'bold'), padding=[20, 10],
                             background="#cfd8dc", foreground=self.colors["text_body"])
        self.style.map("TNotebook.Tab", background=[('selected', self.colors["primary"])],
                       foreground=[('selected', self.colors["bg_white"])])

    def build_layout(self):
        header_frame = tk.Frame(self.root, bg=self.colors["bg_white"], height=80)
        header_frame.pack(fill='x', side='top')
        tk.Frame(header_frame, bg=self.colors["accent_line"], height=2).pack(side='bottom', fill='x')

        lbl_title = tk.Label(header_frame, text="EXAMTABLE MANAGER", font=('Segoe UI', 24, 'bold'),
                             bg=self.colors["bg_white"], fg=self.colors["primary"])
        lbl_title.pack(pady=20)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)

        self.tab_config = tk.Frame(self.notebook, bg=self.colors["bg_white"])
        self.tab_schedule = tk.Frame(self.notebook, bg=self.colors["bg_white"])

        self.notebook.add(self.tab_config, text="SETTINGS & DATA")
        self.notebook.add(self.tab_schedule, text="SCHEDULE (RESULT)")

        self.build_config_tab()
        self.build_schedule_tab()

        self.status_bar = tk.Label(self.root, text="System Ready", bd=1, relief=tk.FLAT, anchor=tk.W,
                                   bg="#cfd8dc", fg=self.colors["text_body"], padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def build_config_tab(self):
        container = tk.Frame(self.tab_config, bg=self.colors["bg_white"])
        container.pack(expand=True, fill='both', padx=50, pady=20)

        lf_style = {"font": ('Segoe UI', 11, 'bold'), "bg": self.colors["bg_white"],
                    "fg": self.colors["primary"], "padx": 20, "pady": 15}

        # Files
        frame_files = tk.LabelFrame(container, text="1. Data Files (CSV/TXT)", **lf_style)
        frame_files.pack(fill='x', pady=10)
        self.create_file_row(frame_files, "Classroom List:", self.imp_rooms)
        self.create_file_row(frame_files, "Course List:", self.imp_courses)
        self.create_file_row(frame_files, "Student List:", self.imp_students)

        # Settings
        frame_time = tk.LabelFrame(container, text="2. Exam Calendar Settings", **lf_style)
        frame_time.pack(fill='x', pady=10)

        row1 = tk.Frame(frame_time, bg=self.colors["bg_white"])
        row1.pack(fill='x', pady=5)

        tk.Label(row1, text="Start Date:", bg=self.colors["bg_white"], width=15, anchor='w').pack(side='left')
        if HAS_CALENDAR:
            self.ent_date = DateEntry(row1, width=15, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            self.ent_date.pack(side='left', padx=(0, 20))
        else:
            self.ent_date = ttk.Entry(row1, width=15)
            self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.ent_date.pack(side='left', padx=(0, 20))

        tk.Label(row1, text="Duration (Days):", bg=self.colors["bg_white"], width=15, anchor='w').pack(side='left')
        self.ent_days = ttk.Entry(row1, width=10)
        self.ent_days.insert(0, "7")
        self.ent_days.pack(side='left')

        # Slots
        tk.Label(frame_time, text="Exam Slots (Time Ranges):", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'bold'), anchor='w').pack(fill='x', pady=(10, 0))
        slot_frame = tk.Frame(frame_time, bg=self.colors["bg_white"])
        slot_frame.pack(fill='x', pady=5)

        self.lst_slots = tk.Listbox(slot_frame, height=5, width=35, borderwidth=1, relief="solid")
        self.lst_slots.pack(side='left', padx=(0, 10))

        default_times = ["09:00-11:00", "11:00-13:00", "13:30-15:30", "15:30-17:30"]
        for t in default_times: self.lst_slots.insert(tk.END, t)

        ctrl_frame = tk.Frame(slot_frame, bg=self.colors["bg_white"])
        ctrl_frame.pack(side='left', fill='y')

        self.ent_new_slot = ttk.Entry(ctrl_frame, width=15)
        self.ent_new_slot.insert(0, "17:30-19:30")
        self.ent_new_slot.pack(pady=(0, 5))

        ttk.Button(ctrl_frame, text="Add (+)", command=self.add_slot).pack(fill='x', pady=2)
        ttk.Button(ctrl_frame, text="Remove (-)", style="Danger.TButton", command=self.remove_slot).pack(fill='x', pady=2)
        tk.Label(ctrl_frame, text="Format: HH:MM-HH:MM", bg=self.colors["bg_white"], fg="gray", font=('Segoe UI', 8)).pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(container, bg=self.colors["bg_white"])
        btn_frame.pack(pady=20)
        self.btn_start = ttk.Button(btn_frame, text="GENERATE SCHEDULE", style="Accent.TButton", command=self.start_process)
        self.btn_start.pack(side='left', padx=10, ipadx=20, ipady=10)
        self.btn_stop = ttk.Button(btn_frame, text="STOP", command=self.stop_process, state='disabled')
        self.btn_stop.pack(side='left', padx=10, ipadx=20, ipady=10)
        self.lbl_log = tk.Label(container, text="", bg=self.colors["bg_white"], fg=self.colors["primary"])
        self.lbl_log.pack()

    def add_slot(self):
        text = self.ent_new_slot.get().strip()
        pattern = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]\s*-\s*([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(pattern, text):
            return messagebox.showerror("Invalid Format", "Please use format: HH:MM-HH:MM\nExample: 09:00-11:00")

        if text in self.lst_slots.get(0, tk.END):
            return messagebox.showwarning("Duplicate", "This slot is already in the list.")

        self.lst_slots.insert(tk.END, text)
        self.ent_new_slot.delete(0, tk.END)

    def remove_slot(self):
        selection = self.lst_slots.curselection()
        if selection: self.lst_slots.delete(selection[0])

    def create_file_row(self, parent, label_text, command_func):
        f = tk.Frame(parent, bg=self.colors["bg_white"])
        f.pack(fill='x', pady=5)
        tk.Label(f, text=label_text, width=25, anchor='w', bg=self.colors["bg_white"]).pack(side='left')
        ttk.Button(f, text="Select File...", command=command_func).pack(side='left')
        lbl_status = tk.Label(f, text="Not Selected", fg="#95a5a6", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'italic'))
        lbl_status.pack(side='left', padx=10)
        command_func.__func__.status_label = lbl_status

    def build_schedule_tab(self):
        top_bar = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"], pady=10)
        top_bar.pack(fill='x', padx=20)
        tk.Label(top_bar, text="View:", bg=self.colors["bg_white"], font=('Segoe UI', 10, 'bold')).pack(side='left')
        self.view_var = tk.StringVar(value="Daily Plan")
        cb = ttk.Combobox(top_bar, textvariable=self.view_var,
                          values=["General Schedule", "Daily Plan", "Student Based", "Classroom Based"],
                          state='readonly', width=20)
        cb.pack(side='left', padx=10)
        cb.bind("<<ComboboxSelected>>", self.refresh_table)
        ttk.Button(top_bar, text="Export CSV", command=self.export_to_csv).pack(side='right')

        tree_frame = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        scrolly = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollx = ttk.Scrollbar(tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(tree_frame, show='headings', yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        scrolly.config(command=self.tree.yview)
        scrollx.config(command=self.tree.xview)
        scrolly.pack(side="right", fill="y")
        scrollx.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        self.set_columns_daily()

    # --- ACTIONS ---
    def imp_rooms(self): self.load_file(self.imp_rooms, self.system.load_classrooms_regex)
    def imp_courses(self): self.load_file(self.imp_courses, self.system.load_courses_regex)
    def imp_students(self): self.load_file(self.imp_students, self.system.load_all_students_regex)

    def load_file(self, func_ref, system_method):
        path = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("CSV", "*.csv"), ("TXT", "*.txt")])
        if path:
            msg = system_method(path)
            if hasattr(func_ref, 'status_label'):
                fname = path.split('/')[-1]
                if "SUCCESS" in msg or "BAŞARILI" in msg:
                    color, txt = "#27ae60", f"Loaded ({fname})"
                else:
                    color, txt = "#e74c3c", "Error / Empty"
                func_ref.status_label.config(text=txt, fg=color, font=('Segoe UI', 9, 'bold'))
            self.lbl_log.config(text=msg)

    def start_process(self):
        if not self.system.courses or not self.system.classrooms:
            return messagebox.showerror("Missing Data", "Please upload required files.")
        try:
            if HAS_CALENDAR: self.start_date = self.ent_date.get_date()
            else: self.start_date = datetime.strptime(self.ent_date.get(), "%Y-%m-%d").date()

            # --- OTOMATİK SIRALAMA (SORTING) ---
            # Kullanıcı saatleri karışık girse bile (Örn: 17:00, sonra 09:00)
            # Biz bunları kronolojik sıraya diziyoruz ki algoritma bozulmasın.
            raw_slots = list(self.lst_slots.get(0, tk.END))
            if not raw_slots: return messagebox.showerror("Error", "Add at least one time slot.")

            # Saatleri parse edip sıralıyoruz
            def parse_slot(s):
                # "09:00-11:00" -> "09:00" kısmını alıp saate çevir
                start_time_str = s.split('-')[0].strip()
                return datetime.strptime(start_time_str, "%H:%M")

            # Sıralanmış listeyi kaydet
            self.slot_times = sorted(raw_slots, key=parse_slot)

            self.system.num_days = int(self.ent_days.get())
            self.system.slots_per_day = len(self.slot_times)

            self.status_bar.config(text="Calculating...")
            self.lbl_log.config(text="Process running...")
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')
            threading.Thread(target=self.run_logic, daemon=True).start()
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_process(self):
        self.system.stop_event.set()
        self.status_bar.config(text="Stopping...")
        self.lbl_log.config(text="Stopping...", fg="red")

    def run_logic(self):
        success, msg = self.system.solve()
        self.root.after(0, lambda: self.finish_solver(success, msg))

    def finish_solver(self, success, msg):
        self.status_bar.config(text=msg)
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.tab_schedule)
            self.refresh_table()
        else:
            if "Durdur" in msg or "Stopped" in msg: messagebox.showwarning("Cancelled", msg)
            else: messagebox.showerror("Failed", msg)

    # Table Helpers
    def get_real_datetime(self, d, s):
        date = self.start_date + timedelta(days=d)
        time = self.slot_times[s] if s < len(self.slot_times) else "??"
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]}) {time}"

    def get_day_and_date(self, d):
        date = self.start_date + timedelta(days=d)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return f"{date.strftime('%Y-%m-%d')} ({days[date.weekday()]})"

    def set_columns_general(self):
        cols = ["Course", "Time", "Count", "Classroom", "Capacity"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Course", width=120, anchor='center')
        self.tree.column("Time", width=250)
        self.tree.column("Count", width=80, anchor='center')
        self.tree.column("Classroom", width=150)
        self.tree.column("Capacity", width=100, anchor='center')

    def set_columns_daily(self):
        cols = ["Day", "Time", "Course", "Classroom", "Students"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Day", width=180, anchor='w')
        self.tree.column("Time", width=80, anchor='center')
        self.tree.column("Course", width=120, anchor='center')
        self.tree.column("Classroom", width=150, anchor='w')
        self.tree.column("Students", width=80, anchor='center')

    def set_columns_student(self):
        cols = ["Student", "Course", "Time", "Classroom"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Student", width=150, anchor='center')
        self.tree.column("Course", width=150, anchor='center')
        self.tree.column("Time", width=250, anchor='w')
        self.tree.column("Classroom", width=100, anchor='center')

    def set_columns_classroom(self):
        cols = ["Classroom", "Time", "Course", "Status"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Classroom", width=100, anchor='center')
        self.tree.column("Time", width=250, anchor='w')
        self.tree.column("Course", width=150, anchor='center')
        self.tree.column("Status", width=100, anchor='center')

    def refresh_table(self, event=None):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.full_data = []
        mode = self.view_var.get()

        if mode == "General Schedule":
            self.set_columns_general()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                cap = f"{st_cnt} / {sum(r.capacity for r in rooms)}"
                self.full_data.append((c_code, self.get_real_datetime(d,s), st_cnt, r_names, cap))
        elif mode == "Daily Plan":
            self.set_columns_daily()
            sorted_items = sorted(self.system.assignments.items(), key=lambda item: (item[1][0], item[1][1]))
            for c_code, (d, s, rooms) in sorted_items:
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                self.full_data.append((self.get_day_and_date(d), self.slot_times[s], c_code, r_names, st_cnt))
        elif mode == "Student Based":
            self.set_columns_student()
            temp_data = []
            for (sid, c_code), r_code in self.system.student_room_map.items():
                if c_code in self.system.assignments:
                    d, s, _ = self.system.assignments[c_code]
                    temp_data.append((sid, c_code, self.get_real_datetime(d, s), r_code))
            temp_data.sort(key=lambda x: (x[0], x[2]))
            self.full_data = temp_data
        elif mode == "Classroom Based":
            self.set_columns_classroom()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    self.full_data.append((r.code, self.get_real_datetime(d,s), c_code, "OCCUPIED"))
            self.full_data.sort()
        for row in self.full_data: self.tree.insert('', 'end', values=row)

    def export_to_csv(self):
        if not self.full_data: return messagebox.showwarning("Warning", "No data to export.")
        view_name = self.view_var.get().replace(" ", "_")
        default_name = f"Schedule_{view_name}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(self.tree['columns'])
                    writer.writerows(self.full_data)
                messagebox.showinfo("Success", f"Data exported successfully!\nPlan: {self.view_var.get()}")
            except Exception as e: messagebox.showerror("Error", f"Export failed:\n{str(e)}")