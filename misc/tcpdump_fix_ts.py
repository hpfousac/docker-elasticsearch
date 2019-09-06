#!/usr/bin/python3

import os
import sys
import getopt

import time
import datetime

import requests
import json

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"
batch_size   = 100
datespec = ""

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'f:s:p:i:v', ['input-fn=', 
                                                         'elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'datespec=',
                                                         'elastic-index=',
                                                         'verbose'
                                                         ])
#print 'OPTIONS   :', options

for opt, arg in options:
    if opt in ('-f', '--input-fn'):
        input_fn = arg
    elif opt in ('-s', '--elastic-server'):
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
        print(strtime + ' TRACE: ' + str(message) + '\n')
		

YYYY = datespec[0:4]
MM   = datespec[4:6]
DD   = datespec[6:8]

traceLog (YYYY + ":" + MM + ":" + DD)

url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_search"

traceLog (url)

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
	traceLog (doc)
	traceLog (content["hits"]["hits"][docno]["_id"])
	sys.exit (1)

	
for secs in range(startsecs, endsecs, secsincrement):
	offset = 0
	cancontinue = 1
#	print (secs)
#	print tsstring(YYYY, MM, DD, secs)

	while 0 != cancontinue:
		start_ts = tsstring(YYYY, MM, DD, secs)
		end_ts = tsstring(YYYY, MM, DD, secs + secsincrement - 1)
		traceLog ("start_ts=" + start_ts + "; end_ts=" + end_ts )
		query_string = """{
  "size" : """ + str(batch_size) + """,
  "from" : """ + str(offset) + """,
  "stored_fields": [ "_index", "_id" ],
  "_source": [ "timestamp", "line" ],
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "timestamp": {
              "gte": \"""" + start_ts + """\",
              "lte": \"""" + end_ts + """\"
            }
          }
        }

      ]
    }
  }
}"""

#		traceLog (query_string)

		try:
			response = requests.get(url, data=query_string, headers=headers)

			traceLog (url)
#			print (response.status_code)
			content = json.loads(response.text)
#			traceLog (str(content))
			traceLog (str(content["hits"]["total"]["value"]))
#			docs = content["hits"]["total"]["value"]
			for docno in range(0, batch_size):
				doc = content["hits"]["hits"][docno]
				processDoc (doc)
				pass
		except Exception as e:
			print (str(e))
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print(exc_type, fname, exc_tb.tb_lineno)
			cancontinue = 0

		offset += batch_size


#    if 0 == (cnt % batch_size):
#       print ("Send at line:" + str(cnt))
#       print (bulk_string)
#       response = requests.post(url, data=bulk_string, headers=headers)
#       bulk_string = index_line
#   else:
#       bulk_string = bulk_string + index_line
#   cnt += 1
#   response = requests.post(url, data=line, headers=headers)
#   print (response.status_code)
#   if 201 == response.status_code:
#       if True == flag_verbose:
#           print ("OK")
#   else:
#       print ("ERR:" + line)
#       frej.write (line)

#print ("Send at line:" + str(cnt))
#print (bulk_string)

#
