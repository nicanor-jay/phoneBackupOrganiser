import tkinter as tk

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

        self.startMonth = tk.StringVar(self.root)
        self.startMonth.set("Select the start month")
        self.startMonthDropDown = tk.OptionMenu(self.root,self.startMonth, *MONTHOPTIONS)
        self.startMonthDropDown.pack()

        self.endMonth = tk.StringVar(self.root)
        self.endMonth.set("Select the end month")
        self.endMonthDropDown = tk.OptionMenu(self.root,self.endMonth, *MONTHOPTIONS)
        self.endMonthDropDown.pack()

        self.button = tk.Button(self.root, text="Sort", font =('Arial', 10), command=self.test_function)
        self.button.pack(padx=10,pady=10)

        self.root.mainloop()

    def test_function(self):
        print(self.startMonth.get())
        print(self.endMonth.get())
        pass

myGUI()