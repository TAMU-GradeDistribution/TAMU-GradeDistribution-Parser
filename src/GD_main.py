# TAMU-GradeDistribution-Parser: GD_main.py
# @authors: github/adibarra, github/thestarch2


# imports
import numpy as np
from GD_utils import *
from GD_logger import *
from GD_database import *
import matplotlib.pyplot as plt


# complete startup tasks
Utils.startup(PreferenceLoader)


### main program starts here ###

# generate PDF links
pdflinkbase = 'https://web-as.tamu.edu/GradeReports/PDFReports/'
sems = ['SPRING','SUMMER','FALL']
years = [2017,2018,2019,2020,2021]
lastCompletedSemester = sems[1] # adjust to skip ongoing semesters

colleges = ['AG','AR','GB','BA','DN','ED','EN','GE',
            'SL','LA','MD','MS','NU','PH','SC','VM']
            #'DN_PROF','SL_PROF','CP_PROF','VM_PROF'] PROF not supported, different PDF format
### MD_PROF report currently missing from website
# additional unused codes:
# AE=Academic Success Center
# AP=Association Provost For UG Studies
# GV=TAMU-Galveston
# QT=TAMU-Qatar

pdfs = []
for i in range(0, len(colleges)):
    for k in range(years[0], years[-1]+1):
        year = k
        for j in range(3):
            if(year == years[-1] and j > sems.index(lastCompletedSemester)):
                break
            pdfs.append(str(year)+str(j+1)+'/grd'+str(year)+str(j+1)+colleges[i]+'.pdf')

# automatically load pdfs from pdfs list
errors = []
for pdflink in pdfs:
    Utils.loadPDF(downloadURL=pdflinkbase+pdflink, saveLocation='res/'+pdflink.split('/')[1], overwrite=False)
    grades_list = Utils.parseGradesPDFV2('res/'+pdflink.split('/')[1])
    grades_list = Utils.convertToEntries(grades_list, int(pdflink.split('grd')[1][:4]), sems[int(pdflink.split('grd')[1][4:5])-1])
    DatabaseHandler.addGradeEntries(uuid4(), 'tamugrades', pdflink[14:][:-4], grades_list)

for error in errors:    
    print(error)

Logger.log('\n-----------------------\nGoodbye...\n-----------------------\n\n\n', importance=None)
