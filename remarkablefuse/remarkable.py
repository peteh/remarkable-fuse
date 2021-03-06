'''
Created on Dec 24, 2017

@author: pete
'''

import requests
import json

import logging

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


class RemarkableDirectory():
    
    def __init__(self):
        self._subDirs = []
        self._files = []
    
    def appendDirectoryEntry(self, dirEntry):
        self._subDirs.append(dirEntry)
        
    def appendFileEntry(self, fileEntry):
        self._files.append(fileEntry)
        
    def getFileEntries(self):
        return self._files
    
    def getDirectoryEntries(self):
        return self._subDirs

        
class RemarkableDirectoryEntry():

    def __init__(self, name, uniqueId):
        self._name = name
        self._uniqueId = uniqueId
    
    def getName(self):
        return self._name
    
    def getUniqueId(self):
        return self._uniqueId
    
    def __repr__(self):
        return 'dir: ' + self.getName()


class RemarkableFileEntry():

    def __init__(self, name, uniqueId):
        self._name = name
        self._uniqueId = uniqueId
    
    def getName(self):
        return self._name
    
    def getUniqueId(self):
        return self._uniqueId
    
    def __repr__(self):
        return 'file: ' + self.getName()


class Remarkable():
    
    def _removeEmpty(self, entries):
        return [entry for entry in entries if entry]
    
    def _getPathElements(self, path):
        return self._removeEmpty(path.split("/"))

    def _isDirectory(self, entry):
        return entry['Type'] == 'CollectionType'
    
    def _isFile(self, entry):
        return entry['Type'] == 'DocumentType'
    
    def _createDirEntry(self, element):
        return RemarkableDirectoryEntry(element['VissibleName'], element['ID'])
    
    def _createFileEntry(self, element):
        name = element['VissibleName']
        fileTypeKey = 'fileType'
        if(fileTypeKey in element and element[fileTypeKey] != ''):
            name = name + "." + element[fileTypeKey]
        return RemarkableFileEntry(name, element['ID'])
    
    def _getDirFromJson(self, data):
        remarkableDirectory = RemarkableDirectory()
        for element in data:
            if self._isDirectory(element):
                remarkableDirectory.appendDirectoryEntry(self._createDirEntry(element))
            if self._isFile(element):
                remarkableDirectory.appendFileEntry(self._createFileEntry(element))
                
        return remarkableDirectory
    
    def _readDirFromUri(self, uniqueId=None):
        baseUrl = 'http://10.11.99.1/documents/'
        url = baseUrl if uniqueId is None else baseUrl + uniqueId
        resp = requests.get(url=url)
        data = json.loads(resp.text)
        return self._getDirFromJson(data)

    def readDir(self, path):
        directory = self._readDirFromUri()
        for pathElement in self._getPathElements(path):
            found = False
            for directory in directory.getDirectoryEntries():
                if(directory.getName() == pathElement):
                    directory = self._readDirFromUri(directory.getUniqueId())
                    found = True
                    break
            if not found:
                raise NotADirectoryError("Failed to load directory for path: " + path)
        return directory
    
    def readFile(self, path):
        pathElements = self._getPathElements(path)
        dirElements = pathElements[:-1]
        dirPath = "/" + "/".join(dirElements) + "/"
        fileName = pathElements[len(pathElements) - 1]

        try: 
            directory = self.readDir(dirPath)
        except NotADirectoryError as e:
            raise FileNotFoundError("Could not open path " + path) from e
        for file in directory.getFileEntries():
            if(file.getName() == fileName):
                return file
        raise FileNotFoundError("Failed to find file: " + path)
    
    def isFile(self, path):
        try: 
            self.readFile(path)
            return True
        except(FileNotFoundError):
            return False
    
    def isDirectory(self, path):
        try: 
            self.readDir(path)
            return True
        except(NotADirectoryError):
            return False
        
    def downloadToPdf(self, path, targetPath):
        file = self.readFile(path)
        print(file.getName())
        print(file.getUniqueId())
        url = 'http://10.11.99.1/download/' + file.getUniqueId() + "/epub/"
        resp = requests.get(url=url)
        fp = open(targetPath, "wb")
        fp.write(resp.content)
        fp.close()
    
    def uploadFile(self, fp, targetName):
        if not targetName.endswith((".epub", ".pdf")):
            raise RuntimeError("Target file names have to be .epub or .pdf")
        url = 'http://10.11.99.1/upload'
        files = {'file': (targetName, fp)}
        LOG.debug("Uploading...")
        r = requests.post(url, files=files)
        LOG.debug("Uploading finished")
        print(r.text)
        if r.text != "Upload successfull":
            raise RuntimeError("Failed to upload file: " + r.text)
        
    def uploadFileFromPath(self, srcPath, targetName):
        fp = open(srcPath, 'rb')
        try:
            self.uploadFile(fp, targetName)
        finally:
            fp.close()


# remarkable.uploadFileFromPath("d:/testfuse/test.epub", "test2.epub")
# remarkable.downloadToPdf("/test2.epub", "d:/testfuse/testdl.epub")


#fp = fuse.create("test.epub", "wb")
#fdata = open("d:/testfuse/test.epub", "rb")
#data = fdata.read()
#fdata.close()
#fp.write(data)
#fp.close()
#print(remarkable.isDirectory("/Ebooks"))
# for entry in fuse.readFile("/test.epub"):
#    print (entry)
