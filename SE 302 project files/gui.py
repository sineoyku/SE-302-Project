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
        self.root.title("Examtable Manager - Auto & Remove Only")
        self.root.geometry("1280x900")

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

        self.style.configure("Big.Accent.TButton", font=('Segoe UI', 12, 'bold'),
                             background=self.colors["primary"], foreground=self.colors["bg_white"], borderwidth=0)
        self.style.map("Big.Accent.TButton", background=[('active', self.colors["primary_light"])])

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
        
        #help button
        help_btn = ttk.Button(header_frame, text="? Help", command=self.show_help)
        help_btn.place(relx=0.98, rely=0.5, anchor='e')
    
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

        bottom_area = tk.Frame(self.tab_config, bg=self.colors["bg_white"], pady=15)
        bottom_area.pack(side='bottom', fill='x')

        self.btn_start = ttk.Button(bottom_area, text="GENERATE SCHEDULE", style="Big.Accent.TButton", command=self.start_process)
        self.btn_start.pack(side='left', expand=True, padx=10, ipadx=40, ipady=10) # expand=True ile ortaladık

        self.btn_stop = ttk.Button(bottom_area, text="STOP", command=self.stop_process, state='disabled')
        self.btn_stop.pack(side='left', expand=True, padx=10, ipadx=20, ipady=10)

        self.lbl_log = tk.Label(self.tab_config, text="", bg=self.colors["bg_white"], fg=self.colors["primary"])
        self.lbl_log.pack(side='bottom', pady=(0, 5))

        container = tk.Frame(self.tab_config, bg=self.colors["bg_white"])
        container.pack(side='top', fill='both', expand=True, padx=40, pady=20)

        lf_style = {"font": ('Segoe UI', 11, 'bold'), "bg": self.colors["bg_white"],
                    "fg": self.colors["primary"], "padx": 20, "pady": 15}

        frame_files = tk.LabelFrame(container, text="1. Data Files (CSV/TXT)", **lf_style)
        frame_files.pack(side='top', fill='x', pady=(0, 20), anchor='n')

        self.create_file_row(frame_files, "Classroom List:", self.imp_rooms)
        self.create_file_row(frame_files, "Course List:", self.imp_courses)
        self.create_file_row(frame_files, "Student List:", self.imp_students)

        frame_time = tk.LabelFrame(container, text="2. Exam Calendar Settings", **lf_style)
        frame_time.pack(side='top', fill='both', expand=True, pady=(0, 10))

        row_date = tk.Frame(frame_time, bg=self.colors["bg_white"])
        row_date.pack(fill='x', pady=5)

        tk.Label(row_date, text="Start Date:", bg=self.colors["bg_white"], width=10, anchor='w').pack(side='left')
        if HAS_CALENDAR:
            self.ent_date = DateEntry(row_date, width=15, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            self.ent_date.pack(side='left', padx=(0, 20))
        else:
            self.ent_date = ttk.Entry(row_date, width=15)
            self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.ent_date.pack(side='left', padx=(0, 20))

        tk.Label(row_date, text="Duration (Days):", bg=self.colors["bg_white"], width=12, anchor='w').pack(side='left')
        self.ent_days = ttk.Entry(row_date, width=5)
        self.ent_days.insert(0, "7")
        self.ent_days.pack(side='left')

        tk.Label(frame_time, text="Exam Slots Generator (Auto):", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'bold'), anchor='w').pack(fill='x', pady=(15, 5))

        auto_frame = tk.Frame(frame_time, bg="#eceff1", pady=10, padx=10)
        auto_frame.pack(fill='x')

        tk.Label(auto_frame, text="Start (HH:MM):", bg="#eceff1").pack(side='left', padx=5)
        self.ent_start_hour = ttk.Entry(auto_frame, width=8)
        self.ent_start_hour.insert(0, "09:00")
        self.ent_start_hour.pack(side='left')

        tk.Label(auto_frame, text="End (HH:MM):", bg="#eceff1").pack(side='left', padx=(15, 5))
        self.ent_end_hour = ttk.Entry(auto_frame, width=8)
        self.ent_end_hour.insert(0, "17:00")
        self.ent_end_hour.pack(side='left')

        tk.Label(auto_frame, text="Slot Min:", bg="#eceff1").pack(side='left', padx=(15, 5))
        self.ent_duration_min = ttk.Entry(auto_frame, width=5)
        self.ent_duration_min.insert(0, "60")
        self.ent_duration_min.pack(side='left')

        ttk.Button(auto_frame, text="⚡ Generate Slots", command=self.generate_auto_slots).pack(side='left', padx=20)

        list_container = tk.Frame(frame_time, bg=self.colors["bg_white"])
        list_container.pack(fill='both', expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_container, orient="vertical")
        self.lst_slots = tk.Listbox(list_container, borderwidth=1, relief="solid",
                                    font=('Consolas', 11), yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lst_slots.yview)

        scrollbar.pack(side='right', fill='y')
        self.lst_slots.pack(side='left', fill='both', expand=True)

        bottom_ctrl = tk.Frame(frame_time, bg=self.colors["bg_white"])
        bottom_ctrl.pack(fill='x', pady=5)

        ttk.Button(bottom_ctrl, text="Remove Selected (-)", style="Danger.TButton", command=self.remove_slot).pack(side='right')

        default_times = ["09:00-11:00", "11:00-13:00", "13:30-15:30", "15:30-17:30"]
        for t in default_times: self.lst_slots.insert(tk.END, t)

    def generate_auto_slots(self):
        try:
            start_str = self.ent_start_hour.get().strip()
            end_str = self.ent_end_hour.get().strip()
            duration_min = int(self.ent_duration_min.get().strip())

            start_time = datetime.strptime(start_str, "%H:%M")
            end_time = datetime.strptime(end_str, "%H:%M")

            self.lst_slots.delete(0, tk.END)
            current = start_time
            while True:
                nxt = current + timedelta(minutes=duration_min)
                if nxt > end_time: break
                slot_str = f"{current.strftime('%H:%M')}-{nxt.strftime('%H:%M')}"
                self.lst_slots.insert(tk.END, slot_str)
                current = nxt
            messagebox.showinfo("Auto Fill", "Slots generated successfully.")
        except ValueError:
            messagebox.showerror("Error", "Check time format (HH:MM) and duration.")

    def remove_slot(self):
        selection = self.lst_slots.curselection()
        if selection:
            self.lst_slots.delete(selection[0])
        else:
            messagebox.showwarning("Warning", "Select a slot to remove.")

    def create_file_row(self, parent, label_text, command_func):
        f = tk.Frame(parent, bg=self.colors["bg_white"])
        f.pack(fill='x', pady=5)
        tk.Label(f, text=label_text, width=20, anchor='w', bg=self.colors["bg_white"]).pack(side='left')
        ttk.Button(f, text="Select File...", command=command_func).pack(side='left')
        lbl_status = tk.Label(f, text="Not Selected", fg="#95a5a6", bg=self.colors["bg_white"], font=('Segoe UI', 9, 'italic'))
        lbl_status.pack(side='left', padx=10)
        command_func.__func__.status_label = lbl_status

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

            raw_slots = list(self.lst_slots.get(0, tk.END))
            if not raw_slots: return messagebox.showerror("Error", "Add at least one time slot.")

            def parse_slot(s):
                start_time_str = s.split('-')[0].strip()
                return datetime.strptime(start_time_str, "%H:%M")

            self.slot_times = sorted(raw_slots, key=parse_slot)

            try:
                days_val = int(self.ent_days.get())
            except:
                days_val = 7

            self.system.num_days = days_val
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
            if "timeout" in msg.lower():
                messagebox.showwarning(
                    "Timeout",
                    "⏱️ Schedule generation stopped.\nTime limit (10 seconds) exceeded."
                )

            elif "stopped" in msg.lower() or "durdur" in msg.lower():
                messagebox.showwarning("Cancelled", "⛔ Process stopped by user.")

            else:
                messagebox.showerror("Failed", msg)


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
            
    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Examtable Manager")
        help_window.geometry("700x600")
        help_window.resizable(True, True)
        
        # Help content pages
        help_pages = {
            "index": {
                "title": "Help Menu",
                "content": "EXAMTABLE MANAGER - Help Topics\n\nClick on any topic below for detailed help:\n\n1. Uploading Data Files\n2. Setting Exam Calendar\n3. Generating Time Slots\n4. Creating Schedule\n5. Exporting Results",
                "links": [
                    ("Uploading Data Files", "upload"),
                    ("Setting Exam Calendar", "calendar"),
                    ("Generating Time Slots", "slots"),
                    ("Creating Schedule", "schedule"),
                    ("Exporting Results", "export")
                ]
            },
            "upload": {
                "title": "Uploading Data Files",
                "content": "UPLOADING DATA FILES\n\n1. Click 'Select File...' next to Classroom List\n2. Choose your CSV or TXT file\n3. Repeat for Course List and Student List\n4. Green status indicates successful upload\n\nFile Format:\n- Classroom List: classroom_code, capacity\n- Course List: course_code, student_count\n- Student List: student_id, course_code",
                "links": []
            },
            "calendar": {
                "title": "Setting Exam Calendar",
                "content": "SETTING EXAM CALENDAR\n\n1. Choose Start Date using the date picker\n2. Set Duration (number of days for exams)\n3. Click 'Generate Schedule' when ready\n\nTips:\n- Start Date: When your exams begin\n- Duration: Total number of days for all exams",
                "links": []
            },
            "slots": {
                "title": "Generating Time Slots",
                "content": "GENERATING TIME SLOTS\n\n1. Set Start Time (e.g., 09:00)\n2. Set End Time (e.g., 17:00)\n3. Set Slot Duration in minutes (e.g., 60)\n4. Click '⚡ Generate Slots'\n\nExample:\n- Start: 09:00\n- End: 17:00\n- Duration: 60 min\n- Result: 09:00-10:00, 10:00-11:00, etc.",
                "links": []
            },
            "schedule": {
                "title": "Creating Schedule",
                "content": "CREATING SCHEDULE\n\n1. Upload all required data files\n2. Configure calendar and time slots\n3. Click 'GENERATE SCHEDULE'\n\nThe system will automatically:\n- Assign courses to time slots\n- Allocate appropriate classrooms\n- Avoid scheduling conflicts\n- Respect classroom capacity\n\nView results in multiple formats after generation.",
                "links": []
            },
            "export": {
                "title": "Exporting Results",
                "content": "EXPORTING RESULTS\n\n1. Go to 'SCHEDULE (RESULT)' tab\n2. Select desired view format:\n   - General Schedule: Overview of all exams\n   - Daily Plan: Organized by day\n   - Student Based: View by student\n   - Classroom Based: View by classroom\n3. Click 'Export CSV'\n4. Choose location to save",
                "links": []
            }
        }
        
        # Current page tracking
        current_page = {"page": "index"}
        
        # Title
        title_label = tk.Label(help_window, text="Help Menu", font=('Segoe UI', 16, 'bold'),
                            bg=self.colors["bg_white"], fg=self.colors["primary"])
        title_label.pack(fill='x', padx=20, pady=15)
        
        # Content frame
        content_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(content_frame)
        scrollbar.pack(side='right', fill='y')
        
        help_text = tk.Text(content_frame, wrap='word', font=('Segoe UI', 10),
                        bg=self.colors["bg_white"], fg=self.colors["text_body"],
                        yscrollcommand=scrollbar.set, relief='flat', borderwidth=0, height=20)
        scrollbar.config(command=help_text.yview)
        help_text.pack(fill='both', expand=True)
        
        # Configure tags
        help_text.tag_configure("link", foreground="blue", underline=True)
        help_text.tag_bind("link", "<Enter>", lambda e: help_text.config(cursor="hand2"))
        help_text.tag_bind("link", "<Leave>", lambda e: help_text.config(cursor="arrow"))
        
        # Navigation frame
        nav_frame = tk.Frame(help_window, bg=self.colors["bg_white"])
        nav_frame.pack(fill='x', padx=20, pady=10)
        
        btn_back = ttk.Button(nav_frame, text="← Back to Index")
        btn_back.pack(side='left', padx=5)
        
        close_btn = ttk.Button(nav_frame, text="Close", command=help_window.destroy)
        close_btn.pack(side='right', padx=5)
        
        # Load page function
        def load_page(page_key):
            help_text.config(state='normal')
            help_text.delete('1.0', tk.END)
            
            page = help_pages.get(page_key, help_pages["index"])
            current_page["page"] = page_key
            
            # Update title
            title_label.config(text=page["title"])
            
            # Add content
            help_text.insert('end', page["content"] + "\n\n")
            
            # Add links if any
            if page["links"]:
                help_text.insert('end', "\n--- Related Topics ---\n\n")
                for link_text, link_page in page["links"]:
                    # Create unique tag for each link
                    unique_tag = f"link_{link_page}"
                    help_text.tag_configure(unique_tag, foreground="blue", underline=True)
                    help_text.tag_bind(unique_tag, "<Enter>", lambda e: help_text.config(cursor="hand2"))
                    help_text.tag_bind(unique_tag, "<Leave>", lambda e: help_text.config(cursor="arrow"))
                    help_text.tag_bind(unique_tag, "<Button-1>", lambda e, lp=link_page: load_page(lp))
                    
                    help_text.insert('end', f"• {link_text}\n", unique_tag)
            
            help_text.config(state='disabled')
            
            # Update navigation buttons
            btn_back.config(state='normal' if page_key != "index" else 'disabled')
        
        # Set back button command
        btn_back.config(command=lambda: load_page("index"))
        
        # Load initial page
        load_page("index")