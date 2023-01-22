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
        self.fromFolderLabel = tk.Label(self.root, text="Enter 'From' Directory")
        self.fromFolderLabel.grid(row=1, column=0)
        self.fromFolderEntry = tk.Entry(self.root, width=40, textvariable=self.fromFolderPath)
        self.fromFolderEntry.grid(row=1, column=1)
        self.fromDirectoryButton = tk.Button(self.root, text="Browse Files", font=('Arial', 10),
                                             command=self.getFromDirectory)
        self.fromDirectoryButton.grid(row=1, column=2)

        self.toFolderPath = tk.StringVar()
        self.toFolderLabel = tk.Label(self.root, text = "Enter 'to' Directory")
        self.toFolderLabel.grid(row=2, column=0)
        self.toFolderEntry = tk.Entry(self.root, width=40, textvariable=self.toFolderPath)
        self.toFolderEntry.grid(row=2, column=1)
        self.toDirectoryButton = tk.Button(self.root, text="Browse Files", font=('Arial', 10),
                                             command=self.getToDirectory)
        self.toDirectoryButton.grid(row=2, column=2)

        self.yearLabel = tk.Label(self.root, text="Enter Desired Year")
        self.yearLabel.grid(row=3, column=0)
        self.yearEntry = tk.Text(self.root,  height=1, width=17, font=('Arial', 10))
        self.yearEntry.grid(row=3, column=1)

        self.yearLabel = tk.Label(self.root, text="Enter Start Month")
        self.yearLabel.grid(row=4, column=0)
        self.startMonthEntry = tk.StringVar(self.root)
        self.startMonthEntryDropDown = tk.OptionMenu(self.root,self.startMonthEntry, *MONTHOPTIONS)
        self.startMonthEntryDropDown.grid(row=4, column=1)

        self.yearLabel = tk.Label(self.root, text="Enter End Month")
        self.yearLabel.grid(row=5, column=0)
        self.endMonthEntry = tk.StringVar(self.root)
        self.endMonthEntryDropDown = tk.OptionMenu(self.root,self.endMonthEntry, *MONTHOPTIONS)
        self.endMonthEntryDropDown.grid(row=5, column=1)

        self.sortButton = tk.Button(self.root, text="Move and Organise Files", font =('Arial', 10), command=self.validateInputs)
        self.sortButton.grid(row=6, column=1)

        self.root.mainloop()


    def getFromDirectory(self):
        self.myFromDirectory = tk.filedialog.askdirectory()
        self.fromFolderPath.set(self.myFromDirectory)
    def getToDirectory(self):
        self.myToDirectory = tk.filedialog.askdirectory()
        self.toFolderPath.set(self.myToDirectory)

    def validateInputs(self):
        try:
            fromDirectory = self.fromFolderPath.get()
            toDirectory = self.toFolderPath.get()
            year = int(self.yearEntry.get('1.0', tk.END))
            startMonth = int(self.startMonthEntry.get())
            yearMonth = int(self.endMonthEntry.get())
            print(fromDirectory)
            print(toDirectory)
            print(year)
            print(startMonth)
            print(yearMonth)
        except ValueError:
            tk.messagebox.showinfo(title="Warning", message="Sorry, please correct the inputs & try again.")
    def sortFiles(self):
        pass

myGUI()