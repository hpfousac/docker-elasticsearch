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

## scrolling example:
## https://gist.github.com/hmldd/44d12d3a61a8d8077a3091c4ff7b9307
##

flag_verbose = False

##
## ES parameters
##
elastic_server = "localhost"
elastic_port = "9200"
bulk_size   = 100

##
## Mandatory fields
##
datespec = ""
collector_host = ""
collector_iface = ""

src_elastic_index = ""
dst_elastic_index = ""

##
## Tracing
##
def out_text (line):
	strtime = datetime.fromtimestamp(time.time()).strftime('%Y/%m/%d - %H:%M:%S')
	sys.stderr.write (strtime + ": " + line + "\n")

def error_msg (msg):
	out_text ("ERROR: " + msg)

def trace_msg (msg):
	global flag_verbose
	if True == flag_verbose:
		out_text ("TRACE: " + msg)

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'S:P:H:I:i:o:v', ['elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'datespec=',
                                                         'src-elastic-index=', 'src-index=',
                                                         'dst-elastic-index=', 'dst-index=',
                                                         'verbose'
                                                         ])
#print 'OPTIONS   :', options

for opt, arg in options:
    if opt in ('-S', '--elastic-server'):
        elastic_server = arg
    elif opt in ('-P', '--port', '--elastic-port'):
        elastic_port = arg
    elif opt in ('--datespec'):
        datespec = arg
    elif opt in ('-i', '--src-index', '--src-elastic-index'):
        src_elastic_index = arg
    elif opt in ('-o', '--dst-index', '--dst-elastic-index'):
        dst_elastic_index = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True
    elif opt in ('-H', '--collector-host'):
        collector_host = arg
# trace_msg ("Set collector host (field: src.host): " + collector_host)
    elif opt in ('-I', 'collector-iface', 'iface', 'collector-interface', 'interface'):
        collector_iface = arg
# trace_msg ("Set collector interface (field: src.iface): " + collector_iface)

def traceLog(message):
	if (True == flag_verbose):
		strtime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y %m %d - %H:%M:%S')
		print (strtime + ' TRACE: ' + str(message))

YYYY = datespec[0:4]
MM   = datespec[4:6]
DD   = datespec[6:8]

traceLog (YYYY + ":" + MM + ":" + DD)

search_url = "http://" + elastic_server + ":" + elastic_port + "/" + src_elastic_index + "/_search"
bulk_url   = "http://" + elastic_server + ":" + elastic_port + "/_bulk"

traceLog ("search_url=" + search_url)
traceLog ("bulk_url="   + bulk_url)

esReader = Elasticsearch(["http://" + elastic_server + ":" + elastic_port])
esWriter = Elasticsearch(["http://" + elastic_server + ":" + elastic_port])

startsecs = 0
endsecs   = 3600 * 24
secsincrement = 300 # 5 min

bulk_import_head ='{"index" : {"_index" : "' + dst_elastic_index + "-" + datespec + '"}})'

def tsstring (YYYY, MM, DD, daysecs):
	S = int(daysecs % 60)
	M = int((daysecs / 60) % 60)
	H = int((daysecs / 3600) % 24)
	return '{}-{}-{}T{:02d}:{:02d}:{:02d}'.format(YYYY, MM, DD, H, M, S)

def processDoc (doc):
	traceLog ("doc=" + str(doc))
	doc_id = str(doc["_id"])
#	traceLog ("id=" + doc_id)

	octets = doc["_source"]["pkt.len"]
#doc_timestamp    = doc["_source"]["timestamp"]
#	doc_timestamp_ms = doc["_source"]["timestamp_ms"]

#	traceLog ("octets=" + str(octets))

	return int(octets)

def doBulkUpdate (update_batch):
	traceLog ("doBulkUpdate (" + update_batch + ")")
	esWriter.bulk (body=update_batch)

def processBatch (batch):
	packets = 0
	octets  = 0
	for doc in batch:
		octets += processDoc (doc)
		packets += 1

	return packets, octets

bulk_string = ""

for secs in range(startsecs, endsecs, secsincrement):
	offset = 0
	cancontinue = 1
#	print (secs)
#	print tsstring(YYYY, MM, DD, secs)

	start_ts = tsstring(YYYY, MM, DD, secs)
	end_ts = tsstring(YYYY, MM, DD, secs + secsincrement - 1)
	traceLog ("start_ts=" + start_ts + "; end_ts=" + end_ts )

	res = esReader.search (index=src_elastic_index, body={"query": {
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
				],
				"must" : [
					{ "term" :  
						{ "src.host" : collector_host }
					},
					{ "term" : 
						{ "src.iface" : collector_iface }
					}
				]
			}
		}
	}, size=bulk_size, scroll='2m'
)

	traceLog ("res=" + str(res))

	sid = res['_scroll_id']
	traceLog ("_scroll_id=" + sid)
	scroll_size = len(res['hits']['hits'])

	interval_octets = 0
	interval_packets = 0

	while scroll_size > 0:

		packets, octets = processBatch (res['hits']['hits'])
		interval_packets += packets
		interval_octets  += octets

		res = esReader.scroll(scroll_id=sid, scroll='1m')

		# Update the scroll ID
		sid = res['_scroll_id']
		traceLog ("_scroll_id=" + sid)

		# Get the number of results that returned in the last scroll
		scroll_size = len(res['hits']['hits'])

	esReader.clear_scroll (scroll_id=sid)

	record = {}
	record ["src.host"] = collector_host
	record ["src.iface"] = collector_iface
	record ["@timestamp"] = start_ts
	record ["interval"]   = secsincrement

	record ["ts.year"]    = int (YYYY)
	record ["ts.month"]   = int (MM)
	record ["ts.day"]     = int (DD)
	record ["ts.weekday"] = datetime.date(int(YYYY), int(MM), int(DD)).weekday()
	record ["ts.hour"]    = int (secs / 3600)
	record ["ts.minute"]  = int ((secs % 3600) / 60)
	record ["ts.second"]  = int (secs % 60)

	record ["packets"]    = interval_packets
	record ["octets"]     = interval_octets

	bulk_import_line = json.dumps(record)
	traceLog ("Consolidated: " + bulk_import_line)
	bulk_string = bulk_string + bulk_import_head + "\n" + bulk_import_line + "\n"

traceLog ("Writting: " + bulk_string)
esWriter.bulk (body=bulk_string)



