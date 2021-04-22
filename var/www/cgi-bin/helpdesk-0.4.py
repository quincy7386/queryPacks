#!/usr/bin/env python3

# Written by Jon S. Nelson, jnelson@carbonblack.com (C) 2020
# This script is a POC to show off the Live Query API, and has 
# essentially implemented query packs. 
#
# This script cannot be run by itself, and you should just leverage
# the container that sets up everything for you.


###########  Imports ##############
import cb_helper as cb
import os
import sys
import argparse
import json
import cgitb
import cgi
import errno
import shutil
import string
import struct
from binascii import unhexlify
from datetime import datetime, timedelta

###########  Variables ##############
fin = "pt1.html"
fin2 = "pt2.html"
fout = "/var/www/html/help_desk.html"
# Where the query JSONs are stored
path = "queries"

print("Content-Type: text/html")    # HTML is following
print()
cgitb.enable()

###########  File Handles ##############
fRead = open(fin)
fWrite = open(fout, "w", newline="")
fRead2 = open(fin2)

###########  Functions ##############
# listGen()
# Requires: a list of the names of the queries
# Returns: None
# Writes the top portion of the HTML file and generates the
# navigation list  
def listGen(names,ticket,useCase):
    # Print the top portion of the HTML template
    for line in fRead:
        if 'TICKET_NO' in line:
            fixed = line.replace('TICKET_NO',ticket)
            fWrite.write(fixed)
            continue
        if 'USECASE' in line:
            fixed = line.replace('USECASE',useCase)
            fWrite.write(fixed)
            continue
        else:
            fWrite.write(line)
    # Create each list item and the in-page reference
    for name in names:
        li = '<li><a href="#' + name.replace(' ','_') + '">' + name.replace('.json','') + '</a></li>'
        fWrite.write(li)
    home = '<hr><li><a href="../index.html">Home</a></li>'
    fWrite.write(home)
    saved = '<li><a href="../saved.html">Saved Reports</a></li>'
    fWrite.write(saved)
    endTags = """</ul>
            
        </div>
        <div class="col-sm-9 col-sm-offset-3 col-md-10 col-md-offset-2 main">"""
    fWrite.write(endTags)
# end listGen()

# genTable()
# Requirements: The name of the table and a dictionary of the 
# rows of table data
# Return: None
# Generates the tables for each of the query results
def genTable(name,result,uc):
    # Variables
    cnt = 1
    rows = []
    # Iterate through each result
    for r in result['results']:
        # If we are on the first pass
        if cnt == 1:
            # Then capture the header
            cHeader = list(r['fields'])
            if name == 'Software Utilization.json':
                cHeader.append('days_since_use') 
        # Collect all the row data
        rows.append(r['fields'].values())
        # Increment the counter
        cnt += 1
    # Name the table and create the in-page reference
    section = """<h2 class="sub-header" id=""" + name.replace(' ','_') + """>""" + name.replace('.json','') + """</h2>
        <div class="table-responsive">
            <table class="table table-striped">"""
    h = '<tr><th>' + '<th>'.join(cHeader) + '</th></tr>'
    # Write the table name to the HTML file
    fWrite.write(section)
    # Write the current table header
    fWrite.write(h)
    # Reset counter
    cnt = 0
    # Loop through each row
    while cnt < len(rows):
        # Row tag
        fWrite.write('<tr>')
        # Get each column item
        days = ''
        for item in rows[cnt]:
            if len(str(item)) == 16 and checkHex(item):
                item = convertToDate(item)
                date1 = datetime.date(datetime.today())
                date2 = datetime.date(datetime.strptime(item, "%Y-%m-%d %X"))
                days = abs((date1 - date2).days)
            # Write the table data
            i = f'<td>{item}</td>'
            try:
                fWrite.write(i)
            except (UnicodeEncodeError):
                pass
        # Close the row
        if len(str(days)) > 0:
            fWrite.write(f'<td>{days}</td>')
        fWrite.write('</tr>')
        # Increment the counter
        cnt += 1  
    # Close tags
    fWrite.write("</table></div>")
# end genTable()

