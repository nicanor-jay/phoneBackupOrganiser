import tkinter as tk
from tkinter import messagebox

MONTHOPTIONS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
]
class myGUI:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("File Organiser")
        self.root.geometry('700x500')

        self.label = tk.Label(self.root, text="Photo & Video Organiser", font =('Arial', 20))
        self.label.pack(padx=10, pady=10)

        self.yearEntry = tk.Text(self.root,  height=1, width=5, font=('Arial', 10))
        self.yearEntry.pack()

        self.startMonthEntry = tk.StringVar(self.root)
        self.startMonthEntry.set("Select the start month")
        self.startMonthEntryDropDown = tk.OptionMenu(self.root,self.startMonthEntry, *MONTHOPTIONS)
        self.startMonthEntryDropDown.pack()

        self.endMonthEntry = tk.StringVar(self.root)
        self.endMonthEntry.set("Select the end month")
        self.endMonthEntryDropDown = tk.OptionMenu(self.root,self.endMonthEntry, *MONTHOPTIONS)
        self.endMonthEntryDropDown.pack()

        self.sortButton = tk.Button(self.root, text="Sort", font =('Arial', 10), command=self.test_function)
        self.sortButton.pack(padx=10,pady=10)

        self.root.mainloop()

    def test_function(self):
        try:
            year = int(self.yearEntry.get('1.0', tk.END))
            startMonth = int(self.startMonthEntry.get())
            yearMonth = int(self.endMonthEntry.get())
        except ValueError:
            tk.messagebox.showinfo(title="Warning", message="Sorry, please correct the inputs & try again.")
    def sort_function(self):
        pass

myGUI()