import os
def find_files(filename, search_path):
   result = []

# Walking top-down from the root
   for root, dir, file in os.walk(search_path):
      for fileNames in file:
         if filename in fileNames:
               result.append(os.path.join(root, fileNames))
   return result

# Getting user inputs
year = input("Input the year\n")
startMonth = input("Input the start month\n")
endMonth = input ("Input the end month\n")

originDirectory = "C:\\Users\\Nicanor\\Desktop\\TestFiles\\From\\"
destinationDirectory = "C:\\Users\\Nicanor\\Desktop\\TestFiles\\To\\"
yearFolderDestination = destinationDirectory + str(year) + "\\"

# Make destination folders by month if they do not exist.
for i in range(1,13):
    yearMonth = str(year) + "{:02d}".format(i)
    yearMonthDestinationFolder = yearFolderDestination + year + "-"+ "{:02d}".format(i)

    try:
        if os.path.exists(yearMonthDestinationFolder):
            print(yearMonth + " folder already exists")
        else:
            os.makedirs(yearMonthDestinationFolder)
            print(str(yearMonth) + " folder has been created")

        # Find associated photos/videos/files taken in during 'yearMonth'
        found_files = find_files(str(yearMonth), originDirectory)
        if len(found_files) == 0:
            print("No files found for " + str(yearMonth))
        else:
            # Move/Copy the found files into the destination directory
            for file in found_files:
                os.rename(file, yearMonthDestinationFolder + "\\" + os.path.basename(file))
            print(str(yearMonth) + " has been organised.")

    except FileNotFoundError:
        print(yearFolderDestination + " was not found")
    except FileExistsError:
        print("File already exists, moving on")

# for month in range(startMonth, endMonth)