from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkcalendar import DateEntry   
from datetime import date



class App:
    def __init__(self, window):
        self.window = window
        self.window.title("Tkinter App")
        self.window.geometry("600x600")

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
    def openfile(self):
        filepath = filedialog.askopenfilename(
            initialdir="C:\\Users\\Kaan\\Desktop\\tk\\GUI",
            title="Open the file calmly",
            filetypes=(("text files", "*.txt"), ("all files", "*.*"))
        )

        if filepath:
            with open(filepath, "r") as file:
                print(file.read())

    # ---------------- TABS ----------------
    def addTabs(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        self.tab1 = Frame(self.notebook)
        self.tab2 = Frame(self.notebook)

        self.notebook.add(self.tab1, text="                          IMPORT TAB                     ")
        self.notebook.add(self.tab2, text="                          RESULTS TAB                    ")

        


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

        # Exam Period (Days)
        ttk.Label(settings_lf, text="Exam Period (Days):").grid(row=1, column=0, sticky="w", pady=5)
        self.exam_days = Spinbox(
            settings_lf,
            from_=1,
            to=30,
            width=5
        )
        self.exam_days.delete(0, END)
        self.exam_days.insert(0, "5")
        self.exam_days.grid(row=1, column=1, sticky="w", pady=5, padx=10)

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
            command=self.openfile
        ).pack(pady=6)

        Button(
            left_frame,
            text="Import Lessons.csv",
            font=("calibri", 12),
            width=30,
            command=self.openfile
        ).pack(pady=6)

        Button(
            left_frame,
            text="Import Students.csv",
            font=("calibri", 12),
            width=30,
            command=self.openfile
        ).pack(pady=6)

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
