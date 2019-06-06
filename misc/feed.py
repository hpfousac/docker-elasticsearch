#!/usr/bin/python2.7

import requests

elastic_server = "10.245.6.173"
elastic_index = "platform-oracle-in"
input_fn = "/home/david/Downloads/KB-DB/platform-oracle-in_20190606-1523.log"
rejected_fn = input_fn + ".rej"

url = "http://" + elastic_server + ":9200/" + elastic_index + "/record"

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
        print ("OK")
    else:
        print ("ERR")
        frej.write (line)

fp.close ()

