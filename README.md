# photo_organizer

Usage> python photo_organizer.py <infolder> <outfolder>

Will recursivly find all defined (edit file to add more) image and video files in the infolder and subdirectories, copying the files to the outfolder while creating folders and renaming the files after their EXIF dates. If no EXIF date is available the file is named after the date its folder has, and if no date can be determined by that either the file's creation date will be used.

If a subfolder is named something like "2015-01-01 Beach party" the "Beach party" part will be given to the new folder as well.