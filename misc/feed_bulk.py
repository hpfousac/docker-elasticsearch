#!/usr/bin/python3

import sys
import getopt
import requests

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"
batch_size   = 200
ingest_pipeline = ""

user = ""
password = ""

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'f:s:p:i:u:P:v', ['input-fn=', 
                                                         'elastic-server=',
                                                         'elastic-port=', 'port=',
                                                         'user=', 'login=',
                                                         'password=', 'pwd=',
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
    elif opt in ('-u', '--user', '--login'):
        user = arg
    elif opt in ('-P', '--pwd', '--password'):
        password = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True

if ("" != user) and ("" == password):
    print "both parameters user and password has to be specified"
    sys.exit (3)
else:    
    user = user + ":" + password + "@"

rejected_fn = input_fn + ".rej"

if "" == ingest_pipeline:
	url = "http://" + user + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_doc/_bulk"
else:
	url = "http://" + user + elastic_server + ":" + elastic_port + "/" + elastic_index + "/_doc/_bulk?pipeline=" + ingest_pipeline

print (url)


headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

fp = open (input_fn, "r")
frej = open (rejected_fn, "w")

index_line = '{ "index" : {}}'
bulk_string = index_line
# + "\n" + "line 2"

#print line

def sendBulk (url, headers, bulk_string):
    response = requests.post(url, data=bulk_string, headers=headers)
    print (str(response.status_code) + ";" + response.text)
    bulk_string = ""
#   print (response.status_code)
#   if 201 == response.status_code:
#       if True == flag_verbose:
#           print ("OK")
#   else:
#       print ("ERR:" + line)
#       frej.write (line)


for cnt, line in enumerate(fp):
#   print("Line {}: {}".format(cnt, line.strip()))
    bulk_string = bulk_string + index_line + "\n" + line
    if (batch_size - 1) == (cnt % batch_size):
        print ("Send at line:" + str(cnt))
#       print (bulk_string)
        sendBulk (url, headers, bulk_string)
        bulk_string = ""

print ("Send at line:" + str(cnt))
print (bulk_string)
sendBulk (url, headers, bulk_string)

fp.close ()
frej.close ()

sys.exit (0)
