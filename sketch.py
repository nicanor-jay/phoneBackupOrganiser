import tkinter as tk
from tkinter import filedialog

MONTHOPTIONS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
]
class myGUI:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("File Organiser")
        self.root.geometry('500x500')

        self.titleLabel = tk.Label(self.root, text="Photo & Video Organiser", font =('Arial', 17))
        self.titleLabel.grid(row=0, column=1)

        self.fromFolderPath = tk.StringVar()
        self.fromFolderLabel = tk.Label(self.root, text = "Enter 'From' Directory")
        self.fromFolderLabel.grid(row=1, column=0)
        self.fromFolderEntry = tk.Entry(self.root, textvariable = self.fromFolderPath)
        self.fromFolderEntry.grid(row=1, column=1)
        self.fromDirectoryButton = tk.Button(self.root, text="Browse Files", font=('Arial', 10),
                                             command=self.getFromDirectory)
        self.fromDirectoryButton.grid(row=1, column=2)

        self.toFolderPath = tk.StringVar()
        self.toFolderLabel = tk.Label(self.root, text = "Enter 'to' Directory")
        self.toFolderLabel.grid(row=2, column=0)
        self.toFolderEntry = tk.Entry(self.root, textvariable = self.toFolderPath)
        self.toFolderEntry.grid(row=2, column=1)
        self.toDirectoryButton = tk.Button(self.root, text="Browse Files", font=('Arial', 10),
                                             command=self.getToDirectory)
        self.toDirectoryButton.grid(row=2, column=2)

        # self.yearEntry = tk.Text(self.root,  height=1, width=5, font=('Arial', 10))
        # self.yearEntry.pack()
        #
        # self.startMonthEntry = tk.StringVar(self.root)
        # self.startMonthEntry.set("Select the start month")
        # self.startMonthEntryDropDown = tk.OptionMenu(self.root,self.startMonthEntry, *MONTHOPTIONS)
        # self.startMonthEntryDropDown.pack()
        #
        # self.endMonthEntry = tk.StringVar(self.root)
        # self.endMonthEntry.set("Select the end month")
        # self.endMonthEntryDropDown = tk.OptionMenu(self.root,self.endMonthEntry, *MONTHOPTIONS)
        # self.endMonthEntryDropDown.pack()
        #
        # self.sortButton = tk.Button(self.root, text="Sort", font =('Arial', 10), command=self.validateInputs)
        # self.sortButton.pack(padx=10,pady=10)

        self.root.mainloop()


    def getFromDirectory(self):
        self.myFromDirectory = tk.filedialog.askdirectory()
        self.fromFolderPath.set(self.myFromDirectory)
    def getToDirectory(self):
        self.myToDirectory = tk.filedialog.askdirectory()
        self.toFolderPath.set(self.myToDirectory)

    def validateInputs(self):
        try:
            fromDirectory = self.fromDirectoryLabel.get('1.0', tk.END)
            year = int(self.yearEntry.get('1.0', tk.END))
            startMonth = int(self.startMonthEntry.get())
            yearMonth = int(self.endMonthEntry.get())
            print(fromDirectory)
        except ValueError:
            tk.messagebox.showinfo(title="Warning", message="Sorry, please correct the inputs & try again.")
    def sortFiles(self):
        pass

myGUI()