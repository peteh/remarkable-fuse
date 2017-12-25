from fusepy import FUSE, FuseOSError, Operations, LoggingMixIn
import fusepy
import tempfile
import logging
import os
import remarkable
import stat

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


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


class RemarkeableFuse(LoggingMixIn, Operations):

    def __init__(self):
        self._remarkable = remarkable.Remarkable()

    def create(self, path, mode, fi=None):
        pathElements = self._remarkable._getPathElements(path)
        if len(pathElements) != 1:
            raise RuntimeError("Cannot create file out of root dir")
        fileName = pathElements[0]
        print(fileName)
        LOG.debug("fuse create: " + path + " mode " + mode)
        fh = VirtualFileHandle(self._remarkable, fileName)
        return fh
    
    def readdir(self, path, fh):
        LOG.debug("fuse readdir: %s" % (path))
        remarkableDir = self._remarkable.readDir(path)

        dirents = ['.', '..']
        dirents.extend([entry.getName() for entry in remarkableDir.getDirectoryEntries()])
        dirents.extend([entry.getName() for entry in remarkableDir.getFileEntries()])

        for r in dirents:
            yield r
    
    def write(self, path, buf, offset, fh):
        LOG.debug("fuse write: " + path + " offset " + offset)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def getattr(self, path, fh=None):
        LOG.debug("fuse getaddr: %s" % (path))
        mode = stat.S_IFDIR if(self._remarkable.isDirectory(path)) else stat.S_IFREG
            
        return{'st_atime': 0,
               'st_ctime': 0,
               'st_gid': 0,
               'st_mode': mode,
               'st_mtime': 0,
               'st_nlink': 0,
               'st_size': 0,
               'st_uid': 0}
        
    def statfs(self, path):
        #TODO: come up with useful values
        return{ 'f_bsize': 4096,  # file block size
               'f_frsize': 4096,  # fragment size
               'f_blocks': 10000,  # total file blocks
               'f_bfree': 10000,  # free file blocks
               'f_bavail': 1000,  # free blocks for unpriviledged users
               'f_files': 100000,  # number of inodes
               'f_ffree': 10000,  # free inodes
               'f_favail': 10000,  # free inodes for unpriviledged users
               # fsid not present
               'f_flag': 0,  # mount flag
               'f_namemax': 255  # max length of file names
               }

    def flush(self, path, fh):
        LOG.debug("fuse flush: %s" % (path))
        return os.fsync(fh)

    def release(self, path, fh):
        LOG.debug("fuse release: %s" % (path))
        return os.close(fh)


FUSE(RemarkeableFuse(), "/home/pete/mnt3/", nothreads=True, foreground=True)

