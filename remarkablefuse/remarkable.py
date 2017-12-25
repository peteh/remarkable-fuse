'''
Created on Dec 24, 2017

@author: HOFMANNP
'''

import requests
import json
import tempfile
import logging
import os

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
        LOG.debug("Uploading")
        r = requests.post(url, files=files)
        print(r.text)
        if r.text != "Upload successfull":
            raise RuntimeError("Failed to upload file: " + r.text)
        
    def uploadFileFromPath(self, srcPath, targetName):
        fp = open(srcPath, 'rb')
        try:
            self.uploadFile(fp, targetName)
        finally:
            fp.close()
    
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


class VirtualFileHandle(tempfile.SpooledTemporaryFile):
    
    def __init__(self, remarkable, fileName):
        super(VirtualFileHandle, self).__init__(mode='w+b')
        self._fileName = fileName
        self._remarkable = remarkable
    
    def close(self):
        self.seek(0)
        try:
            self._remarkable.uploadFile(self, self._fileName)
        finally:
            tempfile.SpooledTemporaryFile.close(self)


class RemarkeableFuse():

    def __init__(self):
        self._remarkable = Remarkable()

    def create(self, path, mode, fi=None):
        pathElements = self._remarkable._getPathElements(path)
        if len(pathElements) != 1:
            raise RuntimeError("Cannot create file out of root dir")
        fileName = pathElements[0]
        print(fileName)
        LOG.debug("create: " + path + " mode " + mode)
        fh = VirtualFileHandle(self._remarkable, fileName)
        return fh
    
    def readdir(self, path, fh):
        remarkableDir = self._remarkable.readDir(path)

        dirents = ['.', '..']
        dirents.extend([entry.getName() for entry in remarkableDir.getDirectoryEntries()])
        dirents.extend([entry.getName() for entry in remarkableDir.getFileEntries()])

        for r in dirents:
            yield r
    
    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)
    
    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))


remarkable = Remarkable()
# remarkable.uploadFileFromPath("d:/testfuse/test.epub", "test2.epub")
# remarkable.downloadToPdf("/test2.epub", "d:/testfuse/testdl.epub")

fuse = RemarkeableFuse()
#fp = fuse.create("test.epub", "wb")
#fdata = open("d:/testfuse/test.epub", "rb");
#data = fdata.read()
#fdata.close()
#fp.write(data)
#fp.close()
print(remarkable.readFile("/test.epub"))
# for entry in fuse.readFile("/test.epub"):
#    print (entry)
