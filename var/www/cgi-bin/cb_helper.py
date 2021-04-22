#!/usr/bin/env python3

# Written by Jon S. Nelson, jnelson@carbonblack.com (C) 2020

# This script is a bunch of helper functions to be imported into other scripts 
#
# PREREQS:
# 
# 1. Create a custom PSC connector with the proper level of permissions to access CBLO 
# 2. Your ORG KEY (https://defense-prod05.conferdeploy.net/settings/connectors)
# 3. Modify your ~/.carbonblack/credentials.psc file to match this format with the correct information:
#       [cblo]
#       cbdUrl=https://defense-prod05.conferdeploy.net
#       cbloUrl=https://api-prod05.conferdeploy.net
#       cbloToken=123457AZB7ZYZBITIYLYAC87/12345FIY31
#       cbdToken=12345IYKY3CSQ7HLZ1KIK5ZW/12345Z7C3H
#       orgKey=12345678


# Imports
import requests
import json
import time
import sys
import logging
import configparser
import os

# Set up logging
#logging.basicConfig(filename='helpdesk.log', filemode='w', format='%(asctime)s -- %(levelname)s: %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s -- %(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

###########  Variables ##############
# LiveOps API
baseUrl = "{cbloUrl}/livequery/v1/orgs/{oKey}/runs"
# CBD API
defUrl = "{cbloUrl}/integrationServices/v3/device/"
platformUrl = "{cbloUrl}/appservices/v6/orgs/{oKey}"
# LiveOps headers
headers = {'content-type': 'application/json', 'X-Auth-Token':'', 'Accept-Charset': 'UTF-8'}
# CBD headers 
cbdHeaders = {'content-type': 'application/json', 'X-Auth-Token':'', 'Accept-Charset': 'UTF-8'}
# For sleep timer in seconds
t = 30

################## Functions ###################

# getVars() - this function parses the credentials.psc file and
# gets the ORG Key, the CBD and CBLO tokens, and the API URLs
def getVars():
    # Declare variables global
    global baseUrl
    global defUrl
    global platformUrl
    global headers
    global cbdHeaders
    global orgKey

    # Create new parser
    config = configparser.ConfigParser()
    # Read the config file
    config.read(os.path.expanduser('credentials.psc'))
    # Get the correct URL and ORG Key
    baseUrl = baseUrl.format(cbloUrl = config['cblo']['cbloUrl'], oKey = config['cblo']['orgKey'])
    platformUrl = platformUrl.format(cbloUrl = config['cblo']['cbloUrl'], oKey = config['cblo']['orgKey'])
    # Get the correct URL
    #defUrl = defUrl.format(cbloUrl = config['cblo']['cbloUrl'])
    # Get the CBLO token
    headers['X-Auth-Token'] = config['cblo']['cbloToken']
    orgKey = config['cblo']['orgKey']
    # Get the CBD token
    #cbdHeaders['X-Auth-Token'] = config['cblo']['cbdToken']
# End getVars

# errorCheck() - this function checks the response codes from submitted
# queries and gives human readable feedback.
def errorCheck(rCode):
    jData = rCode.json()
    # Successful LiveOps query submission
    if rCode.status_code == 201:
        log.info("Query successfully started...")
    # Successful CBD API call
    elif rCode.status_code == 200:
        log.info("API call completed successfully...")
    # Errors here on out
    elif rCode.status_code == 400:
        log.error("The JSON body was malformed, or some part of the JSON body included an invalid value")
        log.info("URL used: " + rCode.url)
        log.error("API call success: " + str(jData["success"]))
        log.error("API call message: " + str(jData["message"]))
        sys.exit(1)
    elif rCode.status_code == 401:
        log.error("Unauthorized " +str(rCode.status_code)) + "the API Secret Key or API ID is invalid"
        log.info("URL used: " + rCode.url)
        log.error(rCode.text)
        sys.exit(1)
    elif rCode.status_code == 403:
        log.error("Forbidden " + str(rCode.status_code))
        log.info("URL used: " + rCode.url)
        log.error(rCode.text)
        sys.exit(1)
    elif rCode.status_code == 404:
        log.error("Object not found. Does the target policy exist? " + str(rCode.status_code))
        log.info("URL used: " + rCode.url)
        log.error(rCode.text)
        sys.exit(1)
    else: 
        log.error("Unkown error " + str(rCode.status_code))
        log.info("URL used: " + rCode.url)
        log.error(rCode.text)
        sys.exit(1)
# end errorCheck()

