# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from logic import ScheduleSystem

class FilterHoverWindow:
    """Small hover window for filtering a specific column with search and checkboxes."""
    def __init__(self, parent, column_name, unique_values, x, y, on_apply_callback):
        self.result = None
        self.on_apply = on_apply_callback
        self.window = tk.Toplevel(parent)
        self.window.wm_overrideredirect(True)  # Remove title bar
        self.window.wm_attributes('-topmost', True)  # Keep on top
        
        # Main frame with border
        main_frame = ttk.Frame(self.window, relief='solid', borderwidth=1)
        main_frame.pack(fill='both', expand=True)
        
        # Header with close button
        header = ttk.Frame(main_frame)
        header.pack(fill='x', padx=5, pady=3)
        ttk.Label(header, text=f"Filter: {column_name}", font=('TkDefaultFont', 9, 'bold')).pack(side='left', fill='x', expand=True)
        ttk.Button(header, text="✕", width=2, command=self.close).pack(side='right')
        
        # Search box
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', padx=5, pady=2)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_checkboxes)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(fill='x')
        
        # Checkboxes in a scrollable frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel to scroll (macOS and Windows/Linux)
        def _on_mousewheel(event):
            # macOS: event.delta is in increments of 120
            # Linux: event.num is 4 (up) or 5 (down)
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(3, "units")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-3, "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        
        # Store checkbox vars and widgets
        self.checkbox_vars = {}
        self.checkbox_widgets = {}
        self.all_values = sorted(unique_values)
        
        for val in self.all_values:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(scrollable_frame, text=str(val), variable=var)
            cb.pack(anchor='w', padx=2, pady=1, fill='x')
            self.checkbox_vars[val] = var
            self.checkbox_widgets[val] = cb
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', padx=5, pady=3)
        
        ttk.Button(btn_frame, text="OK", width=6, command=self.apply).pack(side='left', padx=1)
        ttk.Button(btn_frame, text="All", width=4, command=self.select_all).pack(side='left', padx=1)
        ttk.Button(btn_frame, text="None", width=4, command=self.deselect_all).pack(side='left', padx=1)
        
        # Update window to calculate size, then set geometry with position
        self.window.update_idletasks()
        width = min(250, self.window.winfo_reqwidth())
        height = min(300, self.window.winfo_reqheight())
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def filter_checkboxes(self, *args):
        """Show only checkboxes that match the search term."""
        search_text = self.search_var.get().upper()
        for val, widget in self.checkbox_widgets.items():
            if search_text in str(val).upper():
                widget.pack(anchor='w', padx=2, pady=1)
            else:
                widget.pack_forget()
    
    def select_all(self):
        for var in self.checkbox_vars.values():
            var.set(True)
    
    def deselect_all(self):
        for var in self.checkbox_vars.values():
            var.set(False)
    
    def apply(self):
        """Return the list of selected values and call callback."""
        self.result = [val for val, var in self.checkbox_vars.items() if var.get()]
        self.on_apply(self.result)
        self.close()
    
    def close(self):
        """Close the hover window."""
        self.window.destroy()

class ExamSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sınav Programı - Final")
        self.root.geometry("1100x800")
        self.system = ScheduleSystem()
        self.column_filters = {}  # {column_name: [allowed_values]}
        self.current_headers = []  # Track current view's headers
        self.current_data = []  # Cache the current displayed data for filtering
        self.create_menu()
        self.setup_ui()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Çıkış", command=self.root.quit)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Yardım", command=self.show_help)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        self.root.config(menu=menubar)

    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.tab_setup = ttk.Frame(notebook)
        self.tab_results = ttk.Frame(notebook)
        notebook.add(self.tab_setup, text="Veri Yükleme")
        notebook.add(self.tab_results, text="Sonuçlar")
        self.build_setup_tab()
        self.build_results_tab()
        self.notebook = notebook

    def build_setup_tab(self):
        f = ttk.Frame(self.tab_setup, padding=20)
        f.pack(fill='both', expand=True)

        lf_cfg = ttk.LabelFrame(f, text="Ayarlar", padding=10)
        lf_cfg.grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)

<<<<<<< Updated upstream
        ttk.Label(lf_cfg, text="Gün:").pack(side='left')
        self.ent_days = ttk.Entry(lf_cfg, width=5)
