'''
Created on Dec 24, 2017

@author: HOFMANNP
'''

import requests
import json
import tempfile


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
    
    def readFile(self, path):
        pathElements = self._getPathElements(path)
        dirElements = pathElements[:-1]
        dirPath = "/" + "/".join(dirElements) + "/"
        fileName = pathElements[len(pathElements) - 1]

        directory = self.readDir(dirPath)
        for file in directory.getFileEntries():
            if(file.getName() == fileName):
                return file
        raise RuntimeError("Failed to find file: " + path)
    
    def downloadToPdf(self, path, targetPath):
        file = self.readFile(path)
        print(file.getName())
        print(file.getUniqueId())
        url = 'http://10.11.99.1/download/'+file.getUniqueId()+"/epub/"
        resp = requests.get(url=url)
        fp = open(targetPath, "wb")
        fp.write(resp.content)
        fp.close()
    
    def uploadFile(self, srcPath, targetName):
        if not targetName.endswith((".epub", ".pdf")):
            raise RuntimeError("Target file names have to be .epub or .pdf")
        url = 'http://10.11.99.1/upload'
        files = {'file': (targetName, open(srcPath, 'rb'))}

        r = requests.post(url, files=files)
        print(r.text)
        if r.text != "Upload successfull":
            raise RuntimeError("Failed to upload file: "+r.text)
    
    
    def readDir(self, path):
        dirs = self._readDirFromUri()
        for pathElement in self._getPathElements(path):
            found = False
            for directory in dirs.getDirectoryEntries():
                if(directory.getName() == pathElement):
                    dirs = self._readDirFromUri(directory.getUniqueId())
                    found = True
                    break
            if not found:
                raise RuntimeError("Failed to load directory for path: " + path)
        return dirs


class VirtualFileHandle:
    
    def __init__(self, path, data):
        self._fp = tempfile.TemporaryFile(mode='w+b')
        self._fp.write(data);
        self._fp.seek(0)


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


remarkable = Remarkable()
remarkable.uploadFile("d:/testfuse/test.epub", "test2.epub")
#remarkable.downloadToPdf("/test.epub", "d:/testfuse/testdl.epub")

#fuse = RemarkeableFuse()
#print(fuse.readFile("/test.epub"))
#for entry in fuse.readFile("/test.epub"):
#    print (entry)
