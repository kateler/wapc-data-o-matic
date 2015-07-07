# SCRIPT TO IMPORT WAPC CALL DATA TO ARCGIS
#
# Author: Kate Leroux (kate@mynameiskate.com)
# Created under the direction of Carrie Ulvestad (culvestad@wapc.org)
#
# Summary:
#    This script takes an Excel file containing new call records and
#    cleans, validates, and processes it; appends it to the existing data;
#    and updates the ArcGIS Online feature service.
#
# Table of Contents:
#    Introductory settings (setting variables, importing libraries)
#    1. Import new data table into the geodatabase
#       a. Import table
#       b. Make sure date field isn't null and try again if so
#       c. Make sure date field is in date format
#       d. Only keep today's records
#    2. Clean data
#       a. Change county names to title case
#       b. Remove non-Washington calls and those from unknown counties
#       c. Add spaces to the substance category field for better display
#       d. Make sure number fields are the correct field type
#    3. Geocode the clean data
#       a. Geocode with a county-based address locator
#       b. Stop and complain if there are unmatched records
#    4. Add new data to this month's table
#    5. Delete tables from previous month(s)
#    6. Create separate feature classes for today's cases and this hour's cases
#    7. Create feature class for today's choropleth map
#       a. Calculate number of cases per county for today
#       b. Join today's county totals to the county polygons
#    8. Delete intermediate tables and feature classes
#    9. Update the ArcGIS Online feature service 
#
# Note to user:
#    You may need to change the variables before section 1 if field names or paths change.
#    The rest of the script is less likely to need changes. 
#

## Introductory settings
import time
print "****** Start time: " + time.strftime("%c") + " ******"
from datetime import date, datetime, timedelta
# Add timestamp to print output
def printLog(logString):
    print "[" + time.strftime("%X") + "] " + logString

printLog("Importing arcpy and setting environment...")
import arcpy
import sys
import os
arcpy.SetLogHistory(True)
arcpy.env.overwriteOutput = True
printLog("Done.")

printLog("Setting variables...")

# set variables: directory names
workingDirectory = r"C:\Users\kate\Google Drive\GIS\WAPC Project\Dashboard"
dataDirectory = workingDirectory + "\\call-data"
gdb = workingDirectory + "\\dashboard.gdb"
arcpy.env.workspace = gdb

# set variables: file names
inputDataFile = dataDirectory + "\\Toxdata.xlsx"
addressLocator = "counties_locator"
compareOutput = workingDirectory + "\\table-compare-output.txt"

# set variables: retention of past data
keepPastMonths = False
deletionHour = 1
keepIntTables = True

# set variables: table names
newDataTableOrig = "WAPC_new"
newDataTableToday = "WAPC_new_today"
newDataTableWA = "WAPC_new_wa"
newDataTableGeo = "WAPC_new_geo"
todayUnique = "WAPC_today_unique"
todayCounties = "WAPC_today_by_county"
monthTableCurrent = "WAPC_this_month"
dayTableCurrent = "WAPC_this_day"
hourTableCurrent = "WAPC_this_hour"
countyFC = "county_2010"

# real table name (today)
# monthTable = "WAPC_" + time.strftime("%Y%m")
# for testing
monthTable = "WAPC_201501"

# set variables: fields in new data table
# note: any spaces should be replaced with underscores
zipDataField = "Caller_Info_CallerZip"
countyDataField = "Caller_Info_CallerCounty"
catDataField = "Major_Category_MajorCatDescription"
caseIDDataField = "CaseID"
dateDataField = "Case_Details_StartDate"
stateDataField = "Caller_Info_CallerState_Text"
patAgeField = "Patient_Age_Groupings_PatAgeRange_Toxicall_Text"

# set variables: fields in county feature class
sumCalls = "Num_Today"
countyName = "NAME10"

# set variables: only used for testing
# date format "'yyyy-mm-dd'"
testDate = "'2015-01-01'"
# hour format '0x' (pad with a zero for single digits)
testHour = '23'

printLog("Done.")


## 1. Import new data table into the geodatabase
# 1a. Import table

