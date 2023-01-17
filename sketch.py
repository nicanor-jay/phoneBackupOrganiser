import os
import random

#find_files definition
def find_files(filename, search_path):
   result = []

# Walking top-down from the root
   for root, dir, file in os.walk(search_path):
      for fileNames in file:
         if filename in fileNames:
               result.append(os.path.join(root, fileNames))
   return result

# Setup Step 0 - Create folders by month, by year in desired folder destination
# destination = "E:\\Phone Media Backups\\2023\\2023-"
destination = "C:\\Users\\Nicanor\\Desktop\\TestFiles\\To\\2022-"

for i in range(1,13):
    filename = destination + "{:02d}".format(i)
    try:
        if os.path.exists(filename):
            print("There is already a file there")
        else:
            os.makedirs(filename)
            print("File has been created")
    except FileNotFoundError:
        print(destination +" was not found")

# Step 1 - Search for files named
# found_files = find_files("202203", "E:\\Phone Media Backups\\2022")
found_files = find_files("202201", "C:\\Users\\Nicanor\\Desktop\\TestFiles\\From")
print(found_files)

# Step 3 - Copy/Move found files into folders created earlier
# for file in found_files:
#     os.rename(file, destination)
