from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkcalendar import DateEntry   
from datetime import date



class App:
    def __init__(self, window):
        self.window = window
        self.window.title("Tkinter App")
        self.window.geometry("800x700")

        self.addMenu()
        self.addTabs()
        self.addFrames()




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
    def openfile(self,file_type="FILE"):
        filepath = filedialog.askopenfilename(
            title="Open the file calmly",
            filetypes=(("CSV files", "*.csv"), ("All Files", "*.*"))
        )

        if filepath:
            filename = filepath.split("/")[-1]
            self.log(f"📂 {file_type} imported: {filename}")
            self.log(f"    Path: {filepath}")
        else:
            self.log(f"⚠️ {file_type} import cancelled.")


        

        


    # ---------------- TABS ----------------
    def addTabs(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        self.tab1 = Frame(self.notebook)
        self.tab2 = Frame(self.notebook)

        self.notebook.add(self.tab1, text="                          IMPORT TAB                     ")
        self.notebook.add(self.tab2, text="                          RESULTS TAB                    ")

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

        # ========= EXAM SETTINGS (YENİ EKLENEN KISIM) =========
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
            #command=self.generateTable
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
