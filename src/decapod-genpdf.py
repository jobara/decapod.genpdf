#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) 2010, 2011 University of Kaiserslautern 
# 
# You may not use this file except under the terms of the accompanying license.
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License. You may
# obtain a copy of the License at http:#www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Project: Decapod
# File: decapod-genpdf.py
# Purpose: The main pipeline to convert scanned raster image to PDF file
# Creator: Mickael Cutter (cutter@iupr.com), Joost van Beusekom (joost@iupr.org)
# Reviewer: Hasan S. M. Al-Khaffaf (hasan@iupr.com)
# Primary Repository: 
# Web Sites: www.iupr.com, www.dfki.de


import os
import sys
import time
import getopt
import shlex, subprocess
import glob
from optparse import OptionParser # easier parsing of the cmd line parameters


class Options:
    def __init__(self):
        self.dpi           = 300       # resolution of the input data
        self.pdfFileName   = "out.pdf" # name of the resulting pdf file
        self.pdfOutputType = 1         # type of the PDF: 1 (image only), 2, 3 or 4 (fontreconstructed PDF)
        self.verbose       = 0         # level of verbosity
        self.bookFileName  = ""        # filename of the input multipage tiff file
        self.width         = 21.0      # width of the generated PDF pages
        self.height        = 29.7      # height of the generated PDF pages
        self.bookDir       = "book-new"# book directory that will be generated containing temp data
        self.fontFileName  = "times"   # font file name to be used to create PDF file
        self.inFileList    = []        # list of image file names to be converted to one PDF
                                  # more flexible alternative to the bookFileName option
        self.book2PagesCMD = ["ocropus","book2pages"] # cmd line tool generating bookDir needed for further processing
        self.psegCMD       = ["ocropus","pages2lines"] # cmd line tool for page segmentation
        self.lineRec1CMD   = ["ocropus","lines2fsts"] #  cmd line tool for line recognition
        self.lineRec2CMD   = ["ocropus","fsts2text"] #
        self.clusterCMD    = "binned-inter" # cmd line tool for clustering
        self.fontCMD       = "./fontGrouper.py" # cmd line tool for font generation
        self.pdfGenCMD     = "./ocro2pdf.py"  # cmd line tool for PDF generation
        
        
    def generateBook2PagesCMD(self):
        cmd = []
        if(self.bookFileName!="" and len(self.inFileList)==0): # multipage tiff given
            cmd = self.book2PagesCMD
            cmd.append(self.bookDir)
            cmd.append(self.bookFileName)
        elif(self.bookFileName=="" and len(self.inFileList)>0): # Hasan: FIXME: wrong code in elif
            cmd = [self.book2PagesCMD]
            for i in len(self.inFileList):
                cmd.append(self.inFileList[i])
            cmd.append("-o")
            cmd.append(self.bookDir)
        else:
            print("[warn] Expecting either -b FILE or FILE1...N as arguments")
        return cmd;
        
    def generateClusterCMD(self):
        cmd=[]
        if(self.pdfOutputType >= 2):
            cmd = ["binned-inter","-b","%s" %(self.bookDir),"-v","%d" %(self.verbose)]
        return cmd
    
    def generatePSegCMD(self):
        cmd=[]
#        if (self.pdfOutputType > 1):
#            self.fileList = glob.glob("%s/????.png" %(self.bookDir))
#            cmd = self.fileList 
        cmd = self.psegCMD + [self.bookDir]
        return cmd
                    
    def generateLineRec1CMD(self):
        cmd=[]
        if(self.pdfOutputType > 1):
#            self.fileList = glob.glob("%s/????/??????.png" %(self.bookDir))
#            cmd = self.fileList
#            cmd.insert(0,self.lineRec1CMD)
            cmd = self.lineRec1CMD + [self.bookDir]
        return cmd
    
    def generateLineRec2CMD(self):
        cmd=[]
        if(self.pdfOutputType > 1):
