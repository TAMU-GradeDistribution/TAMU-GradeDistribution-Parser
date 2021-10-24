# TAMU-GradeDistribution-Parser: GD_database.py
# @authors: github/adibarra


# imports
import uuid
import math
import pymysql
from uuid import uuid4
from GD_logger import Logger, Importance
from GD_prefsloader import PreferenceLoader
from alive_progress import alive_bar


class DatabaseHandler:
    """ This is a class to handle database queries """

    # functions to make retreiving data from the database easier
    @staticmethod
    def checkDBConnection():
        """Checks connection to database.

        Returns:
            bool: True if connection successful, else False
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            rows_affected = cursor.execute('show tables;')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            return False
        return True

    @staticmethod
    def checkDBConnectionError():
        """Checks database connection error.

        Returns:
            str: String representing error, None otherwise
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket,
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            rows_affected = cursor.execute('show tables;')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            return str(e.args[0])+': '+str(e.args[1])
        return 'No Error'
    
    @staticmethod
    def sendQuery(transactionID:uuid, message:str):
        """Send a querty to the database server.
        Parameters:
            transactionID (uuid): The transactionID for current transaction
            message (str): The command to send to the MySQL database
        Returns:
            tuple: Will return tuple of tuples containing the result if no error was encountered
            str: Will return a string if an error was encountered
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket,
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            #Logger.log('>>> Executing DB Query: '+message, Importance.DBUG, transactionID, final=True)
            rows_affected = cursor.execute(message)
            # print(message+' || Affected '+str(rows_affected)+' row(s)')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            Logger.log('>>> Error Executing DB Query: ERROR '+str(e), Importance.WARN, transactionID,final=True)
            return 'ERROR '+str(e)
        return results

    @staticmethod
    def doesTableExist(transactionID:uuid, tableName:str):
        """Checks for table with given name.

        Args:
            transactionID (uuid): The transactionID for current transaction
            tableName (str): Name of the table to check for

        Returns:
            bool: returns true if table with given name does exist
        """

        results = DatabaseHandler.sendQuery(transactionID, 'SHOW TABLES LIKE "'+tableName+'";')

        if len(results) == 0:
            return False
        return True
    
    @staticmethod
    def addGradeEntries(transactionID:uuid, tableName:str, college:str, entrylist:list):
        """Adds a list or single grade report entery to the database

        Args:
            transactionID (uuid): The transactionID for current transaction
            tableName (str): Name of the table to check for
            entry (list): List to add to DB as a record

        Returns:
            tuple: Will return tuple of tuples containing the result if no error was encountered
            str: Will return a string if an error was encountered
        """
        
        def splitToString(entry:list):
            return ('('+str(entry[ 0]).strip()+',"'+str(entry[ 1]).strip()+'","'+str(college)          +'","'+str(entry[ 2]).strip()+'","'+str(entry[ 3]).strip()+'","'+str(entry[ 4]).strip()+'",'+str(entry[ 5]).strip()+','
                       +str(entry[ 6]).strip()+',' +str(entry[ 7]).strip()+ ',' +str(entry[ 8]).strip()+ ',' +str(entry[ 9]).strip()+ ',' +str(entry[10]).strip()+ ',' +str(entry[11]).strip()+ ','+str(entry[12]).strip()+','
                       +str(entry[13]).strip()+',' +str(entry[14]).strip()+ ',' +str(entry[15]).strip()+ ',' +str(entry[16]).strip()+ ',"'+str(entry[17]).strip()+'")')
        
        try:
            Logger.log('Started adding new records to database', Importance.INFO, transactionID, final=True)
            if type(entrylist) == type([]) and len(entrylist) > 0 and type(entrylist[0]) != type([]):
                tid = uuid4()
                Logger.log('Adding new entry to '+tableName, Importance.DBUG, tid)
                results = DatabaseHandler.sendQuery(tid, 'INSERT INTO '+tableName+' '
                    +'(year,semester,college,departmentName,course,section,numA,numB,numC,numD,numF,avgGPA,numI,numS,numU,numQ,numX,numTotal,professorName) VALUES '
                    +splitToString(entrylist)+';')
            
            elif type(entrylist) == type([]) and len(entrylist) > 0 and type(entrylist[0]) == type([]):
                with alive_bar(total=len(entrylist),title='Sending to DB') as bar:
                    tid = uuid4()
                    toAdd = ''
                    results = []
                    rowsAdded = 0
                    batchSize = 50
                    
                    for entry in entrylist:
                        toAdd += splitToString(entry)+'@'
                    
                    toAdd = toAdd[:-1]
                    Logger.log('Adding new entries to '+tableName, Importance.DBUG, tid)
                    
                    # add batchSize at a time until out of records then the remainder
                    toAddSplit = toAdd.split('@')
                    if len(toAddSplit) > batchSize+1:
                            tmpBatchSize = batchSize
                    else:
                        tmpBatchSize = len(toAddSplit)
                    
                    savelen = math.ceil(len(toAddSplit)/tmpBatchSize)
                    for i in range(0, savelen):
                        if len(toAddSplit) > batchSize+1:
                            tmpBatchSize = batchSize
                        else:
                            tmpBatchSize = len(toAddSplit)
                        
                        combined = ''
                        rowsAdded += tmpBatchSize
                        for k in range(0, tmpBatchSize):
                            combined += toAddSplit[k]+','
                        
                        if combined[:-1] != '':
                            results += DatabaseHandler.sendQuery(tid, 'INSERT INTO '+tableName+' '
                                +'(year,semester,college,departmentName,course,section,numA,numB,numC,numD,numF,avgGPA,numI,numS,numU,numQ,numX,numTotal,professorName) VALUES '+combined[:-1]+';')
                        else:
                            rowsAdded -= 1
                        
                        toAddSplit = toAddSplit[tmpBatchSize:]
                        bar(tmpBatchSize)
            
            elif len(entrylist) == 0:
                return ()            
                        
        except pymysql.Error as e:
            Logger.log('>>> Error Executing DB Query: ERROR '+str(e), Importance.WARN, transactionID)
            return 'ERROR '+str(e)
        Logger.log('Finished adding new records ('+str(rowsAdded)+') to database', Importance.INFO, transactionID, final=True)
        return results
    
    @staticmethod
    def bulkQuery(transactionID:uuid, request:str, conditions:list):
        """Batches the query to process request faster

        Args:
            transactionID (uuid): The transactionID for current transaction
            request (str): First part of DB query e.g. 'SELECT * FROM __ WHERE'
            conditions (list): List of strings with query conditions e.g. [['year=2020',avgGPA>2.0],['year=2021',avgGPA>2.0]]

        Returns:
            tuple: Will return tuple of tuples containing the result if no error was encountered
            str: Will return a string if an error was encountered
        """
        
        try:
            Logger.log('Started bulk requesting DB', Importance.INFO, transactionID, final=True)
            with alive_bar(total=len(conditions),title='Sending to DB') as bar:
                tid = uuid4()
                results = []
                batchSize = 50
                
                for i in range(0,len(conditions)):
                    conditionBuilder = '('
                    for condition in conditions[i]:
                        conditionBuilder += str(condition)+' '
                    conditionBuilder = conditionBuilder.replace(' ',' AND ',len(conditions[i])-1)+') OR '
                    conditionBuilder = conditionBuilder.replace(' )',')',)
                    conditions[i] = conditionBuilder
                
                # add batchSize at a time until out of records then the remainder
                if len(conditions) > batchSize:
                        tmpBatchSize = batchSize
                else:
                    tmpBatchSize = len(conditions)
                
                savelen = math.ceil(len(conditions)/tmpBatchSize)
                for i in range(0, savelen):
                    if len(conditions) > batchSize:
                        tmpBatchSize = batchSize
                    else:
                        tmpBatchSize = len(conditions)
                    
                    combined = ''
                    for k in range(0, tmpBatchSize):
                        combined += conditions[k]
                    
                    if combined[:-4] != '':
                        results += DatabaseHandler.sendQuery(tid, request+' '+combined[:-4]+';')
                    conditions = conditions[tmpBatchSize:]
                    bar(tmpBatchSize)
                        
                        
        except pymysql.Error as e:
            Logger.log('>>> Error Executing DB Query: ERROR '+str(e), Importance.WARN, transactionID)
            return 'ERROR '+str(e)
        Logger.log('Finished bulk requesting ('+str(len(conditions))+') requests', Importance.INFO, transactionID, final=True)
        return results