# statusCheck() - this fuction checks to see if the query has
# completed so that the endpoints can be moved. If it has not
# finished then it will sleep for 30 seconds and check again.
def statusCheck(id):
    # Initialize counter
    cnt = 1
    # Infinite loop
    while 1:
        # Construct URL
        statusUrl = baseUrl + "/" + id
        # Make API call
        r = requests.get(statusUrl, headers=headers)
        # Convert to JSON
        jData = r.json()
        # If query still active go to sleep
        if jData["status"] == "ACTIVE":
            if cnt > 1:
                log.info("Still running...")
            # If we have sleep 10 time then we are outside of sensor check in
            if cnt > 10:
                # Let them know something is wrong
                log.warning("One of the targeted endpoints may be offline!!")
            # Let them know we are sleeping
            log.info(str(cnt) + ": Sleeping " + str(t) + " seconds")
            # Go to sleep
            time.sleep(t)
        # Query is done
        elif jData["status"] == "COMPLETE":
            # Let them know
            log.info("Query completed: " + jData['id'])
            # Exit infinite loop
            break
        elif jData["status"] == "CANCELLED":
            # Let them know
            log.info("Query stopped. Exiting...")
            # Exit program
            sys.exit(1)
        # If we got here something went wrong
        else:
            log.warning("Query completed with exceptions:")
            # Show what the status was
            log.warning("Query Status: " + jData["status"])
            # We got errors
            if jData["error_count"] > 0:
                log.error("Completed with errors")
            # Someone did not check in
            if jData["no_match_count"] > 0:
                log.warning("Some devices did not respond")
            break
        # Count our loops
        cnt += 1
# end statusCheck()

# createQuery() - this function create the initial query
# and returns the query ID
def createQuery(baseUrl,payload,headers):
    try:
        with open(payload) as fin:
            jData = json.load(fin)
    except (UnicodeDecodeError):
        pass
    # Make API call in create query
    r = requests.post(baseUrl, data=json.dumps(jData), headers=headers)
    # Check for errors in the API call
    errorCheck(r)
    # Convert to JSON
    jData = r.json()
    # Capture the query ID
    queryId = jData["id"]
    return queryId
# end createQuery

# deleteQuery()
# Deletes a query by the query ID
def deleteQuery(baseUrl,qid,headers):
    # Add the query ID to the URL
    url = baseUrl + '/' + qid
    # Make API call to delete query
    r = requests.delete(url,headers=headers)
    # Check for errors in the API call
    if r.status_code != requests.codes.ok:
        # Log an error
        log.info("Failed to delete: " + qid) 
# end deleteQuery

# getResults() - this function gets the results of the 
# previously run query. It returns the results to be used
# in the movePolicy() function
def getResults(baseUrl,queryID,headers):
    # Construct the URL for API call
    resultsUrl = baseUrl + "/" + queryID + "/results/_search"
    # Make the request
    r = requests.post(resultsUrl, headers=headers, data=json.dumps({}))
    # Check for errors in the call
    errorCheck(r)
    # Convert to JSON
    jData = r.json()
    return jData
# end getResults

def getDeviceID(host):
    # Construct the URL for API call
    resultsUrl = platformUrl + "/devices/_search"
    qFile = {"query":"name:" + host}
    # Make the request
    r = requests.post(resultsUrl, headers=headers, data=json.dumps(qFile))
    # Check for errors in the call
    errorCheck(r)
    # Convert to JSON
    jData = r.json()
    deviceID = jData['results'][0]['id']
    return deviceID
# end getResults 

# movePolicy() - this fuction moves the endpoints to the desired policy
def movePolicy(jData,url):
    # Initialize the counter
    cnt = len(jData["results"])
    # Loop to move each device
    for i in range(cnt):
        # Get the policy from the registry key query
        policy = jData["results"][i]["fields"]["name"]
        # Get the device ID
        device = jData["results"][i]["device"]["id"]
        # Get the device name
        deviceName = jData["results"][i]["device"]["name"]
        # Construct the URL
        defUrl = url + str(device)
        # Create payload
        pData = {"policyName": policy}
        # Make API call
        r = requests.patch(defUrl, data=json.dumps(pData), headers=cbdHeaders)
        # Check for erros in the call
        errorCheck(r)
        # Convert to JSON
        jData = r.json()
        # Print messages on status
        log.info("Moved device: " + deviceName + " to policy: " + policy)
        log.info("Success: " + str(jData["success"]))
        log.info("Message: " + str(jData["message"]))
