import os

def find_files(filename, search_path):
   result = []
# Walking top-down from the root
   for root, dir, file in os.walk(search_path):
      for fileNames in file:
         if filename in fileNames:
               result.append(os.path.join(root, fileNames))
   return result

def count_files(search_path):
    numOfFiles = 0
    # Walking top-down from the root
    for root, dir, file in os.walk(search_path):
        for fileNames in file:
            numOfFiles += 1
    return numOfFiles


def sortFiles(fromDirectory, toDirectory, year, startMonth, endMonth):
    yearFolderDestination = toDirectory + "/" + str(year)
    numPhotosSorted = 0

    print(fromDirectory)

    for i in range(startMonth, endMonth + 1):
        yearMonth = str(year) + "{:02d}".format(i)
        yearMonthDestinationFolder = yearFolderDestination + "-" + "{:02d}".format(i)

        try:
            if os.path.exists(yearMonthDestinationFolder):
                print(yearMonth + " folder already exists")
            else:
                os.makedirs(yearMonthDestinationFolder)
                print(str(yearMonth) + " folder has been created")

            # Find associated photos/videos/files taken in during 'yearMonth'
            found_files = find_files(str(yearMonth), fromDirectory)
            if len(found_files) == 0:
                print("No files found for " + str(yearMonth))
            else:
                # Move/Copy the found files into the 'to' directory
                for file in found_files:
                    os.rename(file, yearMonthDestinationFolder + "/" + os.path.basename(file))
                    numPhotosSorted += 1
                print(str(yearMonth) + " has been organised.")


        except FileNotFoundError:
            print(yearFolderDestination + " was not found")
        except FileExistsError:
            print("moving on")

    return count_files(fromDirectory), numPhotosSorted