def importTable():
    if os.path.isfile(inputDataFile):
        printLog("Importing " + inputDataFile + " to " + gdb + " as " + newDataTableOrig + "...")
        arcpy.ExcelToTable_conversion(inputDataFile, gdb + "\\" + newDataTableOrig)
    else:
        printLog("Unable to find " + inputDataFile + ". Exiting.")
        sys.exit()

importTable()

# 1b. Make sure date field isn't null and try again if so
# Sometimes the dates are blank the first time
whereClause = dateDataField + " is null"
nullDates = [row[0] for row in arcpy.da.SearchCursor(newDataTableOrig, (dateDataField), where_clause=whereClause)]
if len(nullDates) > 0:
    print "   Null value(s) found in Start Date field. Trying again..."
    importTable()
    nullDates = [row[0] for row in arcpy.da.SearchCursor(newDataTableOrig, (dateDataField), where_clause=whereClause)]
    if len(nullDates) > 0:
        print "********** ERROR MESSAGE **********"
        printLog(" ")
        print "Null value found in Start Date field. Script should be re-run."
        print "Exiting."
        print "********** ERROR MESSAGE **********"
        sys.exit()
        
printLog("Successfully imported.")


# 1c. Make sure date field is in date format
# (data comes like this: "Jan  1 2015 01:04PM")
dateFieldType = arcpy.ListFields(newDataTableOrig, dateDataField)[0].type
if str(dateFieldType) != 'Date':
    printLog(dateDataField + " type is " + dateFieldType + ". Creating new date field and copying data...")
    arcpy.ConvertTimeField_management(newDataTableOrig, dateDataField, "MMM dd yyyy hh:mmtt;1033;;", "StartDate", "DATE", "'Not Used'")
    arcpy.DeleteField_management(newDataTableOrig, dateDataField)
    arcpy.AlterField_management(newDataTableOrig, "StartDate", dateDataField, dateDataField)
    printLog("Done.")
else:
    printLog(dateDataField + " is already a date field. No need to convert.")


# 1d. Only keep today's records
printLog("Keeping only records from today...")
# real clause (today's date)
# dateWhereClause = dateDataField + " >= date '" + time.strftime("%Y-%m-%d") + "'"
# clause for testing
dateWhereClause = dateDataField + " >= date " + testDate
arcpy.TableSelect_analysis(newDataTableOrig, newDataTableToday, dateWhereClause)
printLog("Done.")


## 2. Clean data
# 2a. Change county names to title case
printLog("Changing county names to title case...")
titleString = "!" + countyDataField + "!.title()"
arcpy.CalculateField_management(newDataTableToday, countyDataField, titleString, "PYTHON_9.3")
printLog("Done.")


# 2b. Remove non-Washington calls and those from unknown counties
printLog("Removing non-WA calls and those from unknown counties...")
stateWhereClause = stateDataField + " = 'WA' AND " + countyDataField + " NOT LIKE 'U%'"
arcpy.TableSelect_analysis(newDataTableToday, newDataTableWA, stateWhereClause)
printLog("Done.")


# 2c. Add spaces to the substance category field for better display
printLog("Adding spaces to substance categories...")
catString = "!" + catDataField + "!.replace('/', ' / ')"
arcpy.CalculateField_management(newDataTableWA, catDataField, catString, "PYTHON_9.3")
printLog("Done.")


# 2d. Make sure number fields are the correct field type
# (if they are auto-detected wrong, the append will fail.)
printLog("Ensuring numeric fields are the correct field type...")

def checkNumberField(table, field, correctType, correctTypeAdd, correctTypeFunc, tempName):
    fieldType = arcpy.ListFields(table, field)[0].type
    if str(fieldType) != correctType:
        print "   " + field + " type is " + fieldType + ". Creating new " + correctType + " field and copying data..."
        arcpy.AddField_management(table, tempName, correctTypeAdd)
        newString = correctTypeFunc + "( !" + field + "! )"
        arcpy.CalculateField_management(table, tempName, newString, "PYTHON_9.3")
        arcpy.DeleteField_management(table, field)
        arcpy.AlterField_management(table, tempName, field, field)
    else:
        print "   " + field + " is already " + correctType +" type. No need to convert."

checkNumberField(newDataTableWA, zipDataField, "String", "STRING", "str", "ZipCode")
printLog("Done.")


