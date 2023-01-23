import tkinter as tk, sorting, os
from tkinter import filedialog

MONTHSTOINT = {
    "January":1,
    "February":2,
    "March":3,
    "April":4,
    "May":5,
    "June":6,
    "July":7,
    "August":8,
    "September":9,
    "October":10,
    "November":11,
    "December":12
}

# "Janury", "February", "March", "April", "May", "June", "July", "August", "September",
# "October", "November", "December"
class myGUI:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("File Organiser")
        self.root.geometry('525x330')

        # Title and help
        self.titleFrame = tk.Frame(self.root)
        self.titleFrame.grid(row=0, column=0)
        self.titleLabel = tk.Label(self.titleFrame, text="Photo, Video & File Organiser", font =('Arial', 17))
        self.titleLabel.grid(row=0, column=1)

        self.descriptionLabel = tk.Label(self.titleFrame, text="This sorts & organises your files by year & month. "
                                                        "\n(2016/2016-01, 2016/2016-02, etc)", font =('Arial', 10))
        self.descriptionLabel.grid(row=1, column=1)

        # Getting the directories
        self.directoryFrame = tk.Frame(self.root)
        self.directoryFrame.grid(row=1,column=0)
        self.directoryFrameLabel = tk.LabelFrame(self.directoryFrame, text="Directories")
        self.directoryFrameLabel.grid(row=0, column=0)

        self.fromFolderPath = tk.StringVar()
        self.fromFolderLabel = tk.Label(self.directoryFrameLabel, text="Enter 'From' Directory")
        self.fromFolderLabel.grid(row=2, column=0)
        self.fromFolderEntry = tk.Entry(self.directoryFrameLabel, width=40, textvariable=self.fromFolderPath)
        self.fromFolderEntry.grid(row=2, column=1)
        self.fromDirectoryButton = tk.Button(self.directoryFrameLabel, text="Browse Files", font=('Arial', 10),
                                             command=self.getFromDirectory)
        self.fromDirectoryButton.grid(row=2, column=2)

        self.toFolderPath = tk.StringVar()
        self.toFolderLabel = tk.Label(self.directoryFrameLabel, text="Enter 'To' Directory")
        self.toFolderLabel.grid(row=3, column=0)
        self.toFolderEntry = tk.Entry(self.directoryFrameLabel, width=40, textvariable=self.toFolderPath)
        self.toFolderEntry.grid(row=3, column=1)
        self.toDirectoryButton = tk.Button(self.directoryFrameLabel, text="Browse Files", font=('Arial', 10),
                                             command = self.getToDirectory)
        self.toDirectoryButton.grid(row=3, column=2)

        #Getting the year & month ranges

        self.timeRangeFrame = tk.Frame(self.root)
        self.timeRangeFrame.grid(row=2,column=0)
        self.timeFrameLabel = tk.LabelFrame(self.directoryFrame, text="Year & Month Range")
        self.timeFrameLabel.grid(row=1, column=0, sticky="news")

        self.yearLabel = tk.Label(self.timeFrameLabel, text="Enter Desired Year")
        self.yearLabel.grid(row=0, column=0)
        self.yearEntry = tk.Text(self.timeFrameLabel,  height=1, width=17, font=('Arial', 10))
        self.yearEntry.grid(row=0, column=1)

        self.startMonthLabel = tk.Label(self.timeFrameLabel, text="Range of Months")
        self.startMonthLabel.grid(row=1, column=0)
        self.startMonthEntry = tk.StringVar(self.timeFrameLabel)
        self.startMonthEntry.set(list(MONTHSTOINT.keys())[0])
        self.startMonthEntryDropDown = tk.OptionMenu(self.timeFrameLabel, self.startMonthEntry, *MONTHSTOINT.keys())
        self.startMonthEntryDropDown.grid(row=1, column=1)

        self.between = tk.Label(self.timeFrameLabel, text=" to ")
        self.between.grid(row=1, column=2)

        # self.endMonthLabel = tk.Label(self.timeFrameLabel, text="Enter End Month")
        # self.endMonthLabel.grid(row=2, column=0)
        self.endMonthEntry = tk.StringVar(self.timeFrameLabel)
        self.endMonthEntry.set(list(MONTHSTOINT.keys())[11])
        self.endMonthEntryDropDown = tk.OptionMenu(self.timeFrameLabel, self.endMonthEntry, *MONTHSTOINT.keys())
        self.endMonthEntryDropDown.grid(row=1, column=3)

        # Button
        self.sortButton = tk.Button(self.root, text="Move and Organise Files", font =('Arial', 10),
                                    command=self.validateInputs)
        self.sortButton.grid(row=2, column=0)

        for widget in self.directoryFrameLabel.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        for widget in self.timeFrameLabel.winfo_children():
            widget.grid_configure(padx=10, pady=5)

        self.root.mainloop()


    def getFromDirectory(self):
        self.myFromDirectory = tk.filedialog.askdirectory()
        self.fromFolderPath.set(self.myFromDirectory)
    def getToDirectory(self):
        self.myToDirectory = tk.filedialog.askdirectory()
        self.toFolderPath.set(self.myToDirectory)

    def validateInputs(self):
        try:
            fromDirectory = str(self.fromFolderPath.get())
            toDirectory = str(self.toFolderPath.get())

            if not os.path.exists(fromDirectory) or not os.path.exists(toDirectory):
                raise NotADirectoryError

            year = int(self.yearEntry.get('1.0', tk.END))
            startMonth = MONTHSTOINT[self.startMonthEntry.get()]
            endMonth = MONTHSTOINT[self.endMonthEntry.get()]

            if (startMonth > endMonth):
                raise ValueError

            numFilesLeft, numFilesSorted, numPreexistingFiles = sorting.sortFiles(fromDirectory, toDirectory, year, startMonth, endMonth)
            postProcessingMessage = ""

            if (numFilesSorted > 0):
                postProcessingMessage += str(numFilesSorted) + " files successfully organised."
            else:
                postProcessingMessage = "No files were organised."

            if (numPreexistingFiles > 0):
                postProcessingMessage += "\n " + str(numPreexistingFiles) + " are already within the destination folder."

            if (numFilesLeft > 0):
                postProcessingMessage += "\n " + str(numFilesLeft) + " remaining and needs your attention."

            tk.messagebox.showinfo(title="Success", message=postProcessingMessage)

        except ValueError:
            tk.messagebox.showinfo(title="Warning", message="Sorry, please correct the inputs & try again.")
        except NotADirectoryError:
            tk.messagebox.showinfo(title="Warning", message="Sorry, one of the input directories does not exist.")

myGUI()