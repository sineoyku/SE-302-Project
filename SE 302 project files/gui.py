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

        lbl_title = tk.Label(title_holder, text="EXAMTABLE MANAGER", font=('Segoe UI', 24, 'bold'),
                             bg=self.colors["bg_white"], fg=self.colors["primary"])
        lbl_title.pack(side='left')
        
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

        # footer/status bar removed per user request

    def build_config_tab(self):

        bottom_area = tk.Frame(self.tab_config, bg=self.colors["bg_white"], pady=15)
        bottom_area.pack(side='bottom', fill='x')

        self.btn_start = ttk.Button(bottom_area, text="GENERATE SCHEDULE", style="Big.Accent.TButton", command=self.start_process)
        self.btn_start.pack(side='left', expand=True, padx=10, ipadx=40, ipady=10) # expand=True ile ortaladık

        self.btn_stop = ttk.Button(bottom_area, text="STOP", command=self.stop_process, state='disabled')
        self.btn_stop.pack(side='left', expand=True, padx=10, ipadx=20, ipady=10)

        self.lbl_log = tk.Label(self.tab_config, text="", bg=self.colors["bg_white"], fg=self.colors["primary"])
        self.lbl_log.pack(side='bottom', pady=(0, 5))

        # Settings area canvas (no vertical scrollbar)
        container_canvas = tk.Canvas(self.tab_config, bg=self.colors["bg_white"], highlightthickness=0)
        container_frame = tk.Frame(container_canvas, bg=self.colors["bg_white"])

        def _on_container_config(event):
            container_canvas.configure(scrollregion=container_canvas.bbox("all"))

        container_frame.bind("<Configure>", _on_container_config)
        container_canvas.create_window((0, 0), window=container_frame, anchor='nw')
        container_canvas.pack(side='left', fill='both', expand=True, padx=40, pady=20)

        lf_style = {"font": ('Segoe UI', 11, 'bold'), "bg": self.colors["bg_white"],
                    "fg": self.colors["primary"], "padx": 20, "pady": 15}

        # Two-column layout: left for settings, right for activity log
        columns_frame = tk.Frame(container_frame, bg=self.colors["bg_white"])
        columns_frame.pack(fill='both', expand=True)

        left_col = tk.Frame(columns_frame, bg=self.colors["bg_white"])
        left_col.pack(side='left', fill='both', expand=True)

        right_col = tk.Frame(columns_frame, bg=self.colors["bg_white"], width=360)
        right_col.pack(side='right', fill='y')

        frame_files = tk.LabelFrame(left_col, text="1. Data Files (CSV/TXT)", **lf_style)
        frame_files.pack(side='top', fill='x', pady=(0, 20), anchor='n')

        self.create_file_row(frame_files, "Classroom List:", self.imp_rooms)
        self.create_file_row(frame_files, "Course List:", self.imp_courses)
        self.create_file_row(frame_files, "Student List:", self.imp_students)

        frame_time = tk.LabelFrame(left_col, text="2. Exam Calendar Settings", **lf_style)
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

        # Activity log area placed in the right column
        log_frame = tk.LabelFrame(right_col, text="Activity Log", **lf_style)
        log_frame.pack(side='top', fill='both', expand=True, padx=(10, 0), pady=(0, 0))

        self.txt_log = tk.Text(log_frame, height=30, bg="#111111", fg="#e6e6e6",
                font=('Consolas', 10), wrap='word', state='disabled', padx=8, pady=6)
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = log_scroll.set
        log_scroll.pack(side='right', fill='y')
        self.txt_log.pack(side='left', fill='both', expand=True)

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
            self.append_log(f"Auto slots generated ({len(self.lst_slots.get(0, tk.END))} slots)")
        except ValueError:
            messagebox.showerror("Error", "Check time format (HH:MM) and duration.")
            self.append_log("Auto slots generation failed: invalid input")

    def remove_slot(self):
        selection = self.lst_slots.curselection()
        if selection:
            val = self.lst_slots.get(selection[0])
            self.lst_slots.delete(selection[0])
            self.append_log(f"Removed slot: {val}")
        else:
            messagebox.showwarning("Warning", "Select a slot to remove.")
            self.append_log("Remove slot attempted without selection")

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
            # Append to activity log
            try:
                fname = path.split('/')[-1]
            except:
                fname = path
            self.append_log(f"Import {fname}: {msg}")

    def start_process(self):
        if not self.system.courses or not self.system.classrooms:
            return messagebox.showerror("Missing Data", "Please upload required files.")
        try:
            self.append_log("Schedule generation requested by user")
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

            self.lbl_log.config(text="Calculating...")
            self.lbl_log.config(text="Process running...")
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')
            threading.Thread(target=self.run_logic, daemon=True).start()
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_process(self):
        self.system.stop_event.set()
        self.lbl_log.config(text="Stopping...")
        self.lbl_log.config(fg="red")
        self.append_log("Stop requested by user")

    def run_logic(self):
        success, msg = self.system.solve()
        self.root.after(0, lambda: self.finish_solver(success, msg))

    def finish_solver(self, success, msg):
        self.lbl_log.config(text=msg)
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')

        if success:
            messagebox.showinfo("Success", msg)
            self.notebook.select(self.tab_schedule)
            self.refresh_table()
            self.append_log(f"Schedule generation finished: SUCCESS - {msg}")

        else:
            if "timeout" in msg.lower():
                messagebox.showwarning(
                    "Timeout",
                    "⏱️ Schedule generation stopped.\nTime limit (10 seconds) exceeded."
                )

            elif "stopped" in msg.lower() or "durdur" in msg.lower():
                messagebox.showwarning("Cancelled", "⛔ Process stopped by user.")
                self.append_log(f"Schedule generation stopped by user: {msg}")

            else:
                messagebox.showerror("Failed", msg)
                self.append_log(f"Schedule generation failed: {msg}")


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

        # Center the table by using a 3-column grid (left spacer, center content, right spacer)
        tree_outer = tk.Frame(self.tab_schedule, bg=self.colors["bg_white"])
        tree_outer.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        tree_outer.grid_rowconfigure(0, weight=1)
        tree_outer.grid_columnconfigure(0, weight=1)
        tree_outer.grid_columnconfigure(1, weight=3)
        tree_outer.grid_columnconfigure(2, weight=1)

        center_frame = tk.Frame(tree_outer, bg=self.colors["bg_white"] )
        center_frame.grid(row=0, column=1, sticky='nsew')

        scrolly = ttk.Scrollbar(center_frame, orient="vertical")
        scrollx = ttk.Scrollbar(center_frame, orient="horizontal")
        self.tree = ttk.Treeview(center_frame, show='headings', yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        scrolly.config(command=self.tree.yview)
        scrollx.config(command=self.tree.xview)
        scrolly.pack(side="right", fill="y")
        scrollx.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        # keep references for switching views
        self.schedule_center = center_frame
        self.tree_scrolly = scrolly
        self.tree_scrollx = scrollx
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
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Time", width=300)
        self.tree.column("Count", width=100, anchor='center')
        self.tree.column("Classroom", width=200)
        self.tree.column("Capacity", width=120, anchor='center')

    def set_columns_daily(self):
        cols = ["Day", "Time", "Course", "Classroom", "Students"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Day", width=300, anchor='w')
        self.tree.column("Time", width=120, anchor='center')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Classroom", width=200, anchor='w')
        self.tree.column("Students", width=120, anchor='center')

    def set_columns_student(self):
        cols = ["Student", "Course", "Time", "Classroom"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Student", width=200, anchor='center')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Time", width=300, anchor='w')
        self.tree.column("Classroom", width=120, anchor='center')

    def set_columns_classroom(self):
        cols = ["Classroom", "Time", "Course", "Status"]
        self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("Classroom", width=150, anchor='center')
        self.tree.column("Time", width=300, anchor='w')
        self.tree.column("Course", width=200, anchor='center')
        self.tree.column("Status", width=120, anchor='center')

    def refresh_table(self, event=None):
        mode = self.view_var.get()
        # Clean up any per-view widgets from previous view (search frames, day/student frames)
        for attr in ('student_frame', 'student_search_frame', 'day_frame', 'day_search_frame'):
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    getattr(self, attr).destroy()
                    setattr(self, attr, None)
                except Exception:
                    try:
                        setattr(self, attr, None)
                    except Exception:
                        pass
        # Ensure tree is visible by default
        if hasattr(self, 'tree') and not self.tree.winfo_ismapped():
            try:
                self.tree_scrolly.pack(side="right", fill="y")
                self.tree_scrollx.pack(side="bottom", fill="x")
                self.tree.pack(side="left", fill="both", expand=True)
            except Exception:
                pass

        for i in self.tree.get_children(): self.tree.delete(i)
        self.full_data = []
        if mode == "General Schedule":
            self.set_columns_general()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                cap = f"{st_cnt} / {sum(r.capacity for r in rooms)}"
                self.full_data.append((c_code, self.get_real_datetime(d,s), st_cnt, r_names, cap))
        elif mode == "Daily Plan":
            # Build per-day selectable view: date picker + table for chosen day
            # collect assignments per date string
            from collections import defaultdict
            day_groups = defaultdict(list)
            for c_code, (d, s, rooms) in self.system.assignments.items():
                date = (self.start_date + timedelta(days=d)).strftime('%Y-%m-%d')
                time_str = self.slot_times[s] if s < len(self.slot_times) else '??'
                c = next((x for x in self.system.courses if x.code == c_code), None)
                st_cnt = len(c.students) if c else 0
                r_names = ", ".join([r.code for r in rooms])
                day_groups[date].append((time_str, c_code, r_names, st_cnt))
            # store groups for later export/use
            self.day_groups = {k: sorted(v, key=lambda x: x[0]) for k, v in day_groups.items()}

            # hide main tree
            try:
                self.tree.pack_forget()
                self.tree_scrolly.pack_forget()
                self.tree_scrollx.pack_forget()
            except Exception:
                pass

            # create date picker search in center (per-view)
            self.day_search_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
            self.day_search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(self.day_search_frame, text="Select Date:", bg=self.colors["bg_white"]).pack(side='left')
            if HAS_CALENDAR:
                dp = DateEntry(self.day_search_frame, width=12, background=self.colors["primary"], foreground='white', date_pattern='yyyy-mm-dd')
            else:
                dp = ttk.Entry(self.day_search_frame, width=12)
                dp.insert(0, self.start_date.strftime('%Y-%m-%d'))
            dp.pack(side='left', padx=(6,4))
            def _do_pick(event=None):
                try:
                    sel = dp.get()
                except Exception:
                    sel = None
                if not sel:
                    messagebox.showwarning("Select Date", "Please choose a date.")
                    return
                if sel not in self.day_groups:
                    messagebox.showwarning("No Data", f"No schedule available for {sel}.")
                    return
                self._show_day_schedule(sel)
            pick_btn = ttk.Button(self.day_search_frame, text="Search", command=_do_pick)
            pick_btn.pack(side='left', padx=(4,0))
            if HAS_CALENDAR:
                dp.bind('<Return>', _do_pick)

            # show first available day by default
            default_day = next(iter(self.day_groups.keys()), None)
            if default_day:
                try:
                    if HAS_CALENDAR:
                        dp.set_date(default_day)
                    else:
                        dp.delete(0, 'end'); dp.insert(0, default_day)
                except Exception:
                    pass
                self._show_day_schedule(default_day)
            else:
                lbl = tk.Label(self.schedule_center, text="No schedule data available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
        elif mode == "Student Based":
            # Build a searchable single-student view: show one student at a time
            temp_data = []
            for (sid, c_code), r_code in self.system.student_room_map.items():
                if c_code in self.system.assignments:
                    d, s, _ = self.system.assignments[c_code]
                    temp_data.append((sid, c_code, self.get_real_datetime(d, s), r_code))
            temp_data.sort(key=lambda x: (x[0], x[2]))
            self.full_data = temp_data

            # hide main tree
            try:
                self.tree.pack_forget()
                self.tree_scrolly.pack_forget()
                self.tree_scrollx.pack_forget()
            except Exception:
                pass

            # prepare student groups
            from collections import defaultdict
            groups = defaultdict(list)
            for sid, c_code, time_str, r_code in temp_data:
                groups[sid].append((c_code, time_str, r_code))
            self.student_groups = groups
            self.student_list_sorted = sorted(groups.keys())

            # create search frame and result area in center (per-view)
            self.student_search_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
            self.student_search_frame.pack(fill='x', padx=6, pady=(6,4))
            tk.Label(self.student_search_frame, text="Student ID:", bg=self.colors["bg_white"]).pack(side='left')
            self.search_var = tk.StringVar()
            search_entry = ttk.Entry(self.student_search_frame, textvariable=self.search_var, width=20)
            search_entry.pack(side='left', padx=(6,4))
            def _do_search(event=None):
                sid = self.search_var.get().strip()
                if not sid and self.student_list_sorted:
                    sid = self.student_list_sorted[0]
                if sid not in self.student_groups:
                    messagebox.showwarning("Not found", f"Student ID '{sid}' not found.")
                    return
                self._show_student_schedule(sid)
            search_btn = ttk.Button(self.student_search_frame, text="Search", command=_do_search)
            search_btn.pack(side='left', padx=(4,0))
            search_entry.bind('<Return>', _do_search)

            # show first student by default (if any)
            default_sid = self.student_list_sorted[0] if self.student_list_sorted else None
            if default_sid:
                self.search_var.set(default_sid)
                self._show_student_schedule(default_sid)
            else:
                lbl = tk.Label(self.schedule_center, text="No student assignments available.", bg=self.colors["bg_white"], fg=self.colors["text_body"])
                lbl.pack(pady=20)
        elif mode == "Classroom Based":
            self.set_columns_classroom()
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    self.full_data.append((r.code, self.get_real_datetime(d,s), c_code, "OCCUPIED"))
            self.full_data.sort()
        for row in self.full_data: self.tree.insert('', 'end', values=row)

    def export_to_csv(self):
        if not self.full_data: return messagebox.showwarning("Warning", "No data to export.")
        view_name = self.view_var.get()
        # If Student Based view, ask whether to export only the currently shown student
        if view_name == "Student Based":
            only_one = messagebox.askyesno("Export Options", "Export only the currently shown student (Yes) or all students (No)?")
            if only_one:
                # determine current student id from search_var or fallback
                sid = None
                if hasattr(self, 'search_var') and getattr(self, 'search_var'):
                    sid = self.search_var.get().strip()
                if not sid and hasattr(self, 'student_list_sorted') and self.student_list_sorted:
                    sid = self.student_list_sorted[0]

                if not sid:
                    return messagebox.showwarning("Warning", "No student selected to export.")

                default_name = f"Schedule_Student_{sid}.csv"
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
                if not path:
                    return
                try:
                    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f, delimiter=';')
                        cols = ["Course", "Date", "Time", "Classroom"]
                        writer.writerow(cols)
                        groups = getattr(self, 'student_groups', {})
                        for c_code, time_str, r_code in groups.get(sid, []):
                            parts = time_str.split()
                            date_part = parts[0] if parts else ""
                            time_part = parts[-1] if len(parts) > 1 else ""
                            writer.writerow([c_code, date_part, time_part, r_code])
                    messagebox.showinfo("Success", f"Student schedule exported: {sid}")
                    self.append_log(f"Exported CSV for student {sid}: {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{str(e)}")
                    self.append_log(f"Export failed: {str(e)}")
                return

        # Default: export full view data
        view_name_fname = view_name.replace(" ", "_")
        default_name = f"Schedule_{view_name_fname}.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                try:
                    cols = list(self.tree['columns'])
                    writer.writerow(cols)
                    writer.writerows(self.full_data)
                except Exception:
                    writer.writerows(self.full_data)
            messagebox.showinfo("Success", f"Data exported successfully!\nPlan: {self.view_var.get()}")
            self.append_log(f"Exported CSV: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{str(e)}")
            self.append_log(f"Export failed: {str(e)}")
            
    def show_help(self):
        help_text = """
    EXAMTABLE MANAGER - Help Menu
    TBA
    """
        messagebox.showinfo("Help", help_text)

    def append_log(self, text):
        """Append a timestamped entry to the activity log (read-only Text widget)."""
        try:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"[{ts}] {text}\n"
            self.txt_log.config(state='normal')
            self.txt_log.insert('end', entry)
            self.txt_log.see('end')
            self.txt_log.config(state='disabled')
        except Exception:
            # If log widget isn't available, fallback to status label
            try:
                self.lbl_log.config(text=text)
            except Exception:
                pass

    def _show_student_schedule(self, sid):
        """Display a single student's schedule in the center area."""
        # remove previous student widgets if present
        try:
            if hasattr(self, 'student_frame') and self.student_frame:
                self.student_frame.destroy()
        except Exception:
            pass

        # container for one student's schedule (no vertical scrollbar)
        self.student_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
        self.student_frame.pack(fill='both', expand=False, padx=6, pady=6)

        # header
        hdr = tk.Frame(self.student_frame, bg="#cfd8dc")
        hdr.pack(fill='x', padx=5, pady=(6,0))
        lbl = tk.Label(hdr, text=f"Student ID: {sid}", bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        # build student's table (height = number of exams so no empty space below)
        courses = self.student_groups.get(sid, [])
        cols = ["Course", "Date", "Time", "Classroom"]
        tbl_frame = tk.Frame(self.student_frame, bg=self.colors["bg_white"])
        tbl_frame.pack(fill='x', padx=10, pady=8)

        tbl_height = max(1, min(len(courses), 40))
        tbl = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=tbl_height)
        for c in cols:
            tbl.heading(c, text=c)
        tbl.column("Course", width=300)
        tbl.column("Date", width=140, anchor='center')
        tbl.column("Time", width=140, anchor='center')
        tbl.column("Classroom", width=160, anchor='center')

        for c_code, time_str, r_code in courses:
            # time_str format: 'YYYY-MM-DD (Weekday) HH:MM-...'
            parts = time_str.split()
            date_part = parts[0] if parts else ""
            time_part = parts[-1] if len(parts) > 1 else ""
            tbl.insert('', 'end', values=(c_code, date_part, time_part, r_code))

        # pack table so its vertical size matches rows (no expand)
        tbl.pack(fill='x')

        # ensure visible top
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass

    def _show_day_schedule(self, date_str):
        """Display a single day's schedule in the center area."""
        # remove previous day widgets if present
        try:
            if hasattr(self, 'day_frame') and self.day_frame:
                self.day_frame.destroy()
        except Exception:
            pass

        self.day_frame = tk.Frame(self.schedule_center, bg=self.colors["bg_white"])
        self.day_frame.pack(fill='both', expand=False, padx=6, pady=6)

        hdr = tk.Frame(self.day_frame, bg="#cfd8dc")
        hdr.pack(fill='x', padx=5, pady=(6,0))
        lbl = tk.Label(hdr, text=f"Date: {date_str}", bg="#cfd8dc", fg=self.colors["text_header"], font=('Segoe UI', 12, 'bold'))
        lbl.pack(side='left', padx=6, pady=6)

        # build table for day
        rows = self.day_groups.get(date_str, [])
        cols = ["Time", "Course", "Classroom", "Students"]
        tbl_frame = tk.Frame(self.day_frame, bg=self.colors["bg_white"])
        tbl_frame.pack(fill='x', padx=10, pady=8)

        tbl_height = max(1, min(len(rows), 40))
        tbl = ttk.Treeview(tbl_frame, columns=cols, show='headings', height=tbl_height)
        for c in cols:
            tbl.heading(c, text=c)
        tbl.column("Time", width=200, anchor='center')
        tbl.column("Course", width=300)
        tbl.column("Classroom", width=180, anchor='center')
        tbl.column("Students", width=100, anchor='center')

        for time_str, c_code, r_names, st_cnt in rows:
            tbl.insert('', 'end', values=(time_str, c_code, r_names, st_cnt))

        tbl.pack(fill='x')
        try:
            tbl.yview_moveto(0)
        except Exception:
            pass