# gui.py
import tkinter as tk
import csv
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from tkinter import ttk, filedialog, messagebox
import threading
from logic import ScheduleSystem

class ExamSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sınav Programı - Final")
        self.root.geometry("1100x800")
        self.system = ScheduleSystem()
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
        file_menu.add_command(label="CSV'ye Aktar (Görünen Tablo)", command=self.export_current_view_to_csv)
        file_menu.add_command(label="PDF'ye Aktar (Görünen Tablo)", command=self.export_current_view_to_pdf)
        file_menu.add_separator()

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

        ttk.Label(lf_cfg, text="Gün:").pack(side='left')
        self.ent_days = ttk.Entry(lf_cfg, width=5)
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
        cb.bind("<<ComboboxSelected>>", self.refresh)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda n,i,m: self.refresh())
        ttk.Entry(ctrl, textvariable=self.search_var).pack(side='left', padx=5)
        ttk.Label(ctrl, text="(Filtrele)").pack(side='left')

        self.tree = ttk.Treeview(f, columns=('1','2','3','4','5'), show='headings')
        self.tree.pack(fill='both', expand=True)

        scrolly = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview)
        scrolly.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrolly.set)

    def show_help(self):
        messagebox.showinfo(
            "Yardım",
            " Sistem Özellikleri:\n\n"
            "1. Otomatik Dengeli Dağıtım: Sınavlar günlere yayılır.\n"
            "2. Günlük 2 Sınav Limiti (Öğrenci Bazlı).\n"
            "3. Ardışık Slot Yasağı (Öğrenci Bazlı).\n"
            "4. Esnek İsimlendirme: Dosya isimleri formatı serbesttir.\n"
        )

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
        for i in self.tree.get_children(): self.tree.delete(i)

        mode = self.view_var.get()
        flt = self.search_var.get().upper()
        data = []

        if mode == "Günlük Görünüm":
            headers = ["Gün", "Slot", "Ders Kodu", "Sınıflar", "Mevcut"]
            all_assignments = []
            for c_code, (d, s, rooms) in self.system.assignments.items():
                if flt and flt not in c_code: continue
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
                if flt and flt not in c_code: continue
                room_names = " + ".join([r.code for r in rooms])
                total_cap = sum(r.capacity for r in rooms)
                course_obj = next((c for c in self.system.courses if c.code == c_code), None)
                st_count = len(course_obj.students) if course_obj else 0
                data.append((c_code, f"{st_count} / {total_cap}", f"G{d+1}/S{s+1}", room_names, ""))

        elif mode == "Sınıf Görünümü":
            headers = ["Sınıf", "Ders", "Zaman", "Durum", "-"]
            for c_code, (d, s, rooms) in self.system.assignments.items():
                for r in rooms:
                    if flt and flt not in r.code: continue
                    data.append((r.code, c_code, f"G{d+1}/S{s+1}", "Dolu", ""))

        elif mode == "Öğrenci Görünümü":
            headers = ["Öğrenci ID", "Ders", "Zaman", "GİDECEĞİ SINIF", "Durum"]
            all_st = sorted(list(self.system.all_students_list))
            if not all_st:
                tmp = set()
                for c in self.system.courses: tmp.update(c.students)
                all_st = sorted(list(tmp))

            for sid in all_st:
                if flt and flt not in sid: continue
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

        for i, h in enumerate(headers):
            self.tree.heading(str(i+1), text=h)
        if mode != "Günlük Görünüm": data.sort()
        for row in data: self.tree.insert('', 'end', values=row)
        self.last_headers = headers
        self.last_rows = data

    def export_current_view_to_csv(self):
        if not getattr(self.system, "assignments", None):
            return messagebox.showerror("Hata", "Önce 'HESAPLA' ile program oluşturun.")

        # if refresh did not work (if last_rows do not exist ) we upgrade
        if not hasattr(self, "last_rows") or not hasattr(self, "last_headers"):
            self.refresh()

        if not self.last_rows:
            return messagebox.showerror("Hata", "Dışa aktarılacak veri yok (filtre boş olabilir).")

        default_name = "export.csv"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not path:
            return  # if the user cancels

        try:
            # karakter uyumu için bu
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(self.last_headers)
                for row in self.last_rows:
                    w.writerow(list(row))

            self.log(f"Export tamam: {path}")
            messagebox.showinfo("Başarılı", f"CSV kaydedildi:\n{path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Export başarısız: {e}")

    def export_current_view_to_pdf(self):
        if not getattr(self.system, "assignments", None):
            return messagebox.showerror("Hata", "Önce 'HESAPLA' ile program oluşturun.")

        if not hasattr(self, "last_rows") or not hasattr(self, "last_headers"):
            self.refresh()

        if not self.last_rows:
            return messagebox.showerror("Hata", "Dışa aktarılacak veri yok (filtre boş olabilir).")

        default_name = "export.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            doc = SimpleDocTemplate(
                path,
                pagesize=landscape(A4),
                leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24
            )

            # Başlık satırı + veri satırları
            table_data = [[self._to_ascii(h) for h in self.last_headers]] + \
                         [[self._to_ascii(x) for x in r] for r in self.last_rows]

            tbl = Table(table_data, repeatRows=1)

            tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))

            doc.build([tbl])

            self.log(f"PDF Export tamam: {path}")
            messagebox.showinfo("Başarılı", f"PDF kaydedildi:\n{path}")
        except Exception as e:
            messagebox.showerror("Hata", f"PDF export başarısız: {e}")

    def _to_ascii(self, s):
        tr_map = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
        return str(s).translate(tr_map)
