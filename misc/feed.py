#!/usr/bin/python2.7

import sys
import getopt
import requests

flag_verbose = False
elastic_server = "localhost"
elastic_port = "9200"

#print 'ARGV      :', sys.argv[1:]
options, remainder = getopt.getopt(sys.argv[1:], 'f:s:p:i:v', ['input-fn=', 
                                                         'elastic-server=',
                                                         'elastic-port=', 'port=',
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
    elif opt in ('-i', '--elastic-index'):
        elastic_index = arg
    elif opt in ('-v', '--verbose'):
        flag_verbose = True

#elastic_server = "10.245.6.173"
#elastic_index = "platform-oracle-in"
#input_fn = "/home/david/Downloads/KB-DB/platform-oracle-in_20190606-1523.log"
rejected_fn = input_fn + ".rej"

url = "http://" + elastic_server + ":" + elastic_port + "/" + elastic_index + "/record"

headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}

fp = open (input_fn, "r")
frej = open (rejected_fn, "w")

#cnt = 0
#while (line = fp.readline ()):

for cnt, line in enumerate(fp):
#   print("Line {}: {}".format(cnt, line.strip()))
#   cnt += 1
    response = requests.post(url, data=line, headers=headers)
#   print (response.status_code)
    if 201 == response.status_code:
        if True == flag_verbose:
            print ("OK")
    else:
        print ("ERR")
        frej.write (line)

fp.close ()
frej.close ()