## 3. Geocode the clean data
# 3a. Geocode with a county-based address locator
printLog("Geocoding " + newDataTableWA + " with " + addressLocator + "...")
geoFields = "'Single Line Input' '" + countyDataField + "' VISIBLE NONE"
arcpy.GeocodeAddresses_geocoding(newDataTableWA, addressLocator, geoFields, newDataTableGeo, "STATIC")
printLog("Done.")


# 3b. Stop and complain if there are unmatched records
counties = [row[0] for row in arcpy.da.SearchCursor(newDataTableGeo, (countyDataField), where_clause="Status = 'U'")]
uniqueCounties = sorted(set(counties))
for county in uniqueCounties:
    print "   Unmatched: " + county
if len(counties) > 0:
    print ""
    print "********** ERROR MESSAGE **********"
    print "The counties listed above were not matched"
    print "and therefore the new data file was NOT ADDED."
    print "********** ERROR MESSAGE **********"
    print ""
    sys.exit()


## 4. Add new data to this month's table
printLog("Adding new data to this month's table (" + monthTable + ")...")
if not arcpy.Exists(monthTable):
    print "   " + monthTable + " doesn't exist. Copying new data table to " + monthTable + "."
    arcpy.CopyFeatures_management(newDataTableGeo, monthTable)
else:
    try:
        arcpy.Append_management(newDataTableGeo, monthTable, "TEST", "", "")
    except:
        print ""
        print "********** ERROR MESSAGE **********"
        printLog(" ")
        print "Appending to master table failed, probably because the table schemas don't match."
        arcpy.TableCompare_management(monthTable, newDataTableGeo, "ObjectID", "SCHEMA_ONLY", "", "", "", "CONTINUE_COMPARE", compareOutput)
        print "See " + compareOutput + "for more details."
        print "********** ERROR MESSAGE **********"
        print ""
        sys.exit()

doneInputDataFile = inputDataFile[:-5] + "_" + time.strftime("%Y%m%d_%H%M") + ".xlsx"
os.rename(inputDataFile, doneInputDataFile)
print "   Success. Renamed input file to " + doneInputDataFile + "."
print "   If this script is run again on the same file, it will create duplicate records (not recommended)."
arcpy.CopyFeatures_management(monthTable, monthTableCurrent)
printLog("Done.")


## 5. Delete tables from previous month(s)
if keepPastMonths == False:
    printLog("Checking for old data tables...")
    currentHour = int(time.strftime("%H"))
    if currentHour >= deletionHour:
        tables = arcpy.ListFeatureClasses("WAPC_2*")
        for table in tables:
            if table != monthTable:
                print "   Deleting " + table + "."
                arcpy.Delete_management(table)
    else:
        print "    Skipping deletion because it is before " + str(deletionHour) + ":00."
    printLog("Done.")


## 6. Create separate feature classes for today's cases and this hour's cases

# TODAY:    
# real clause (today's date)
# todayWhereClause = dateDataField + " >= date '" + time.strftime("%Y-%m-%d") + "'"

# use clause below to hardcode for testing
todayWhereClause = dateDataField + " >= date " + testDate

arcpy.FeatureClassToFeatureClass_conversion(monthTable, gdb, dayTableCurrent, todayWhereClause)

# THIS HOUR: 
# real clause (uses last 60 minutes)
# lastHour = datetime.now() - timedelta(minutes=60)
# hourWhereClause = dateDataField + " >= date '" + datetime.strftime(lastHour, "%Y-%m-%d %H:%M:%S") + "'"

# the clause below will use the current hour, in case that's needed
# hourWhereClause = "EXTRACT(HOUR FROM \"" + dateDataField + "\") = " + time.strftime("%H")

# use clause below to hardcode for testing
hourWhereClause = "EXTRACT(HOUR FROM \"" + dateDataField + "\") >= " + testHour

arcpy.FeatureClassToFeatureClass_conversion(dayTableCurrent, gdb, hourTableCurrent, hourWhereClause)


