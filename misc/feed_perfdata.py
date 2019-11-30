#!/usr/bin/python3

import os
import sys
import getopt

import time
import datetime
import re

import requests
import json

# pip install elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

## scrolling example:
## https://gist.github.com/hmldd/44d12d3a61a8d8077a3091c4ff7b9307
##

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"
bulk_size   = 200
# http://strftime.org/
indateformat = "%Y-%m-%d %H:%M:%S.%f"
input_fn = ""
elastic_index = "mini-capman"

es_user = ""
es_password = ""

sleepTimeout = 2


#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'f:s:p:i:vu:P:', ['elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'file=',
                                                         'datefmt=',
                                                         'elastic-index=',
                                                         'user=', 'login=',
                                                         'pwd=', 'password=',
                                                         'verbose'
                                                         ])

for opt, arg in options:
    if opt in ('-f', '--file'):
        input_fn = arg
    elif opt in ('-s', '--elastic-server'):
        elastic_server = arg
    elif opt in ('-p', '--port', '--elastic-port'):
        elastic_port = arg
    elif opt in ('--datefmt'):
        indateformat = arg
    elif opt in ('-i', '--elastic-index'):
        elastic_index = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True
    elif opt in ('-u', '--user', '--login'):
        es_user = arg
    elif opt in ('-P', '--pwd', '--password'):
        es_password = arg

def traceLog(message):
	if (True == flag_verbose):
		strtime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d - %H:%M:%S')
		print (strtime + ' TRACE: ' + str(message))

traceLog ("start")

test_ts = "2019-11-09 18:05:00.000"
test_t  = datetime.datetime.strptime(test_ts, indateformat)

traceLog ("test_ts = " + str(test_t))
traceLog ("test_t  = " + str(test_t.strftime ("%Y-%m-%dT%H:%M:%S+00:00")))

def processLine (header, line):
    global indateformat

    record = line.split(";")
    outline = {}

    for col in range(1,len(record)):
        colname = header[col]
        value = record[col]
        if "datetime" == colname:
            value = datetime.datetime.strptime(value, indateformat).strftime ("%Y-%m-%dT%H:%M:%S+00:00")

        if "gmt" == colname:
            value = datetime.datetime.strptime(value, indateformat).strftime ("%Y-%m-%dT%H:%M:%S+00:00")

       	res = re.search("([0-9]+),([0-9]+)", value)
        if res is not None:
            value = float(res.group(1) + "." + res.group(2))

        if "NULL" == value:
            value = 0

        # traceLog (colname + "=" + str(value))
        outline [colname] = value
    
    retval = json.dumps(outline)
    # traceLog ("outline = " + retval)
    return retval 

if ("" != es_user) and ("" == es_password):
    print ("both parameters user and password has to be specified")
    sys.exit (3)
elif ("" != es_user):
    es_user = es_user + ":" + es_password + "@"

fp = open (input_fn, "r")
bulk_import_head ='{"index" : {"_index" : "' + elastic_index  + '"}})'
bulk_string = ""
bulk_items = 0

traceLog ("Openning: " + "http://" + es_user + elastic_server + ":" + elastic_port)
esWriter = Elasticsearch(["http://" + es_user + elastic_server + ":" + elastic_port])

header = {}
for cnt, line in enumerate(fp):
    traceLog ("cnt=" + str(cnt) + ";line=" + line)
    if 0 == cnt:
        header = line.rstrip().lower().split(";")
    else:
        bulk_import_line = processLine (header, line.rstrip())

        bulk_string = bulk_string + bulk_import_head + "\n" + bulk_import_line + "\n"
        bulk_items += 1
        if bulk_size <= bulk_items:
            traceLog ("Writting: " + bulk_string)
            try:
                esWriter.bulk (body=bulk_string)

                if sleepTimeout > 2:
                    sleepTimeout -= 1
                bulk_string = ""
                bulk_items = 0
            except ConnectionTimeout:
                sleepTimeout *= 2
                time.sleep (sleepTimeout)

while 0 < bulk_items:
    traceLog ("Writting: " + bulk_string)
    try:
        esWriter.bulk (body=bulk_string)
        bulk_items = 0
    except ConnectionTimeout:
        pass

fp.close ()

sys.exit (0)