#            fileList = glob.glob("%s/????/??????.png" %(bookDir))
#            cmd = fileList
#            cmd.insert(0,lineRec2CMD)
            cmd = self.lineRec2CMD + [self.bookDir]
        return cmd
    
    def generateFontCMD(self):
        cmd=[]
        if(self.pdfOutputType==4):
            cmd=[self.fontCMD,"-d","%s" %(self.bookDir)]
        return cmd

    def generatePDFCMD(self):
        cmd = [self.pdfGenCMD, '-d', "%s" %(self.bookDir), '-t', "%s"%self.pdfOutputType, '-p', '%s'%self.pdfFileName ,'-v', '%s'%self.verbose]
        return cmd
        

msg = '\nusage: python runPipeLine.py input file in pdf form \n\nworks iff "." only appears prior ext\nntake an input file and run ocropus clustering genPdf'

def main(sysargv):
#    clustercommand = ["binned-inter"] # command called for token clustering
#    pdfgencommand = ["ocro2pdf.py"]   # command called for PDF generation
#    fontcommand = ["fontGrouper.py"]  # command called for font generation
#    book2pages = ["ocropus-binarize"] # command called for generating the book Dir and binarization
#    bookFileName = ""   # multipage TIFF file for which the PDF is generated
#    pdfOutputType = 1   # default PDF type: image only
#    pdfFileName = ""    # filename of the resultine PDF
#    dpi=300             # default resolution
#    verbose=0           # default: be not verbose at all
    infoToken = "$@$ExportStatus$@$"
    
    # new option parsing
    parser = OptionParser()
    opt = Options()
    parser.add_option("-t", "--type", default=1, dest="pdfOutputType",  
        help="type of the PDF to be generates:\n"\
             "  1: image only [default]\n"\
             "  2: recognized text overlaid with image\n"\
             "  3: tokenized\n"\
             "  4: font reconstructed PDF\n")
    parser.add_option("-W", "--width", default=21.0, dest="pageWidth",
        type="float", help="page width of the generated PDF file (in [cm])")
    parser.add_option("-H", "--height", default=29.7, dest="pageHeight",
        type="float", help="page height of the generated PDF file (in [cm])")
    parser.add_option("-d", "--dir",  dest="bookDir",  
        help="OCRopus Book directory structure that will be generated")
    parser.add_option("-p", "--pdf",  dest="pdfFileName",  
        help="name of the resulting PDF file")
    parser.add_option("-v", "--verbose", default=0, dest="verbose",  
        type="int", help="verbosity")
    parser.add_option("-r", "--resolution", default=300, dest="dpi", 
        type="int", help="Resolution of the input images (in [dpi])")
    parser.add_option("-b", "--book",  dest="bookFileName",  
        help="name of the multipage tiff input file")
    parser.add_option("-f", "--font",  dest="fontFileName",  
        help="name of the TTF font to be used to create the PDF file")
    # parse params and options
    (options, args) = parser.parse_args() 
    # set options in opt
    opt.dpi     = options.dpi
    opt.width   = options.pageWidth
    opt.height  = options.pageHeight
    opt.bookFileName = options.bookFileName
    opt.bookDir = options.bookDir +'/'
    opt.pdfOutputType = int(options.pdfOutputType)
    opt.verbose = options.verbose
    opt.pdfFileName = options.pdfFileName
    opt.fontFileName = options.fontFileName
    
    
    start = time.time()

    opt.book2PagesCMD = opt.generateBook2PagesCMD()
    retCode = subprocess.call(opt.book2PagesCMD)
    if (retCode != 0):
        print "[Error] generating book structure did not work as expected! (%s)" %(opt.book2PagesCMD)
        sys.exit(2) #unknown error

    endBin = time.time()
    print infoToken+"processComplete:book2pages"
    if opt.verbose>1:
        print "[Info]: time used by binarization: %d sec" %(endBin - start)

 
    opt.psegCMD = opt.generatePSegCMD()
