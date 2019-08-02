#!/usr/bin/python2.7

import sys
import getopt
import requests

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"
batch_size   = 100
ingest_pipeline = ""

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'f:s:p:i:v', ['input-fn=', 
                                                         'elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'ingest-pipeline=', 'pipeline=',
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
    elif opt in ('--ingest-pipeline', '--pipeline'):
        ingest_pipeline = arg
    elif opt in ('-i', '--elastic-index'):
        elastic_index = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True

rejected_fn = input_fn + ".rej"


if "" == ingest_pipeline:
	url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_doc/_bulk"
else:
	url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_doc/_bulk?pipeline=" + ingest_pipeline

print (url)


headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

fp = open (input_fn, "r")
frej = open (rejected_fn, "w")

index_line = '{ "index" : {}}'
bulk_string = index_line
# + "\n" + "line 2"

#print line


for cnt, line in enumerate(fp):
#   print("Line {}: {}".format(cnt, line.strip()))
    bulk_string = bulk_string + "\n" + line
    if 0 == (cnt % batch_size):
        print ("Send at line:" + str(cnt))
        print (bulk_string)
        response = requests.post(url, data=bulk_string, headers=headers)
        bulk_string = index_line
    else:
        bulk_string = bulk_string + index_line
#   cnt += 1
#   response = requests.post(url, data=line, headers=headers)
#   print (response.status_code)
#   if 201 == response.status_code:
#       if True == flag_verbose:
#           print ("OK")
#   else:
#       print ("ERR:" + line)
#       frej.write (line)

print ("Send at line:" + str(cnt))
print (bulk_string)

fp.close ()
frej.close ()

