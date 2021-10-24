# TAMU-GradeDistribution-Parser: GD_utils.py
# @authors: github/adibarra


# imports
import os
import re
import uuid
import time
import PyPDF2
import requests
from uuid import uuid4
from GD_logger import Logger, Importance
from GD_database import DatabaseHandler
from alive_progress import alive_bar


class Utils:

    """ Class to hold misc. utility methods """

    # all startup tasks go here to declutter the main file
    @staticmethod
    def startup(PreferenceLoader):
        Logger.log('-----------------------', importance=None)
        if PreferenceLoader.loadPrefs():
            Logger.log('Loaded Preferences.', importance=None)
        else:
            Logger.log('Failed to load Preferences. (See console for details).', importance=None)
        Logger.log('Starting up at '+time.strftime("%Y-%m-%d %H:%M:%S"), importance=None)
        Utils.checkDBConnection(importance=None)
        Logger.log('-----------------------\n', importance=None)
        
    # parse grade report pdf returns list
    @staticmethod
    def parseGradesPDFV2(pdfFilename:str):
        tid = uuid4()
        Logger.log('Started parsing full PDF', Importance.INFO, transactionID=tid, final=True)
        try:
            pdfFile = open(pdfFilename,'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFile)
        except PyPDF2.utils.PdfReadError:
            print('Bad PDF: '+pdfFilename)
            return []

        output_list = []
        with alive_bar(total=pdfReader.numPages,title='Parsing '+pdfFilename) as bar:
            for pageNum in range(0,pdfReader.numPages):
                pageObj = pdfReader.getPage(pageNum)
                pageStr = pageObj.extractText().split('\n')
                
                if 'Undergraduate & Graduate' in pageStr:
                    pageStr = pageStr[pageStr.index('Undergraduate & Graduate')+1:]
                elif 'Undergraduate' in pageStr:
                    pageStr = pageStr[pageStr.index('Undergraduate')+1:]
                elif 'Graduate' in pageStr:
                    pageStr = pageStr[pageStr.index('Graduate')+1:]
                
                while len(pageStr) > 0:
                    current = pageStr[0]
                    
                    if current == '':
                        pageStr = pageStr[1:]
                    
                    elif current.lower() == 'cannot':
                        print(pdfFilename+': Found corrupt/error PDF... Skipping')
                        Logger.log('Found corrupt/error PDF... Skipping', Importance.INFO, transactionID=tid, final=True)
                        return output_list
                    
                    elif current in str(['COURSE TOTAL:','DEPARTMENT TOTAL:','COLLEGE TOTAL:']):
                        output_list.append(pageStr[:19])
                        pageStr = pageStr[19:]
                    
                    elif len(current.split('-')) == 3:
                        # check if professorName is blank
                        if len(pageStr) >= 21 and len(pageStr[19].split('-')) == 3 and not len(pageStr[20].split('-')) == 3 and not pageStr[20] in str(['COURSE TOTAL:','DEPARTMENT TOTAL:','COLLEGE TOTAL:']):
                            output_list.append(pageStr[:19]+['N/A'])
                            pageStr = pageStr[19:]
                        else:
                            output_list.append(pageStr[:20])
                            pageStr = pageStr[20:]
                    
                    else:
                        pageStr = pageStr[1:]
                
                bar(1)


        pdfFile.close()
        Logger.log('Finished parsing full PDF', Importance.INFO, transactionID=tid, final=True)
        return output_list

    # Deprecated. broken: check Department: Engineering, Course: PETE Grad Level. Cause may be long names with many spaces
    # parse grade report pdf returns list
    @DeprecationWarning
    @staticmethod
    def parseGradesPDF(pdfFilename:str):
        tid = uuid4()
        Logger.log('Started parsing full PDF', Importance.INFO, transactionID=tid, final=True)
        pdfFile = open(pdfFilename,'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFile)

        output_list = []
        with alive_bar(total=pdfReader.numPages,title='Parsing '+pdfFilename) as bar:
            for pageNum in range(0,pdfReader.numPages):
                pageObj = pdfReader.getPage(pageNum)
                pageStr = pageObj.extractText()
                
                if 'Undergraduate & Graduate' in pageStr:
                    pageStr = pageStr[pageObj.extractText().index('Undergraduate & Graduate')+24:]
                elif 'Undergraduate' in pageStr:
                    pageStr = pageStr[pageObj.extractText().index('Undergraduate')+13:]
                elif 'Graduate' in pageStr:
                    pageStr = pageStr[pageObj.extractText().index('Graduate')+8:]
                
                splitPage = pageStr.split('\n')[1:]

                offset = 0
                for i in range(0, (len(splitPage)//20)+1):
                    section = splitPage[i*20-offset:i*20+20-offset]

                    if len(section) > 1:
                        
                        if section[2] == 'COLLEGE:' and section[3] == 'DEPARTMENT:':
                            # handle corrupt/error pdf
                            print(pdfFilename+': Found corrupt/error PDF... Skipping')
                            Logger.log('Found corrupt/error PDF... Skipping', Importance.INFO, transactionID=tid, final=True)
                            break
                        
                        elif section[0] == 'COURSE TOTAL:':
                            section = splitPage[i*20-offset:i*20+19-offset]
                            offset += 1
                        
                        elif section[0] == 'DEPARTMENT TOTAL:' or section[0] == 'COLLEGE TOTAL:':
                            section = splitPage[i*20-offset:i*20+18-(offset-1)]
                            offset += 1
                        
                        elif len(section) >= 20 and len(str(section[19]).split('-')) == 3:
                            # compensate in case of empty professor name
                            print('HERE',pdfFilename,section)
                            section[19] = 'N/A'
                            offset += 1
                            
                        output_list.append(section)
                bar(1)

        pdfFile.close()
        Logger.log('Finished parsing full PDF', Importance.INFO, transactionID=tid, final=True)
        return output_list
    
    # Deprecated. broken: check Department: Engineering, Course: PETE Grad Level. Cause may be long names with many spaces
    # parse grade report pdf by page returns list
    @DeprecationWarning
    @staticmethod
    def parseGradesPagePDF(pdfFilename:str, pageNum:int):
        tid = uuid4()
        Logger.log('Parsing PDF page '+str(pageNum), Importance.INFO, transactionID=tid, final=True)
        pdfFile = open(pdfFilename,'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFile)

        output_list = []
        pageObj = pdfReader.getPage(pageNum)
        pageStr = pageObj.extractText()
        
        if 'Undergraduate & Graduate' in pageStr:
            pageStr = pageStr[pageObj.extractText().index('Undergraduate & Graduate')+24:]
        elif 'Undergraduate' in pageStr:
            pageStr = pageStr[pageObj.extractText().index('Undergraduate')+13:]
        elif 'Graduate' in pageStr:
            pageStr = pageStr[pageObj.extractText().index('Graduate')+8:]
        
        splitPage = pageStr.split('\n')[1:]

        offset = 0
        for i in range(0, (len(splitPage)//20)+1):
            section = splitPage[i*20-offset:i*20+20-offset]

            if len(section) > 1:
                        
                if section[2] == 'COLLEGE:' and section[3] == 'DEPARTMENT:':
                    # handle corrupt/error pdf
                    print(pdfFilename+': Found corrupt/error PDF... Skipping')
                    Logger.log('Found corrupt/error PDF... Skipping', Importance.INFO, transactionID=tid, final=True)
                    break
                
                elif section[0] == 'COURSE TOTAL:':
                    section = splitPage[i*20-offset:i*20+19-offset]
                    offset += 1
                
                elif section[0] == 'DEPARTMENT TOTAL:' or section[0] == 'COLLEGE TOTAL:':
                    section = splitPage[i*20-offset:i*20+18-(offset-1)]
                    offset += 1
                
                elif len(section) >= 20 and len(str(section[19]).split('-')) == 3:
                    # compensate in case of empty professor name
                    section[19] = 'N/A'
                    offset += 1
                    
                output_list.append(section)
        
        pdfFile.close()
        Logger.log('Finished parsing PDF page '+str(pageNum), Importance.INFO, transactionID=tid, final=True)
        return output_list
    
    # convert parsed list into database format
    @staticmethod
    def convertToEntries(toConvert:list, year:int, semster:str):
        convertedList = []
        try:
            for entry in toConvert:
                if len(entry) == 20 and 'TOTAL'.upper() not in str(entry[0]).upper():
                    convertedList += [[year, semster, entry[0].split('-')[0], entry[0].split('-')[1], entry[0].split('-')[2], int(entry[1]), int(entry[3]), int(entry[5]), 
                                       int(entry[7]), int(entry[9]), float(entry[12]), int(entry[13]), int(entry[14]), int(entry[15]), int(entry[16]), int(entry[17]), int(entry[18]), entry[19]]]
        except:
            print('BAD ENTRY DURING CONVERSION:\n'+str(entry)+'\n'+str([year, semster, entry[0].split('-')[0], entry[0].split('-')[1], entry[0].split('-')[2], entry[1], entry[3], entry[5], 
                entry[7], entry[9], float(entry[12]), entry[13], entry[14], entry[15], entry[16], entry[17], entry[18], entry[19]])+'\n')
        return convertedList

    # download pdf from given url
    @staticmethod
    def loadPDF(downloadURL:str, saveLocation:str='res/temp.pdf', overwrite:bool=False):
        tid = uuid4()
        def downloadPDF():
            Logger.log('Downloading PDF', Importance.INFO, transactionID=tid, final=True)
            response = requests.get(downloadURL)
            with open(saveLocation, 'wb') as f:
                f.write(response.content)
            Logger.log('Finished downloading and saving PDF', Importance.INFO, transactionID=tid, final=True)
        
        Logger.log('Checking if PDF is downloaded', Importance.INFO, transactionID=tid, final=True)
        if os.path.exists(saveLocation):
            if overwrite:
                Logger.log('PDF with name already exists... Overwriting enabled... Overwriting', Importance.INFO, transactionID=tid, final=True)
                downloadPDF()
            else:
                Logger.log('PDF with name already exists... Overwriting disabled...  Skipping', Importance.INFO, transactionID=tid, final=True)
        else:
            downloadPDF()
    
    
    # function to convert list to string for certain formats with padding
    # [[1, 1], [1,1], N] -> 1 : 1\n1 : 1\nN or [[1], [1], N] -> 1\n1\nN
    @staticmethod
    def listToStr(list_to_convert: list, header1='Key', header2='Value', padding=10, headers=True):
        if len(list_to_convert) == 0:
            return '```asciidoc\nEmpty\n```'
        # str header
        if headers:
            longest_first = len(header1)
            longest_second = len(header2)
        else:
            longest_first = 0
            longest_second = 0

        inner_list = None
        for inner_list in list_to_convert:
            if len(inner_list) == 1:
                if len(str(inner_list[0])) > longest_first:
                    longest_first = len(str(inner_list[0]))
            if len(inner_list) == 2:
                if len(str(inner_list[0])) > longest_first:
                    longest_first = len(str(inner_list[0]))
                if len(str(inner_list[1])) > longest_second:
                    longest_second = len(str(inner_list[1]))

        longest_first += 4
        longest_second += 4

        full_str = '```asciidoc\n'
        if headers:
            if len(inner_list) == 2:
                full_str = '```asciidoc\n'+\
                    header1.center(longest_first, ' ')+'    '+header2.center(longest_second, ' ')+'\n'
                full_str += ''.center(longest_first, '=')+'----'+''.center(longest_second, '=')+'\n'

            elif len(inner_list) == 1:
                full_str = '```asciidoc\n'+header1.center(longest_first, ' ')+'\n'
                full_str += ''.center(longest_first, '=')+'\n'

        for inner_list in list_to_convert:
            if len(inner_list) == 2:
                full_str += (str(inner_list[0])+' ').rjust(longest_first)+' :: '+(' '+str(inner_list[1])).ljust(longest_second)+'\n'
            elif len(inner_list) == 1:
                full_str += str(inner_list[0])+'\n'
        return full_str+'```'

    # chunk a list
    @staticmethod
    def chunkList(long_list, chunk_size):
        return [long_list[i*chunk_size:(i+1)*chunk_size] for i in range((len(long_list)+chunk_size-1) // chunk_size)]

    # sanitize inputs for database
    @staticmethod
    def sanitizeForDB(toSanitize: str):
        to_remove = ["'", '"', '\\*', 'CREATE', 'DATABASE', 'INSERT', 'SELECT', 'FROM', 'ALTER', 'ADD', 'DISTINCT',
                     'UPDATE', 'SET', 'DELETE', 'TRUNCATE', 'AS', 'ORDER', 'BY', 'ASC', 'DESC', 'BETWEEN', 'WHERE', 'AND',
                     'OR', 'NOT', 'LIMIT', 'NULL', 'DROP', 'IN', 'JOIN', 'UNION', 'ALL', 'EXISTS', 'LIKE', 'CASE', 'TABLES',
                     'SHOW']

        # remove all instances of strings in to_remove from input string
        for item in to_remove:
            toSanitize = re.sub(('(?i)'+item), '', toSanitize, flags=(re.IGNORECASE))
        return toSanitize

    # check if str is valid int
    @staticmethod
    def isValidInt(string: str):
        try:
            int(string)
            return True
        except ValueError:
            return False

    # check if str is valid float
    @staticmethod
    def isValidFloat(string: str):
        try:
            float(string)
            return True
        except ValueError:
            return False

    # convert seconds to more readable format
    @staticmethod
    def secondsToTime(secondsToConvert: int):
        days = 0
        hours = 0
        minutes = 0
        result_str = ''

        while secondsToConvert >= 60*60*24:
            secondsToConvert -= 60*60*24
            days += 1
        while secondsToConvert >= 60*60:
            secondsToConvert -= 60*60
            hours += 1
        while secondsToConvert >= 60:
            secondsToConvert -= 60
            minutes += 1

        if days > 0:
            if days == 1:
                result_str += str(days)+' day'
            else:
                result_str += str(days)+' days'

        if hours > 0:
            if result_str != '':
                result_str += ' '
            if hours == 1:
                result_str += str(hours)+' hour'
            else:
                result_str += str(hours)+' hours'

        if minutes > 0 and days == 0:
            if result_str != '':
                result_str += ' '
            if minutes == 1:
                result_str += str(minutes)+' minute'
            else:
                result_str += str(minutes)+' minutes'

        if secondsToConvert >= 0 and hours == 0 and days == 0 and not (secondsToConvert == 0 and minutes > 0):
            if result_str != '':
                result_str += ' '
            if secondsToConvert == 1:
                result_str += str(secondsToConvert)+' second'
            else:
                result_str += str(secondsToConvert)+' seconds'
        return result_str

    # check database connection
    @staticmethod
    def checkDBConnection(importance: Importance=Importance.CRIT, transactionID: uuid=None):
        if DatabaseHandler.checkDBConnection():
            Logger.log('Database connection established!', importance)
            return True
        else:
            if importance != None:
                Logger.log('!!! Unable to establish database connection !!! @ '+time.strftime('%Y-%m-%d %H:%M:%S'), importance)
            else:
                Logger.log('!!! Unable to establish database connection !!!', importance)
            Logger.log(DatabaseHandler.checkDBConnectionError(), importance)
            return False