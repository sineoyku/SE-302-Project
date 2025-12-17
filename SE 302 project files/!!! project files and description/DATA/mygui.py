import threading
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry   
from datetime import date
from logic import ScheduleSystem




class App:
    def __init__(self, window):
        self.window = window
        self.window.title("Tkinter App")
        self.window.geometry("800x700")

        self.system = ScheduleSystem()
        self.addMenu()
        self.addTabs()
        self.addFrames()
        self.buildResultsTab()
        




    # ---------------- MENU ----------------
    def addMenu(self):
        menubar = Menu(self.window)
        self.window.config(menu=menubar)

        fileMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Open", command=self.openfile)
        fileMenu.add_command(label="Save")
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.window.quit)

        editMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=editMenu)
        editMenu.add_command(label="Edit x")
        editMenu.add_command(label="Edit y")
        editMenu.add_separator()
        editMenu.add_command(label="Exit", command=self.window.quit)

    # ---------------- FILE OPEN ----------------
    def openfile(self, file_type="FILE"):
        filepath = filedialog.askopenfilename(
            title="Open file",
            filetypes=(("CSV files", "*.csv"), ("All Files", "*.*"))
        )

        if not filepath:
            self.log(f"⚠️ {file_type} import cancelled.")
            return

        if file_type == "Classrooms":
            msg = self.system.load_classrooms_regex(filepath)
        elif file_type == "Lessons":
            msg = self.system.load_courses_regex(filepath)
        elif file_type == "Students":
            msg = self.system.load_all_students_regex(filepath)
        else:
            msg = "File loaded."

        self.log(msg)

    # ----------------  Generater ---------------- 
    def startGenerate(self):
        self.log("⏳ Generating exam schedule...")
        
        # Progress baslıyo
        self.window.config(cursor="watch")
        
        # Ayrı thread
        t = threading.Thread(target=self.runGenerate, daemon=True)
        t.start()
    
    def runGenerate(self):
        try:
            self.system.num_days = int(self.exam_days.get())
            self.system.slots_per_day = self.timeslots.size()
        except ValueError:
            self.window.after(0, lambda: messagebox.showerror("Error", "Invalid parameters"))
            return

        success, msg = self.system.solve()

        
        self.window.after(0, lambda: self.finishGenerate(success, msg))



    def finishGenerate(self, success, msg): #anlamadım ne bu
        self.window.config(cursor="")
        self.log(msg)

        if not success:
            messagebox.showerror("Error", msg)
            return

        
        for i in self.tree.get_children():
            self.tree.delete(i)

        columns = ("Day", "Slot", "Course", "Rooms", "Students")
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        for c_code, (d, s, rooms) in self.system.assignments.items():
            course_obj = next(c for c in self.system.courses if c.code == c_code)
            room_names = " + ".join(r.code for r in rooms)

            self.tree.insert("", "end", values=(
                f"Day {d+1}",
                f"Slot {s+1}",
                c_code,
                room_names,
                len(course_obj.students)
            ))

        self.notebook.select(self.tab2)

    
    def generateTable(self):
        # Tree temizle
        for i in self.tree.get_children():
            self.tree.delete(i)

        # GUI'den parametreleri logic'e aktar
        self.system.num_days = int(self.exam_days.get())
        self.system.slots_per_day = self.timeslots.size()

        success, msg = self.system.solve()
        self.log(msg)

        if not success:
            messagebox.showerror("Error", msg)
            return

        columns = ("Day", "Slot", "Course", "Rooms", "Students")
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        for c_code, (d, s, rooms) in self.system.assignments.items():
            course_obj = next(c for c in self.system.courses if c.code == c_code)
            room_names = " + ".join(r.code for r in rooms)

            self.tree.insert("", "end", values=(
                f"Day {d+1}",
                f"Slot {s+1}",
                c_code,
                room_names,
                len(course_obj.students)
            ))

        # Results tab’a geç
        self.notebook.select(self.tab2)

        


    # ---------------- TABS ----------------
    def addTabs(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        self.tab1 = Frame(self.notebook)
        self.tab2 = Frame(self.notebook)

        self.notebook.add(self.tab1, text="                          IMPORT TAB                     ")
        self.notebook.add(self.tab2, text="                          RESULTS TAB                    ")

    def buildResultsTab(self):
        # main container
        main_frame = Frame(
            self.tab2,
            bg="#808080",
            relief="sunken",
            border=12
        )
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

       
        results_frame = Frame(main_frame, bg="#b0b0b0")
        results_frame.pack(expand=True, fill="both", padx=10, pady=10)

        Label(
            results_frame,
            text="Exam Schedule Results",
            font=("calibri", 22, "bold"),
            bg="#b0b0b0"
        ).pack(pady=(15, 10))

        
        table_lf = ttk.LabelFrame(
            results_frame,
            text="Generated Exam Table",
            padding=10
        )
        table_lf.pack(expand=True, fill="both", padx=20, pady=15)

        
        self.tree = ttk.Treeview(table_lf, show="headings")
        self.tree.pack(side="left", expand=True, fill="both")

        
        yscroll = ttk.Scrollbar(
            table_lf,
            orient="vertical",
            command=self.tree.yview
        )
        yscroll.pack(side="right", fill="y")

        self.tree.configure(yscrollcommand=yscroll.set)




    # ---------------------- LOG ---------------------
    def log(self, message):
        self.log_box.insert(END, message + "\n")
        self.log_box.see(END)  

    def examDaysChanged(self):
        try:
            current = int(self.exam_days.get())
        except ValueError:
            self.log("❌ Invalid exam period value.")
            return

        if current != self.last_exam_days:
            self.log(f"📅 Exam period changed: {self.last_exam_days} → {current} days")
            self.last_exam_days = current

    def examStartDateChanged(self, event=None):
        current_date = self.start_date.get_date()

        if current_date != self.last_start_date:
            old = self.last_start_date.strftime("%d.%m.%Y")
            new = current_date.strftime("%d.%m.%Y")

            self.log(f"🗓️ Exam start date changed: {old} → {new}")
            self.last_start_date = current_date




    # ---------------- BUTTON FUNCTIONS ----------------
    def deleteSlotButton(self):
        selected = self.timeslots.curselection()
        if selected:
            removed = self.timeslots.get(selected[0])
            self.timeslots.delete(selected[0])
            self.timeslots.config(height=self.timeslots.size())

            self.log(f"🗑️ Time slot removed: {removed}")
        else:
            self.log("⚠️ No time slot selected to delete.")


     
    def addSlotButton(self):
        if self.timeslots.size() == 0:
            next_slot = "09:00-11:00"
        else:
            last_slot = self.timeslots.get(END)
            start, end = last_slot.split("-")

            end_hour = int(end.split(":")[0])
            next_start = end_hour + 1
            next_end = next_start + 2

            if next_end > 24:
                self.log("❌ Cannot add slot: exceeds day limit.")
                return

            next_slot = f"{next_start:02d}:00-{next_end:02d}:00"

        index = self.timeslots.size()
        self.timeslots.insert(END, next_slot)

        color = "#f0f0f0" if index % 2 == 0 else "white"
        self.timeslots.itemconfig(index, {'bg': color})
        self.timeslots.config(height=self.timeslots.size())

        self.log(f" Time slot added: {next_slot}")

        


    # ---------------- FRAME + BUTTONS ----------------

   


    def addFrames(self):
        # Ana container (tab'ın tamamını kaplar)
        main_frame = Frame(self.tab1, bg="#808080", relief="sunken", border=12)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # ---------------- SOL PANEL ----------------
        left_frame = Frame(main_frame, bg="#8c8c8c")
        left_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        Label(
            left_frame,
            text="Configuration",
            font=("calibri", 22, "bold"),
            bg="#8c8c8c"
        ).pack(pady=(20, 10))

        # ========= EXAM SETTINGS =========
        settings_lf = ttk.LabelFrame(
            left_frame,
            text="Exam Settings",
            padding=10
        )
        settings_lf.pack(fill="x", padx=20, pady=15)

        # Exam Start Date
        ttk.Label(settings_lf, text="Exam Start Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_date = DateEntry(
            settings_lf,
            date_pattern="dd.mm.yyyy",
            width=12
        )
        self.start_date.set_date(date.today())
        self.start_date.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        self.last_start_date = self.start_date.get_date()

        self.start_date.bind("<<DateEntrySelected>>", self.examStartDateChanged)
        self.start_date.bind("<FocusOut>", self.examStartDateChanged)


        # Exam Period (Days)
        ttk.Label(settings_lf, text="Exam Period (Days):").grid(row=1, column=0, sticky="w", pady=5)
        
        self.exam_days = Spinbox(
            settings_lf,
            from_=1,
            to=30,
            width=5,
            command=self.examDaysChanged
        )
        self.exam_days.delete(0, END)
        self.exam_days.insert(0, "5")
        self.exam_days.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        self.last_exam_days = int(self.exam_days.get())
        self.exam_days.bind("<FocusOut>", lambda e: self.examDaysChanged())
        self.exam_days.bind("<Return>", lambda e: self.examDaysChanged())


        # Time Slots
        ttk.Label(settings_lf, text="Time Slots (Hours):").grid(row=2,column=0,sticky="w",pady=12)
        
        self.timeslots = Listbox(settings_lf,fg="black",
                  width=22)
        self.timeslots.insert(0,"09:00-11:00")
        self.timeslots.insert(1,"12:00-14:00")

        self.timeslots.config(height=self.timeslots.size())

        self.timeslots.grid(row=2, column=1, sticky="w", pady=5, padx=10)

        addButton = Button(settings_lf,text="+",background="#078013",
                           width=4,height=1,relief="raised",
                           font=("calibri",12,"bold"),
                           activebackground="black",
                           activeforeground="white",
                           command=self.addSlotButton).grid(row=3, column=1, sticky="e", pady=5, padx=10,)
        
        deleteButton = Button(settings_lf,text="-",background="#7A0808",
                              width=4,height=1,relief="sunken",
                              font=("calibri",12,"bold"),
                              activebackground="black",
                              activeforeground="white",
                              command=self.deleteSlotButton).grid(row=3, column=1, sticky="e", pady=5, padx=55)
        

        # ================================================

        Label(
            left_frame,
            text="Please import the required files.",
            font=("calibri", 13),
            bg="#8c8c8c"
        ).pack(pady=(10, 5))

        Button(
            left_frame,
            text="Import Classrooms.csv",
            font=("calibri", 12),
            width=30,
            command=lambda: self.openfile("Classrooms"),
            activebackground="black",
            activeforeground="white"
        ).pack(pady=6)

        Button(
            left_frame,
            text="Import Lessons.csv",
            font=("calibri", 12),
            width=30,
            command=lambda: self.openfile("Lessons"),
            activebackground="black",
            activeforeground="white"
        ).pack(pady=6)

        Button(
            left_frame,
            text="Import Students.csv",
            font=("calibri", 12),
            width=30,
            command=lambda: self.openfile("Students"),
            activebackground="black",
            activeforeground="white"
        ).pack(pady=6)

        Button(
            left_frame,
            text="GENERATE EXAM TABLE",
            font=("calibri", 13, "bold"),
            width=30,
            bg="#1E88E5",
            fg="white",
            activebackground="black",
            activeforeground="white",
            command=self.startGenerate
        ).pack(pady=15)


        # ---------------- SAĞ PANEL ----------------
        right_frame = Frame(main_frame, bg="#b0b0b0")
        right_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        Label(
            right_frame,
            text="Status / Log",
            font=("calibri", 22, "bold"),
            bg="#b0b0b0"
        ).pack(pady=(20, 10))

        self.log_box = Text(right_frame)
        self.log_box.pack(expand=True, fill="both", padx=10, pady=10)
        

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    window = Tk()
    app = App(window)
    window.mainloop()
