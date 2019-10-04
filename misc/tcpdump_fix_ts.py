#!/usr/bin/python3

import os
import sys
import getopt

import time
import datetime

import requests
import json

# pip install elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"
batch_size   = 100
datespec = ""

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 's:p:i:v', ['elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'datespec=',
                                                         'elastic-index=',
                                                         'verbose'
                                                         ])
#print 'OPTIONS   :', options

for opt, arg in options:
    if opt in ('-s', '--elastic-server'):
        elastic_server = arg
    elif opt in ('-p', '--port', '--elastic-port'):
        elastic_port = arg
    elif opt in ('--datespec'):
        datespec = arg
    elif opt in ('-i', '--elastic-index'):
        elastic_index = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True

def traceLog(message):
	if (True == flag_verbose):
		strtime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d - %H:%M:%S')
		print (strtime + ' TRACE: ' + str(message))

YYYY = datespec[0:4]
MM   = datespec[4:6]
DD   = datespec[6:8]

traceLog (YYYY + ":" + MM + ":" + DD)

search_url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_search"
bulk_url   = "http://" + elastic_server + ":" + elastic_port + "/_bulk"

traceLog ("search_url=" + search_url)
traceLog ("bulk_url="   + bulk_url)

es = Elasticsearch(["http://" + elastic_server + ":" + elastic_port])

headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

index_line = '{ "index" : {}}'
bulk_string = index_line
# + "\n" + "line 2"

#print line

startsecs = 0
endsecs   = 3600 * 6
secsincrement = 900

def tsstring (YYYY, MM, DD, daysecs):
	S = int(daysecs % 60)
	M = int((daysecs / 60) % 60)
	H = int((daysecs / 3600) % 24)
	return '{}-{}-{}T{:02d}:{:02d}:{:02d}'.format(YYYY, MM, DD, H, M, S)

def processDoc (doc):
	traceLog ("doc=" + str(doc))
	doc_id = str(doc["_id"])
#	traceLog ("id=" + doc_id)

	line = doc["_source"]["line"]
	es_index = doc["_index"]
	line_ts = line.split (' ')[0]
#	traceLog ("line_ts=" + line_ts + "; es_index=" + es_index)
	line_ts_HH, line_ts_MM, line_ts_SEC = line_ts.split(':')
#	traceLog ("line_ts_HH=" + line_ts_HH + "; line_ts_MM=" + line_ts_MM + "; line_ts_SEC=" + line_ts_SEC)

	index_ts = es_index.split('-')[2]
#	traceLog ("index_ts=" + index_ts)
	index_YYYY = index_ts[0:4]
	index_MM   = index_ts[4:6]
	index_DD   = index_ts[6:8]

	upd_line1 = '{"update":{"_id":"' + doc_id + '","_index":"' + es_index + '"}}'
	upd_line2 = '{"doc":{"timestamp" : "' + index_YYYY + '-' + index_MM + '-' + index_DD + 'T' + line_ts_HH + ':' + line_ts_MM + ":" + line_ts_SEC + '+00:00"}}'

	traceLog (upd_line1)
	traceLog (upd_line2)

	bulk_update_line = upd_line1 + "\n" + upd_line2 + "\n"
	return bulk_update_line

def doBulkUpdate (update_batch):
	traceLog ("doBulkUpdate (" + update_batch + ")")
	response = requests.post(bulk_url, data=update_batch, headers=headers)
	traceLog ("update_response=" + str(response.status_code))

def processBatch (batch):
	update_batch = ""
	for doc in batch:
		update_batch += processDoc (doc)

#	try:
	traceLog ("update_batch=" + update_batch)
	doBulkUpdate (update_batch)

# 	except Exception as e:
# 				print (str(e))
# 				exc_type, exc_obj, exc_tb = sys.exc_info()
# 				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
# 				print(exc_type, fname, exc_tb.tb_lineno)
# 				cancontinue = 0
# #				traceLog ("update_batch=" + update_batch)
# 				doBulkUpdate (update_batch)
# #				sys.exit (0);





for secs in range(startsecs, endsecs, secsincrement):
	offset = 0
	cancontinue = 1
#	print (secs)
#	print tsstring(YYYY, MM, DD, secs)

	start_ts = tsstring(YYYY, MM, DD, secs)
	end_ts = tsstring(YYYY, MM, DD, secs + secsincrement - 1)
	traceLog ("start_ts=" + start_ts + "; end_ts=" + end_ts )

	res = es.search (index=elastic_index, body={"query": {
    "bool": {
      "filter": [
        {
          "range": {
            "timestamp": {
              "gte": start_ts,
              "lte": end_ts
            }
          }
        }
       ]
    }
  }
 }, size=batch_size, scroll='2m'
)

	traceLog ("res=" + str(res))

	sid = res['_scroll_id']
	scroll_size = len(res['hits']['hits'])

	while scroll_size > 0:

		processBatch (res['hits']['hits'])

		res = es.scroll(scroll_id=sid, scroll='2m')

		# Update the scroll ID
		sid = res['_scroll_id']

		# Get the number of results that returned in the last scroll
		scroll_size = len(res['hits']['hits'])


