'''
Created on Dec 24, 2017

@author: HOFMANNP
'''

import requests
import json

path = "/Ebooks/"

url = 'http://10.11.99.1/documents/'


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

    def isDirectory(self, entry):
        return entry['Type'] == 'CollectionType'
    
    def isFile(self, entry):
        print(entry)
        return entry['Type'] == 'DocumentType'
    
    def _createDirEntry(self, element):
        return RemarkableDirectoryEntry(element['VissibleName'], element['ID'])
    
    def _createFileEntry(self, element):
        name = element['VissibleName']
        fileTypeKey = 'fileType'
        if(fileTypeKey in element and element[fileTypeKey] != ''):
            name = name + "." + element[fileTypeKey]
        return RemarkableDirectoryEntry(name, element['ID'])
    
    def getDirEntries(self, data):
        remarkableDirectory = RemarkableDirectory()
        for element in data:
            if self.isDirectory(element):
                remarkableDirectory.appendDirectoryEntry(self._createDirEntry(element))
            if self.isFile(element):
                remarkableDirectory.appendDirectoryEntry(self._createFileEntry(element))
                
        return remarkableDirectory
        
    def readDir(self, path):
        baseUrl = 'http://10.11.99.1/documents/'
        resp = requests.get(url=baseUrl)
        data = json.loads(resp.text)
        dirs = self.getDirEntries(data)
        for pathElement in self._getPathElements(path):
            found = False
            for directory in dirs.getDirectoryEntries():
                if(directory.getName() == pathElement):
                    resp = requests.get(url=baseUrl + "/" + directory.getUniqueId())
                    data = json.loads(resp.text)
                    data = json.loads(resp.text)
                    dirs = self.getDirEntries(data)
                    found = True
                    break
            if not found:
                raise RuntimeError("Failed to load directory for path: " + path)
        return dirs


class RemarkeableFuse():
    
    def __init__(self):
        self._remarkable = Remarkable()

    def readdir(self, path, fh):
        remarkableDir = self._remarkable.readDir(path)

        dirents = ['.', '..']
        dirents.extend([entry.getName() for entry in remarkableDir.getDirectoryEntries()])
        dirents.extend([entry.getName() for entry in remarkableDir.getFileEntries()])

        for r in dirents:
            yield r


fuse = RemarkeableFuse()
for entry in fuse.readdir("/Ebooks/", None):
    print (entry)