=======
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

        lbl_title = tk.Label(header_frame, text="EXAMTABLE MANAGER", font=('Segoe UI', 20, 'bold'),
                             bg=self.colors["bg_white"], fg=self.colors["primary"])
        lbl_title.pack(pady=20)
        
        ##help menu
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
>>>>>>> Stashed changes
        self.ent_days.insert(0, "7")
        self.ent_days.pack(side='left', padx=5)

        ttk.Label(lf_cfg, text="Slot:").pack(side='left')
        self.ent_slots = ttk.Entry(lf_cfg, width=5)
        self.ent_slots.insert(0, "5")
        self.ent_slots.pack(side='left', padx=5)

        # Checkbox KALDIRILDI

        lf_load = ttk.LabelFrame(f, text="Dosyalar", padding=10)
        lf_load.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)

        self.btn_rooms = ttk.Button(
            lf_load, text="1. SINIFLAR (AllClassrooms.csv)", command=self.imp_rooms
        )
        self.btn_rooms.pack(fill='x', pady=2)

        self.btn_courses = ttk.Button(
            lf_load, text="2. DERSLER (AttendanceLists.csv)", command=self.imp_courses
        )
        self.btn_courses.pack(fill='x', pady=2)

        self.btn_students = ttk.Button(
            lf_load, text="3. ÖĞRENCİLER (AllStudents.csv - Opsiyonel)", command=self.imp_students
        )
        self.btn_students.pack(fill='x', pady=2)

        self.log_text = tk.Text(f, height=8, bg="#f0f0f0", state='disabled')
        self.log_text.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(
            f, text="HESAPLA", command=self.start_thread
        ).grid(row=3, column=0, columnspan=2, pady=10, ipady=5, sticky='ew')

        self.prog_bar = ttk.Progressbar(f, mode='indeterminate')
        self.prog_bar.grid(row=4, column=0, columnspan=2, sticky='ew')

    def build_results_tab(self):
        f = ttk.Frame(self.tab_results)
        f.pack(fill='both', expand=True)
        ctrl = ttk.Frame(f)
        ctrl.pack(fill='x', padx=5, pady=5)

        self.view_var = tk.StringVar(value="Günlük Görünüm")
        cb = ttk.Combobox(
            ctrl,
            textvariable=self.view_var,
            values=["Günlük Görünüm", "Ders Görünümü", "Sınıf Görünümü", "Öğrenci Görünümü"],
            state='readonly'
        )
        cb.pack(side='left')
        cb.bind("<<ComboboxSelected>>", self.on_view_changed)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda n,i,m: self.refresh())
        ttk.Entry(ctrl, textvariable=self.search_var).pack(side='left', padx=5)
        ttk.Label(ctrl, text="(Filtrele)").pack(side='left')

        self.tree = ttk.Treeview(f, columns=('1','2','3','4','5'), show='headings')
        self.tree.pack(fill='both', expand=True)

        scrolly = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview)
        scrolly.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrolly.set)
        
        # Bind heading clicks to open filter popup
        self.tree.bind("<Button-1>", self.on_heading_click)

    def show_help(self):
        messagebox.showinfo(
            "Yardım",
            " Sistem Özellikleri:\n\n"
            "1. Otomatik Dengeli Dağıtım: Sınavlar günlere yayılır.\n"
            "2. Günlük 2 Sınav Limiti (Öğrenci Bazlı).\n"
            "3. Ardışık Slot Yasağı (Öğrenci Bazlı).\n"
            "4. Esnek İsimlendirme: Dosya isimleri formatı serbesttir.\n"
        )

    def on_view_changed(self, _=None):
        """Reset column filters when view changes."""
        self.column_filters = {}
        self.refresh()

    def on_heading_click(self, event):
        """Handle click on treeview heading."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "heading":
            return
        
        col_idx = self.tree.identify_column(event.x)
        if not col_idx or col_idx == "#0":
            return
        
        try:
            col_num = int(col_idx.lstrip('#')) - 1
        except ValueError:
            return
        
        if col_num >= len(self.current_headers):
            return
        
        column_name = self.current_headers[col_num]
        
        # Get all unique values for this column from cached data or tree as fallback
        unique_values = set()
        
        # First try cached data
        if self.current_data:
            for row in self.current_data:
                if col_num < len(row):
                    unique_values.add(str(row[col_num]))
        
        # If no data cached, fall back to tree items
        if not unique_values:
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                if col_num < len(values):
                    unique_values.add(str(values[col_num]))
        
        if not unique_values:
            messagebox.showinfo("Info", "No data in this column.")
            return
        
        # Calculate position for hover window using event coordinates
        x = event.x_root + 10
        y = event.y_root + 20
        
        # Create callback function
        def apply_filter(result):
            self.column_filters[column_name] = result
            self.refresh()
        
        # Open filter hover window
        try:
            FilterHoverWindow(self.root, column_name, unique_values, x, y, apply_filter)
        except Exception as e:
            print(f"Error opening filter window: {e}")
            import traceback
            traceback.print_exc()

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, "> " + str(msg) + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def imp_rooms(self):
        p = filedialog.askopenfilename()
        if p: self.log(self.system.load_classrooms_regex(p))

    def imp_courses(self):
        p = filedialog.askopenfilename()
        if p: self.log(self.system.load_courses_regex(p))

    def imp_students(self):
        p = filedialog.askopenfilename()
        if p: self.log(self.system.load_all_students_regex(p))

    def start_thread(self):
        if not self.system.courses:
            return messagebox.showerror("Hata", "Dersler eksik!")

        try:
            d_val = int(self.ent_days.get())
            s_val = int(self.ent_slots.get())
            self.system.num_days = d_val
            self.system.slots_per_day = s_val
            self.log(f"Hesaplama: {d_val} Gün, {s_val} Slot (Dengeli Dağıtım)...")

        except ValueError:
            return messagebox.showerror("Hata", "Lütfen sayı girin!")

        self.prog_bar.start(10)
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        success, msg = self.system.solve()
        self.root.after(0, lambda: self.finish(success, msg))

    def finish(self, success, msg):
        self.prog_bar.stop()
        self.log(msg)
        if success:
            messagebox.showinfo("Bitti", msg)
            self.notebook.select(self.tab_results)
            self.refresh()
        else:
            messagebox.showerror("Hata", msg)

    def refresh(self, _=None):
        """Rebuild table with current data and filters applied."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        mode = self.view_var.get()
        flt = self.search_var.get().upper()
        data = []

        if mode == "Günlük Görünüm":
            headers = ["Gün", "Slot", "Ders Kodu", "Sınıflar", "Mevcut"]
            all_assignments = []
            for c_code, (d, s, rooms) in self.system.assignments.items():
                if flt and flt not in c_code:
                    continue
                room_names = " + ".join([r.code for r in rooms])
                course_obj = next((c for c in self.system.courses if c.code == c_code), None)
                st_count = len(course_obj.students) if course_obj else 0
                all_assignments.append((d, s, c_code, room_names, st_count))

            all_assignments.sort(key=lambda x: (x[0], x[1]))
            for (d, s, c_code, r_names, count) in all_assignments:
                data.append((f"Gün {d+1}", f"Slot {s+1}", c_code, r_names, count))

        elif mode == "Ders Görünümü":
            headers = ["Ders Kodu", "Mevcut / Top. Kapasite", "Zaman", "Atanan Sınıflar", "-"]
            for c_code, (d, s, rooms) in self.system.assignments.items():
                if flt and flt not in c_code:
                    continue
                room_names = " + ".join([r.code for r in rooms])
                total_cap = sum(r.capacity for r in rooms)
                course_obj = next((c for c in self.system.courses if c.code == c_code), None)
                st_count = len(course_obj.students) if course_obj else 0
                data.append((c_code, f"{st_count} / {total_cap}", f"G{d+1}/S{s+1}", room_names, ""))

        elif mode == "Sınıf Görünümü":
            headers = ["Sınıf", "Ders", "Zaman", "Durum", "-"]
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    if flt and flt not in r.code:
                        continue
                    data.append((r.code, c_code, f"G{d+1}/S{s+1}", "Dolu", ""))

