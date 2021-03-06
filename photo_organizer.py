#!/bin/env python

import re
import os
import sys
import time
from IPython.core.debugger import Tracer
import PIL.Image
import hashlib
import shutil
from optparse import OptionParser

from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import getTerminalCharset
from sys import argv, stderr, exit



parser = OptionParser(usage='usage: %prog [arguments]')
parser.add_option('-i', '--input', 
                        dest='indir',
                        help='Input directory which will be traversed for files.')
parser.add_option('-o', '--output', 
                        dest='outdir',
                        help='Output directory where the result will be placed.')
parser.add_option('-v', '--verbose', action="store_true", help="Verbose progress reporting.", default=False)
parser.add_option('-q', '--quiet', action="store_true", help="Suppress all output.", default=False)
(options, args) = parser.parse_args()
if not options.indir:   # if filename is not given
    parser.error('Input directory (-i) not given')
if not options.outdir:   # if filename is not given
    parser.error('Output directory (-o) not given')






indir = options.indir
outdir = options.outdir

# list all file endings
image_endings = ['jpg', 'jpeg', 'tif', 'tiff', 'gif']
video_endings = ['mp4', 'mpeg', 'mpg', 'vid', 'avi']

# blacklisted annoations
annotation_blacklist = ['camera', '100andro', 'opencamera', 'dcim' ]





# handle image files
def process_file(root, file, annotation):

    # get the checksum of the file
    checksum = md5(root, file)

    # if it has been seen before
    if checksum in checksum_memory:
        return 0

    # get the photos date
    date = get_file_date(root, file)

    # Tracer()()

    # add the annotation to the dirname if needed
    dirname = time.strftime("%Y-%m-%d", date)
    if annotation != "":
        dirname += " "+annotation

    # create the dir if needed
    if not os.path.exists("{}/{}".format(outdir, dirname)):
        os.makedirs("{}/{}".format(outdir, dirname))



    # add increment if filename already exists
    outfilename = checkfile("{}/{}/{}.{}".format(outdir,dirname,time.strftime("%Y-%m-%d_%H%M%S", date),file.split('.')[-1].lower()))

    # copy the file to the output dir with the correct name
    shutil.copy("{}/{}".format(root,file), outfilename)

    # add it to the memory
    checksum_memory[checksum] = 1

    return 1






def get_file_date(root, file):
    date = ""
    try:
        filename = "{}/{}".format(root,file)
        filename, realname = unicodeFilename(filename), filename
        parser = createParser(filename, realname)
        if not parser:
            print >>stderr, "Unable to parse file {}".format(filename)
        try:
            actualstderr = sys.stderr
            sys.stderr = open(os.devnull,'w')
            metadata = extractMetadata(parser)
            sys.stderr = actualstderr
        except HachoirError, err:
            print "Metadata extraction error: %s" % unicode(err)
            metadata = None
        if not metadata:
            print "Unable to extract metadata, {}".format(filename)

        text = metadata.exportPlaintext()
        date = ""
        # Tracer()()
        for line in text:
            if line[0:10] == "- Creation":
                
                match = re.search('(\d+-\d+-\d+ \d+:\d+:\d+)', line)
                if match:
                    date = time.strptime(match.groups()[0], '%Y-%m-%d %H:%M:%S')
                    return date
    # if that's not possible, use the file creation date instead
    except:
        pass


    # try to find a date format in folder or file name
    # YYYY-MM-DD or similar
    root_dir_name = root.split('/')[-1]
    match = re.search('(\d+)[-_](\d+)[-_](\d+)', root_dir_name)
    if match:
        try:
            date = time.strptime("{}{}{}".format(match.groups()[0],match.groups()[1],match.groups()[2]), '%Y%m%d')
            return date
        except:
            try:
               date = time.strptime("{}{}{}".format(match.groups()[0],match.groups()[1],match.groups()[2]), '%y%m%d')
               return date
            except:
                try:
                    date = time.strptime("{}{}{}".format(match.groups()[0],match.groups()[1],match.groups()[2]), '%m%d%Y')
                    return date
                except:
                    try:
                        date = time.strptime("{}{}{}".format(match.groups()[0],match.groups()[1],match.groups()[2]), '%m%d%y')
                        return date
                    except:
                        # give up
                        pass


    # YYYYMMDD or similar
    match = re.search('(\d{6,})', root_dir_name)
    if match:
        try:
            date = time.strptime(match.groups()[0], '%Y%m%d')
            return date
        except:
            try:
               date = time.strptime(match.groups()[0], '%y%m%d')
               return date
            except:
                try:
                    date = time.strptime(match.groups()[0], '%m%d%Y')
                    return date
                except:
                    try:
                        time.strptime(match.groups()[0], '%m%d%y')
                        return date
                    except:
                        # give up
                        pass

    # if all else fails, use the file creation date as date
    date = time.strptime(time.ctime(os.path.getctime("{}/{}".format(root,file))))
    return date





# checksum a file
def md5(root, file, blocksize=2**20):
    m = hashlib.md5()
    with open( os.path.join(root, file) , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()



# add a increasing number to the end of a filename if it exists
def checkfile(path):
    path      = os.path.expanduser(path)

    if not os.path.exists(path):
        return path

    root, ext = os.path.splitext(os.path.expanduser(path))
    dir       = os.path.dirname(root)
    fname     = os.path.basename(root)
    candidate = fname+ext
    index     = 0
    ls        = set(os.listdir(dir))
    while candidate in ls:
        candidate = "{}_{}{}".format(fname,index,ext)
        index    += 1
    return os.path.join(dir,candidate)




# init
checksum_memory = dict()
endings_memory = dict()


# create the outdir if needed
if not os.path.exists(outdir):
    os.makedirs(outdir)


# go through the files
for root, subFolders, files in os.walk(indir):

    # get a possible annotation string from folder names with dates
    annotation = ""
    match = re.search('[0-9-_]+\s+(.+)$', root.split('/')[-1])
    if match:
        annotation = match.groups()[0]

    # get annotation from folder names not starting with a date
    match = re.search('^(\D.*)$', root.split('/')[-1])
    if match and annotation == "":
        annotation = match.groups()[0]

    # remove blacklisted annoations
    if annotation.lower() in annotation_blacklist:
        annotation = ""

    # for each file in the subdir
    for file in files:

        # if it's a image
        if file.split('.')[-1].lower() in image_endings or file.split('.')[-1].lower() in video_endings:
            exitcode = process_file(root, file, annotation)
            if exitcode == 0 and (not options.quiet or options.verbose):
                print "Duplicate file skipped: {}/{}".format(root,file)

            elif exitcode != 1 and (not options.quiet or options.verbose):
                print "[ERR] File failed: {}/{}".format(root,file)

            if options.verbose:
                print "Processed: {}/{}".format(root,file)

        # save the ending
        else:
            if not options.quiet or options.verbose:
                print "File skipped: {}/{}".format(root,file)
            endings_memory[file.split('.')[-1].lower()] = 1


# Tracer()()
        
