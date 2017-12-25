# remarkable-fuse
Python Fuse for Remarkable ebook reader. 

This project aims to use the REST API for the usb web ui of the reMarkable through a FUSE layer. This fuse layer could be mounted and used through ebook management programs like Calibre. 

What works: 
 - Listing files and directories
 
What does not work: 
 - Pushing files to the Remarkable

The web ui uses a REST API for file management. Files and directories have assigned uuids which have a parent child relationship. 

The web ui of the reMarkable listens on http://10.11.99.1 (Has to be enabled in the Storage Options). It provides the following interfaces: 
/documents/ --> lists the root files
/documents/[uuid] --> lists sub directories and files entries of the respective uuid
/upload/ --> can upload pdf/epub files via post to the root of the reMarkable
/download/[uuid]/placeholder --> downloads the respective file uuid as PDF (can be rather slow for big files)

Limitations of the web ui: 
 - no download of files (files would always be transformed to PDF)
 - uploads only to the root folder
 - no renaming
 - no deleting