<<<<<<< Updated upstream
        elif mode == "Öğrenci Görünümü":
            headers = ["Öğrenci ID", "Ders", "Zaman", "GİDECEĞİ SINIF", "Durum"]
            all_st = sorted(list(self.system.all_students_list))
            if not all_st:
                tmp = set()
                for c in self.system.courses:
                    tmp.update(c.students)
                all_st = sorted(list(tmp))

            for sid in all_st:
                if flt and flt not in sid:
                    continue
                student_exams = []
                for (s_id_key, c_code), r_code in self.system.student_room_map.items():
                    if s_id_key == sid:
                        if c_code in self.system.assignments:
                            d, s, _ = self.system.assignments[c_code]
                            student_exams.append((c_code, d, s, r_code))

                if student_exams:
                    student_exams.sort(key=lambda x: (x[1], x[2]))
                    for (code, d, s, r) in student_exams:
                        data.append((sid, code, f"G{d+1}/S{s+1}", r, "Sınav Var"))

        # Store current headers for filter popup reference
        self.current_headers = headers
        
        # Store all data (before filtering) for filter window to access
        self.current_data = data.copy()
        
        # Reconfigure tree columns
        cols = tuple(str(i+1) for i in range(len(headers)))
        self.tree.config(columns=cols)

        # Set headings
        for i, h in enumerate(headers):
            self.tree.heading(str(i+1), text=h)
            self.tree.column(str(i+1), anchor='w')

        # Apply column filters
        filtered = []
        for row in data:
            ok = True
            for col_idx, header in enumerate(headers):
                if header in self.column_filters:
                    allowed_values = self.column_filters[header]
                    cell_value = str(row[col_idx]) if col_idx < len(row) else ""
                    if cell_value not in allowed_values:
                        ok = False
                        break
            if ok:
                filtered.append(row)

        if mode != "Günlük Görünüm":
            filtered.sort()
        
        for row in filtered:
            self.tree.insert('', 'end', values=row)
=======
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
        help_text = """
    EXAMTABLE MANAGER - User Guide
    tba
        """
        messagebox.showinfo("Help", help_text)
>>>>>>> Stashed changes
