#!/usr/bin/python2.7

import sys
import getopt
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


YYYY = datespec[0:4]
MM   = datespec[4:6]
DD   = datespec[6:8]

print (YYYY + ":" + MM + ":" + DD)

url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_search"

print (url)

headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

index_line = '{ "index" : {}}'
bulk_string = index_line
# + "\n" + "line 2"

#print line

startsecs = 0
endsecs   = 3600 * 24
secsincrement = 5

def tsstring(YYYY, MM, DD, daysecs):
	S = daysecs % 60
	M = (daysecs / 60) % 60
	H = (daysecs / 3600) % 24
	return '{}-{}-{}T{:02d}:{:02d}:{:02d}'.format(YYYY, MM, DD, H, M, S)

for secs in range(startsecs, endsecs, secsincrement):
	offset = 0
	cancontinue = 1
#	print (secs)
#	print tsstring(YYYY, MM, DD, secs)

	while 0 != cancontinue:
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
              "gte": \"""" + tsstring(YYYY, MM, DD, secs) + """\",
              "lte": \"""" + tsstring(YYYY, MM, DD, secs + secsincrement - 1) + """\"
            }
          }
        }

      ]
    }
  }
}"""

#		print query_string

		try:
			response = requests.get(url, data=query_string, headers=headers)

#			print (url)
#			print (response.status_code)
#			print (response.text)
			content = json.loads(response.text)
#			print (content["hits"]["total"]["value"])
			docs = content["hits"]["total"]["value"]
			for docno in range(0, batch_size):
#				print (content["hits"]["hits"][docno]["_id"])
				pass
		except:
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