## 7. Create feature class for today's choropleth map
# 7a. Calculate number of cases per county for today
printLog("Calculating the number of cases per county for today...")
arcpy.TableToTable_conversion(dayTableCurrent, gdb, todayUnique, "")
arcpy.DeleteIdentical_management(todayUnique, caseIDDataField, "", "0")
arcpy.Frequency_analysis(todayUnique, todayCounties, countyDataField, "")
arcpy.AlterField_management(todayCounties, "FREQUENCY", sumCalls, sumCalls)
printLog("Done.")


# 7b. Join today's county totals to the county polygons
printLog("Joining today's totals to the county polygons...")
arcpy.DeleteField_management(countyFC, sumCalls)
arcpy.JoinField_management(countyFC, countyName, todayCounties, countyDataField, sumCalls)
# replace nulls with zeros
whereClause = sumCalls + " is null"
table = arcpy.UpdateCursor(countyFC, where_clause=whereClause)
for row in table:
     row.setValue(sumCalls, 0)
     table.updateRow(row)
printLog("Done.")


## 8. Delete intermediate tables and feature classes
if keepIntTables == False:
    printLog("Deleting intermediate tables and feature classes...")
    arcpy.Delete_management(newDataTableOrig)
    arcpy.Delete_management(newDataTableToday)
    arcpy.Delete_management(newDataTableWA)
    arcpy.Delete_management(newDataTableGeo)
    arcpy.Delete_management(todayUnique)
    arcpy.Delete_management(todayCounties)
    printLog("Done.")


## 9. Update the ArcGIS Online feature service
# note: settings for this section are in update_settings.ini
# it requires the requests and requests-master directories
# this section came from here: https://github.com/arcpy/update-hosted-feature-service
# instructions: http://blogs.esri.com/esri/arcgis/2014/01/24/updating-your-hosted-feature-service-for-10-2/

# Copyright 2013 Esri
# portions copyright 2015 Kate Leroux

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at