#    if(opt.pdfOutputType > 0): #Hasan: commented
    retCode = subprocess.call(opt.psegCMD)
    if (retCode != 0):
        print "[Error] page segmentation did not work as expected! (%s)" %(opt.psegCMD)
        sys.exit(2) #unknown error
    
    if(opt.pdfOutputType > 1): #Hasan
        endPSeg = time.time()
        print infoToken+"processComplete:pages2lines"
        if opt.verbose>1:
            print "[Info]: time used by page segmentation: %d sec" %(endPSeg - endBin)

        opt.lineRec1CMD = opt.generateLineRec1CMD()
        retCode = subprocess.call(opt.lineRec1CMD)
        if (retCode != 0):
            print "[Error] line2fst recognition did not work as expected! (%s)" %(opt.lineRec1CMD)
            sys.exit(2) #unknown error
        
        opt.lineRec2CMD = opt.generateLineRec2CMD()
        retCode = subprocess.call(opt.lineRec2CMD)
        if (retCode != 0):
            print "[Error] fst2txt recognition did not work as expected! (%s)" %(opt.lineRec2CMD)
            sys.exit(2) #unknown error

        endRecog = time.time()
        print infoToken+"processComplete:linerec"        
        if opt.verbose>1:
            print "[Info]: time used by text recognizer: %d sec" %(endRecog-endPSeg)


    endOCROPUS = time.time()
    if opt.verbose>1:
        print "[Info]: time used by OCRopus: %d sec" %(endOCROPUS - start)

    #run clustering
    if(opt.pdfOutputType==2 or opt.pdfOutputType==3 or opt.pdfOutputType==4):
        if opt.verbose>1:
            print "[Info]: running clustering"
        #cmd = shlex.split(clustercommand)
        opt.clusterCMD = opt.generateClusterCMD()
        retCode = subprocess.call(opt.clusterCMD)
        if (retCode != 0):
            print "[Error]: clustering did not work as expected! (%s)" %(opt.clusterCMD)
        #os.system(clustercommand)
        print infoToken+"processComplete:clustering"
    endClustering = time.time()
    if opt.verbose>1:
        print "[Info]: time used by clustering: %d sec" %(endClustering - endOCROPUS)


    #run clustering
    if(opt.pdfOutputType==4):
        if opt.verbose>1:
            print "[Info]: running font generation"
        #cmd = shlex.split(clustercommand)
        opt.fontCMD = opt.generateFontCMD()
        retCode = subprocess.call(opt.fontCMD)
        if (retCode != 0):
            print "[Error]: font generation did not work as expected! (%s)" %(opt.fontCMD)
        print infoToken+"processComplete:fontGen"
    endFont = time.time()
    if opt.verbose>1:
        print "[Info]: time used by font generation: %d sec" %(endFont - endClustering)

    #run pdf gen
    if opt.verbose>1:
        print "[Info]: generating pdf"
    
    opt.pdfGenCMD = opt.generatePDFCMD()
    retCode = subprocess.call(opt.pdfGenCMD)
    if (retCode != 0):
        print "[Error] PDF generation did not work as expected! (%s)" %(opt.pdfGenCMD)
        sys.exit(2)
    
    endGenPDF = time.time()
    print infoToken+"processComplete:genpdf"
    if opt.verbose>1:
        print "[Info]: time used by pdf generation: %d sec" %(endGenPDF - endFont)
        print "[Info]: time used for whole process: %d sec" %(endGenPDF - start)

def usage(progName):
    print "\n%s [OPTIONS]\n\n"\
	      "   -b  --book         name of multipage tiff file\n"\
          "   -d, --dir          Ocropus Directory to be converted\n"\
          "   -p, --pdf          PDF File that will be generated\n"\
          " Options:\n"\
          "   -h, --help:        print this help\n"\
          "   -v, --verbose:     verbose level [0,1,2,3]\n"\
          "   -t, --type:        type of the PDF to be generates:\n"\
          "                          1: image only [default]\n"\
          "                          2: recognized text overlaid with image\n"\
          "                          3: tokenized\n"\
          "                          4: reconstructed font\n"\
          "   -W, --width:       width of the PDF page [in cm] [default = 21.0]:\n"\
          "   -H, --height:      height of the PDF page [in cm] [default = 29.7]:\n"\
          "   -r, --resolution:  resolution of the images in the PDF [default = 200dpi]\n"\
          "   -R --remerge       remerge token clusters [default = false] \n"\
          "   -S, --seg2bbox     suppresses generating files necessary to generate PDF \n"\
          "   -C, --enforceCSEG  characters can only match if there CSEG labels are equal \n"\
          "   -e, --eps          matching threshold [default=7] \n"\
          "   -s, --reps         matching threshold [default=.07] \n"\


if __name__ == "__main__":
    main(sys.argv)
    sys.exit(0)


 