# getFormVars()
# Requirements: None
# Return: The ticket number, hostname, and the use case selected in the CGI form
# gets the CGI form data
def getFormVars():
    # Create instance of FieldStorage
    form = cgi.FieldStorage() 
    # Get the ticket number
    ticket = form.getvalue('ticket')
    # Get the hostname
    host = form.getvalue('host')
    # Get the use case
    useCase = form.getvalue('useCase')
    return ticket, host, useCase
# end getFormVars()

# addDeviceID()
# Requirements: The hosts device ID, and the current query JSON file  
# Return: Copies the JSON file to a tmp folder and replaces a 
# placeholder with the device ID
def addDeviceID(deviceID,jFile):
    # Create the path
    jFileTmp = 'tmp/' + jFile
    # See if the directories exist
    if not os.path.exists(os.path.dirname(jFileTmp)):
        # If the don't create them
        try:
            os.makedirs(os.path.dirname(jFileTmp))
        # Check for erros and fail if there are any
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    # Open the query file
    with open(jFile, "r") as jsonIn:
        # Open the tmp query file
        with open(jFileTmp, "w") as jsonOut:
            # Write all the lines
            try:
                for line in jsonIn:
                    # ...but fix the one that needs fixing
                    fixed = line.replace('DEVICE_ID', str(deviceID))
                    # Write the tmp file
                    jsonOut.write(fixed)
            except (UnicodeDecodeError):
                pass
    # Return the full path to the fixed file
    return jFileTmp
def checkHex(value):
    for letter in value:  
             
        # If anything other than hexdigit  
        # letter is present, then return  
        # False, else return True  
        if letter not in string.hexdigits:  
            return False
    return True

def convertToDate(hexValue):
    nt_timestamp = struct.unpack("<Q", unhexlify(hexValue))[0]
    epoch = datetime(1601, 1, 1, 0, 0, 0)
    nt_datetime = epoch + timedelta(microseconds=nt_timestamp / 10)
    return nt_datetime.strftime("%Y-%m-%d %X")

def getUC(useCase):
    if useCase == '1':
        uc = 'Help Desk'
    if useCase == '2':
        uc = 'IT Operations'
    if useCase == '3':
        uc = 'Compliance'
    if useCase == '4':
        uc = 'IR Snapshot'
    if useCase == '5':
        uc = 'Software Utilization Audit'
    return uc

# main()
def main ():
    # Variables
    queryIDs = []
    # Get the CBC config
    cb.getVars()
    # Get the CGI form data
    ticket, host, useCase = getFormVars()
    #ticket = '23424234'
    #host = 'jkfgv5437h'
    #useCase = '1'
    # Get the device ID from the hostname
    deviceID = cb.getDeviceID(host)

    # Set the path for the use case
    path = 'queries/' + useCase
    # Get a list of the JSONs
    try:
        # Check if the dir exists
        items = os.listdir(path)
    except:
        # Throw an error and exit if it doesn't
        print("\nERROR: " + path + " does not exist\n")
        sys.exit()
    # Iterate over the list
    for item in items:
        # Add the path to the filename
        qFile = os.path.join(path,item)
        # Get the query file with the device ID
        qFileTmp = addDeviceID(deviceID,qFile)
        # Create each query and store it's ID
        queryIDs.append(cb.createQuery(cb.baseUrl,qFileTmp,cb.headers))
    ucForTitle = getUC(useCase)
    # Create the navigation list
    listGen(items,ticket,ucForTitle)
    # Reset counter
    iCnt = 0
    # Loop through all the queries
    for id in queryIDs:
        # Check that this query succeeded
        cb.statusCheck(id)
        # Get the query results
        data = cb.getResults(cb.baseUrl,id,cb.headers)
        # Generate the table for this data set
        genTable(items[iCnt],data,ucForTitle)
        cb.deleteQuery(cb.baseUrl,id,cb.headers)
        # Increment the counter
        iCnt += 1
    # Print the tail end of the HTML template
    for line2 in fRead2:
        fWrite.write(line2)
    # Delete the tmp files
    try:
        shutil.rmtree('tmp/queries')
    # Throw an error if the can't be found
    except OSError as e:
        print("Error: %s : %s" % ('tmp/queries', e.strerror))


main()
# Close the file handles
fRead.close()
fRead2.close()
fWrite.close()
print("<h1>Please see your report <a href='http://localhost:8080/help_desk.html'>here</a></h1>")