#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

    
def updateAGOL():
    # START OF IMPORTED SCRIPT
    # Import system modules
    import urllib, urllib2, json
    import requests
    import ConfigParser
    from xml.etree import ElementTree as ET

    class AGOLHandler(object):    
        
        def __init__(self, username, password, serviceName):
            self.username = username
            self.password = password
            self.serviceName = serviceName
            self.token, self.http = self.getToken(username, password)
            self.itemID = self.findItem("Feature Service")
            self.SDitemID = self.findItem("Service Definition")
            
        def getToken(self, username, password, exp=60):
            
            referer = "http://www.arcgis.com/"
            query_dict = {'username': username,
                          'password': password,
                          'expiration': str(exp),
                          'client': 'referer',
                          'referer': referer,
                          'f': 'json'}   
            
            query_string = urllib.urlencode(query_dict)
            url = "https://www.arcgis.com/sharing/rest/generateToken"
            
            token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
            
            if "token" not in token:
                print token['error']
                sys.exit()
            else: 
                httpPrefix = "http://www.arcgis.com/sharing/rest"
                if token['ssl'] == True:
                    httpPrefix = "https://www.arcgis.com/sharing/rest"
                    
                return token['token'], httpPrefix
                
        def findItem(self, findType):
            #
            # Find the itemID of whats being updated
            #        
            searchURL = self.http + "/search"
            
            query_dict = {'f': 'json',
                          'token': self.token,
                          'q': "title:\""+ self.serviceName + "\"AND owner:\"" + self.username + "\" AND type:\"" + findType + "\""}    
            
            jsonResponse = sendAGOLReq(searchURL, query_dict)
            
            if jsonResponse['total'] == 0:
                print "\nCould not find a service to update. Check the service name in the update_settings.ini"
                sys.exit()
            else:
                print("found {} : {}").format(findType, jsonResponse['results'][0]["id"])    
            
            return jsonResponse['results'][0]["id"]
                

    def urlopen(url, data=None):
        # monkey-patch URLOPEN
        referer = "http://www.arcgis.com/"
        req = urllib2.Request(url)
        req.add_header('Referer', referer)

        if data:
            response = urllib2.urlopen(req, data)
        else:
            response = urllib2.urlopen(req)

        return response


    def makeSD(MXD, serviceName, tempDir, outputSD, maxRecords):
        #
        # create a draft SD and modify the properties to overwrite an existing FS
        #    
        
        arcpy.env.overwriteOutput = True
        # All paths are built by joining names to the tempPath
        SDdraft = os.path.join(tempDir, "tempdraft.sddraft")
        newSDdraft = os.path.join(tempDir, "updatedDraft.sddraft")    
         
        arcpy.mapping.CreateMapSDDraft(MXD, SDdraft, serviceName, "MY_HOSTED_SERVICES")
        
        # Read the contents of the original SDDraft into an xml parser
        doc = ET.parse(SDdraft)  
        
        root_elem = doc.getroot()
        if root_elem.tag != "SVCManifest":
            raise ValueError("Root tag is incorrect. Is {} a .sddraft file?".format(SDDraft))
        
        # The following 6 code pieces modify the SDDraft from a new MapService
        # with caching capabilities to a FeatureService with Query,Create,
        # Update,Delete,Uploads,Editing capabilities as well as the ability to set the max
        # records on the service.
        # The first two lines (commented out) are no longer necessary as the FS
        # is now being deleted and re-published, not truly overwritten as is the 
        # case when publishing from Desktop.
        # The last three pieces change Map to Feature Service, disable caching 
        # and set appropriate capabilities. You can customize the capabilities by
        # removing items.
        # Note you cannot disable Query from a Feature Service.
        
        #doc.find("./Type").text = "esriServiceDefinitionType_Replacement" 
        #doc.find("./State").text = "esriSDState_Published"
        
        # Change service type from map service to feature service
        for config in doc.findall("./Configurations/SVCConfiguration/TypeName"):
            if config.text == "MapServer":
                config.text = "FeatureServer"
        
        #Turn off caching
        for prop in doc.findall("./Configurations/SVCConfiguration/Definition/" +
                                    "ConfigurationProperties/PropertyArray/" +
                                    "PropertySetProperty"):
            if prop.find("Key").text == 'isCached':
                prop.find("Value").text = "false"
            if prop.find("Key").text == 'maxRecordCount':
                prop.find("Value").text = maxRecords
        
        # Turn on feature access capabilities
        for prop in doc.findall("./Configurations/SVCConfiguration/Definition/Info/PropertyArray/PropertySetProperty"):
            if prop.find("Key").text == 'WebCapabilities':
                prop.find("Value").text = "Query,Create,Update,Delete,Uploads,Editing"

        # Add the namespaces which get stripped, back into the .SD    
        root_elem.attrib["xmlns:typens"] = 'http://www.esri.com/schemas/ArcGIS/10.1'
        root_elem.attrib["xmlns:xs"] ='http://www.w3.org/2001/XMLSchema'

        # Write the new draft to disk
        with open(newSDdraft, 'w') as f:
            doc.write(f, 'utf-8')
            
        # Analyze the service
        analysis = arcpy.mapping.AnalyzeForSD(newSDdraft)
         
        if analysis['errors'] == {}:
            # Stage the service
            arcpy.StageService_server(newSDdraft, outputSD)
            print "Created {}".format(outputSD)
                
        else:
            # If the sddraft analysis contained errors, display them and quit.
            print analysis['errors']
            sys.exit()
               
    def upload(fileName, tags, description): 
        #
        # Overwrite the SD on AGOL with the new SD.
        # This method uses 3rd party module: requests
        #
        
        updateURL = agol.http+'/content/users/{}/items/{}/update'.format(agol.username, agol.SDitemID)
            
        filesUp = {"file": open(fileName, 'rb')}
        
        url = updateURL + "?f=json&token="+agol.token+ \
            "&filename="+fileName+ \
            "&type=Service Definition"\
            "&title="+agol.serviceName+ \
            "&tags="+tags+\
            "&description="+description
            
        response = requests.post(url, files=filesUp);     
        itemPartJSON = json.loads(response.text)
        
        if "success" in itemPartJSON:
            itemPartID = itemPartJSON['id']
            print("updated SD:   {}").format(itemPartID)
            return True
        else:
            print "\n.sd file not uploaded. Check the errors and try again.\n"  
            print itemPartJSON
            sys.exit()        
        
        
    def publish():
        #
        # Publish the existing SD on AGOL (it will be turned into a Feature Service)
        #
        
        publishURL = agol.http+'/content/users/{}/publish'.format(agol.username)
        
        query_dict = {'itemID': agol.SDitemID,
                  'filetype': 'serviceDefinition',
                  'overwrite': 'true',
                  'f': 'json',
                  'token': agol.token}    
        
        jsonResponse = sendAGOLReq(publishURL, query_dict)
                
        print("successfully updated...{}...").format(jsonResponse['services'])
        
        return jsonResponse['services'][0]['serviceItemId']
        

    def enableSharing(newItemID, everyone, orgs, groups):
        #
        # Share an item with everyone, the organization and/or groups
        #
        shareURL = agol.http+'/content/users/{}/items/{}/share'.format(agol.username, newItemID)

        if groups == None:
            groups = ''
        
        query_dict = {'f': 'json',
                      'everyone' : everyone,
                      'org' : orgs,
                      'groups' : groups,
                      'token': agol.token}    
        
        jsonResponse = sendAGOLReq(shareURL, query_dict)
        
        print("successfully shared...{}...").format(jsonResponse['itemId'])    
        
        
        
    def sendAGOLReq(URL, query_dict):
        #
        # Helper function which takes a URL and a dictionary and sends the request
        #
        
        query_string = urllib.urlencode(query_dict)    
        
        jsonResponse = urllib.urlopen(URL, urllib.urlencode(query_dict))
        jsonOuput = json.loads(jsonResponse.read())
        
        wordTest = ["success", "results", "services", "notSharedWith"]
        if any(word in jsonOuput for word in wordTest):
            return jsonOuput    
        else:
            print "\nfailed:"
            print jsonOuput
            sys.exit()
            
        
    if __name__ == "__main__":
        #
        # start
        #
        
        print "Starting Feature Service publish process"
        
        # Find and gather settings from the ini file
        localPath = sys.path[0]
        settingsFile = os.path.join(localPath, "update_settings.ini")

        if os.path.isfile(settingsFile):
            config = ConfigParser.ConfigParser()
            config.read(settingsFile)
        else:
            print "INI file not found. \nMake sure a valid 'update_settings.ini' file exists in the same directory as this script."
            sys.exit()
        
        # AGOL Credentials
        inputUsername = config.get( 'AGOL', 'USER')
        inputPswd = config.get('AGOL', 'PASS')

        # FS values
        MXD = config.get('FS_INFO', 'MXD')
        serviceName = config.get('FS_INFO', 'SERVICENAME')   
        tags = config.get('FS_INFO', 'TAGS')
        description = config.get('FS_INFO', 'DESCRIPTION')
        maxRecords = config.get('FS_INFO', 'MAXRECORDS')
        
        # Share FS to: everyone, org, groups
        shared = config.get('FS_SHARE', 'SHARE')
        everyone = config.get('FS_SHARE', 'EVERYONE')
        orgs = config.get('FS_SHARE', 'ORG')
        groups = config.get('FS_SHARE', 'GROUPS')  #Groups are by ID. Multiple groups comma separated
        
        
        # create a temp directory under the script     
        tempDir = os.path.join(localPath, "tempDir")
        if not os.path.isdir(tempDir):
            os.mkdir(tempDir)  
        finalSD = os.path.join(tempDir, serviceName + ".sd")  

        #initialize AGOLHandler class
        agol = AGOLHandler(inputUsername, inputPswd, serviceName)
        
        # Turn map document into .SD file for uploading
        makeSD(MXD, serviceName, tempDir, finalSD, maxRecords)
        
        # overwrite the existing .SD on arcgis.com
        
        if upload(finalSD, tags, description):
            
            # publish the sd which was just uploaded
            newItemID = publish()
            
            # share the item
            if shared:
                enableSharing(newItemID, everyone, orgs, groups)
                
            print "\nfinished."
        # END OF IMPORTED SCRIPT


printLog("Updating the ArcGIS Online feature service...")
try:
    updateAGOL()
    printLog("Done.")
except:
    print "Update failed. Trying one more time..."
    try:
        updateAGOL()
        printLog("Done.")
    except:
        print ""
        print "********** ERROR MESSAGE **********"
        print ""
        print "Update to ArcGIS Online failed!"
        print ""
        print "********** ERROR MESSAGE **********"
        print ""

print "****** End time: " + time.strftime("%c") + " ******"



