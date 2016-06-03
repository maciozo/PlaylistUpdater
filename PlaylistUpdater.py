import glob, os, time, threading, queue, sys

cwd = os.getcwd()

# Directories to scan for files from. Use cwd for current working directory.
sourceDirs = [cwd, "D:/Libraries/Music"]

# Directory to write playlist files to
playlistDir = cwd

# Filename for the saved playlist. Existing files will be overwritten
playlistName = "Default.m3u"

# File extensions to scan for
extensions = ["mp3", "flac", "wav", "ogg", "m4a", "aac", "mka"]

# Whether to scan recursively
recursiveScan = True

# Whether to remove non-existant files from the playlist. 
#If the m3u file is edited outside of this script, the modification will not be checked until the script is run again. This is to prevent having to read the entire playlist file on every loop
removeDead = True

maxNumberOfThreads = os.cpu_count()
files = queue.Queue()
directoriesToScan = queue.Queue()

if os.name == "posix":
    dirDelimiter = "/"
else:
    dirDelimiter = "\\"

def main(cwd, sourceDirs, playlistDir, playlistName, extensions, recursiveScan, removeDead, maxNumberOfThreads, files, directoriesToScan):
    for directory in sourceDirs:
        directory = directory.replace("\\", "/")
    
    currentFiles = []
    threads = []
    filesToDelete = False
    
    if len(sourceDirs) < maxNumberOfThreads:
        maxNumberOfThreads = len(sourceDirs)
        
    try:
        with open("%s/%s" % (playlistDir, playlistName), "r", encoding = "utf-8") as m3u:
            for file in m3u:
                currentFiles.append(file.rstrip())
        currentFiles = set(currentFiles) # Removes duplicates
        currentFiles = list(currentFiles)
    except FileNotFoundError:
        with open("%s/s" % (playlistDir, playlistName), "w", encoding = "utf-8") as m3u:
            pass
    
    while (1):
        
        newFiles = []
        
        for i in range(maxNumberOfThreads):
            threads.append(threading.Thread(target = worker, args = (i, extensions), daemon = True))
            threads[i].start()
            
        for directory in sourceDirs:
            directoriesToScan.put(directory)
            
        for i in range(maxNumberOfThreads):
            threads[i].join()
        threads = []
            
        numberOfFoundFiles = 0
        numberOfOldFiles = len(currentFiles)
        numberOfNewFiles = 0
        numberOfRemovedFiles = 0
            
        while not files.empty():
            file = files.get()
            numberOfFoundFiles += 1
            if file not in currentFiles:
                numberOfNewFiles += 1
                currentFiles.append(file)
                newFiles.append(file)
                
        if removeDead:
            for file in currentFiles:
                if not os.path.isfile(file):
                    currentFiles.remove(file)
                    numberOfRemovedFiles += 1
                
        print("%i files found. %i new files. %i removed. %i total" % (numberOfFoundFiles, numberOfNewFiles, numberOfRemovedFiles, numberOfNewFiles + numberOfOldFiles - numberOfRemovedFiles))
        
        if (numberOfNewFiles > 0) and (numberOfRemovedFiles == 0):
            try:
                with open("%s/%s" % (playlistDir, playlistName), "a", encoding = "utf-8") as m3u:
                    m3u.write("\n".join(newFiles))
                    m3u.write("\n")
            except PermissionError:
                print("Permission error opening playlist file for writing")
                
        elif numberOfNewFiles > 0:
            try:
                with open("%s/%s" % (playlistDir, playlistName), "w", encoding = "utf-8") as m3u:
                    m3u.write("\n".join(currentFiles) + "\n")
            except PermissionError:
                print("Permission error opening playlist file for writing")
        
        
def worker(threadID, extensions):
    directory = directoriesToScan.get()
    for file in glob.iglob("%s/**/*.*" % directory, recursive = recursiveScan):
        if file.split(".")[-1] in extensions:
            files.put(file)
        
main(cwd, sourceDirs, playlistDir, playlistName, extensions, recursiveScan, removeDead, maxNumberOfThreads, files, directoriesToScan)
