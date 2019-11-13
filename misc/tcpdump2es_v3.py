#!/usr/bin/python3

import sys
import getopt
import time
from datetime import datetime
import re
from collections import namedtuple
import json

from elasticsearch import Elasticsearch

##
## ES parameters
##
elastic_server = "localhost"
elastic_port = "9200"
bulk_size   = 100
elastic_index = ""


##
## Mandatory fields
##
collector_host = ""
collector_iface = ""

##
## base formatting
##  tcpdump -p -i ${IFACE} -n -nn ...
##

defTF     = "%d.%m.%Y_%H:%M:%S"
tcpdumpTF = "%H:%M:%S"
dayTF     = "%d.%m.%Y"

IPv4_unknown = "0.0.0.0/0"

now = datetime.now()
today = now.strftime (dayTF)
today_sec = datetime.strptime(today, dayTF).timestamp ()

additional_tags = {}

es_user = ""
es_password = ""

verbose_flag = False
source_flag = False

# used for rolling from 23:59:?? to 00:??:??
last_ts = today_sec ## in number of seconds from begginig of the era

def out_text (line):
	strtime = datetime.fromtimestamp(time.time()).strftime('%Y/%m/%d - %H:%M:%S')
	sys.stderr.write (strtime + ": " + line + "\n")

def error_msg (msg):
	out_text ("ERROR: " + msg)

def trace_msg (msg):
	global verbose_flag
	if True == verbose_flag:
		out_text ("TRACE: " + msg)

trace_msg ("today=" + today + "; today_sec=" + str(today_sec))


def add_tags (tags):
	trace_msg ("add_tag (" + tags + ");")

	for tag in tags.split (","):
		s1 = tag.split ("=")
		if 2 == len (s1):
			trace_msg ("adding tag: " + s1[0] + "=" + s1[1])
			additional_tags[s1[0]] = s1[1]
		else:
			error_msg ("Invalid parameter -tag " + tag)

def extract_pktlen (line):
	trace_msg ("extract_pktlen (" + line + ");")

	res = re.search("length ([0-9]+)", line)
	if res is not None:
		trace_msg ("extracted pkt_len: (" + str(res.group(1)) + ");")
		return int(res.group(1))

	return 0

def extract_src (line):
	trace_msg ("extract_src (" + line + ");")

## IPv4 (ip)+(port)
	res = re.search("([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\.([0-9]+) > ", line)
	if res is not None:
		trace_msg ("extracted IPv4 (src ip+port): (" + str(res.group(1)) + ":" + str(res.group(2)) + ");")
		return res.group(1) + "/32", int(res.group(2))

## IPv4 (ip)
	res = re.search("([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) > ", line)
	if res is not None:
		trace_msg ("extracted IPv4 (src ip): (" + str(res.group(1)) + ");")
		return res.group(1) + "/32", 0

## IPv6 (ip)+(port)
	res = re.search("IP6 ([0-9a-f:]+)\.([0-9]+) > ", line)
	if res is not None:
		trace_msg ("extracted IPv6 (src ip+port): (" + str(res.group(1)) + ":" + str(res.group(2)) + ");")
		return res.group(1) + "/128", int(res.group(2))

## IPv6 (ip) without port
	res = re.search("IP6 ([0-9a-f:]+) > ", line)
	if res is not None:
		trace_msg ("extracted IPv6 (src ip): (" + str(res.group(1)) + ");")
		return res.group(1) + "/128", 0

## IPv4 ARP
	res = re.search(" ARP, Request who-has ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) tell ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", line)
	if res is not None:
		trace_msg ("extracted ARP (src ip): (" + str(res.group(2)) + ");")
		return res.group(2) + "/32", 0

	return IPv4_unknown, 0

def extract_dst (line):
	trace_msg ("extract_dst (" + line + ");")

## IPv4 (ip)+(port)
	res = re.search("> ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\.([0-9]+): ", line)
	if res is not None:
		trace_msg ("extracted IPv4 (dst ip+port): (" + str(res.group(1)) + ":" + str(res.group(2)) + ");")
		return res.group(1) + "/32", int(res.group(2))

## (ipv4 no port):
## 01:25:04.146602 IP 172.24.16.3 > 104.208.243.111: ICMP echo reply, id 16612, seq 4, length 64
	res = re.search("> ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+): ", line)
	if res is not None:
		trace_msg ("extracted IPv4 (dst ip): (" + str(res.group(1)) + ");")
		return res.group(1) + "/32", 0

# ## IPv6 (ip)+(port)
	res = re.search("IP6 .* > ([0-9a-f:]+)\.([0-9]+): ", line)
	if res is not None:
		trace_msg ("extracted IPv6 (dst ip+port): (" + str(res.group(1)) + ":" + str(res.group(2)) + ");")
		return res.group(1) + "/128", int(res.group(2))

# ## IPv6 (ip) no port
	res = re.search("IP6 .* > ([0-9a-f:]+): ", line)
	if res is not None:
		trace_msg ("extracted IPv6 (dst ip): (" + str(res.group(1)) + ");")
		return res.group(1) + "/128", 0

# ## IPv4 ARP
	res = re.search(" ARP ", line)
	if res is not None:
		trace_msg ("extracted IPv6 (dst ip): (" + str(res.group(1)) + ");")
		return "255.255.255.255/32", 0

	return IPv4_unknown, 0

def extract_hms (line):
	trace_msg ("extract_hms (" + line + ");")

	res = re.search("^([0-9]+):([0-9]+):([0-9]+).([0-9]+)", line)
	if res is not None:
		if "" == res.group(1).strip ():
			h = 0
		else:
			h = int(res.group(1).strip ())

		if "" == res.group(2).strip ():
			m = 0
		else:
			m = int(res.group(2).strip ())

		if "" == res.group(3).strip ():
			s = 0
		else:
			s = int(res.group(3).strip ())

		if "" == res.group(4).strip ():
			uS = 0
		else:
			uS = int(res.group(4).strip ())

		return s + m * 60 + h * 3600

	return 0

def extract_uS (line):
	trace_msg ("extract_uS (" + line + ");")

	res = re.search("^([0-9]+):([0-9]+):([0-9]+).([0-9]+)", line)
	if res is not None:
		if "" == res.group(4).strip ():
			uS = 0
		else:
			uS = int(res.group(4).strip ())

		return uS

	return 0

def proc_tcpdump_n_line (short_filename, line):
	global today_sec, last_ts, source_flag,	elastic_index


	trace_msg ("proc_tcpdump_n_line (" + line + ");")

	srcip, srcport = extract_src (line)
	trace_msg ("proc_tcpdump_n_line src: " + srcip + ":" + str(srcport))

	dstip, dstport = extract_dst (line)
	trace_msg ("proc_tcpdump_n_line dst: " + dstip + ":" + str(dstport))

	pktlen = extract_pktlen (line) ## NOTE: Number is returned
	trace_msg ("proc_tcpdump_n_line pktlen: " + str (pktlen))


	if pktlen > 0 and srcip != IPv4_unknown and dstip != IPv4_unknown:
		hms = extract_hms (line)
		trace_msg ("proc_tcpdump_n_line hms: " + str (hms))
		uS = extract_uS (line)
		trace_msg ("proc_tcpdump_n_line uS: " + str (uS))

		ts = today_sec + hms
		ts_mS = uS / 1000000

		if ts < last_ts:
			today_sec += 24 * 3600
			ts        += 24 * 3600
		last_ts = ts

		record = {}

		record["timestamp_ms"] = ts * 1000 + ts_mS

# 		set timestamp [fmttime ${ts} %Y-%m-%dT%H:%M:%S+00:00]
# 		trace_msg "ts=${ts}, timestamp=${timestamp}"
		record_ts = datetime.utcfromtimestamp(ts)
		record["timestamp"] =  record_ts.strftime ("%Y-%m-%dT%H:%M:%S+00:00")
		for key, value in additional_tags.items ():
			record[key] = value

		record ["pkt.src.ip"]   = srcip
		record ["pkt.src.port"] = srcport
		record ["pkt.dst.ip"]   = dstip
		record ["pkt.dst.port"] = dstport
		record ["pkt.len"]      = pktlen
		record ["src.host"]     = collector_host
		record ["src.iface"]    = collector_iface
		record ["ts.year"]      = record_ts.year
		record ["ts.month"]     = record_ts.month
		record ["ts.day"]       = record_ts.day
		record ["ts.hour"]      = record_ts.hour
		record ["ts.minute"]    = record_ts.minute
		record ["ts.second"]    = record_ts.second
		record ["ts.weekday"]   = record_ts.weekday ()

		if True == source_flag:
			record ["src.line"] = line
			record ["src.file"] = short_filename

		bulk_import_head ='{"index" : {"_index" : "' + elastic_index + record_ts.strftime ("%Y%m%d") + '"}})'
		bulk_import_line = json.dumps(record)

		# print (bulk_import_head)
		# print (bulk_import_line)
		# os.exit (0)

		return bulk_import_head, bulk_import_line

	return "", ""

def process_file (filename):
	global elastic_server, elastic_port, bulk_size, es_password, es_user

	if ("" != es_user) and ("" == es_password):
    	print "both parameters user and password has to be specified"
    	sys.exit (3)
	else:    
    	es_user = es_user + ":" + es_password + "@"

	trace_msg ("process_file (" + filename + ");")
	f = open(filename, "r")

	trace_msg ("Openning: " + "http://" + es_user + elastic_server + ":" + elastic_port)
	esWriter = Elasticsearch(["http://" + es_user + elastic_server + ":" + elastic_port])

	bulk_string = ""
	bulk_items = 0

	for line in f:
		bulk_import_head, bulk_import_line = proc_tcpdump_n_line (filename, line.strip ())
		if "" != bulk_import_head:
			bulk_string = bulk_string + bulk_import_head + "\n" + bulk_import_line + "\n"
			bulk_items += 1
			if bulk_size <= bulk_items:
				trace_msg ("Writting: " + bulk_string)
				esWriter.bulk (body=bulk_string)

				bulk_string = ""
				bulk_items = 0

	f.close ()

	if 0 < bulk_items:
		trace_msg ("Writting: " + bulk_string)
		esWriter.bulk (body=bulk_string)
	# esWriter.close ()

options, remainder = getopt.getopt(sys.argv[1:], 'Ab:cd:f:H:I:i:s:p:t:vu:P:', ['addsource',
														 'bulk-size=',
														 'clear-add-tags',
														 'collector-host=', 'collector='
														 'collector-iface=', 'iface=', 'collector-interface=', 'interface=',
														 'day=',
														 'elastic-index='
														 'elastic-port=',
														 'elastic-server=', 'port=',
                                                         'user=', 'login=',
														 'file=',
                                                         'tag=', 'tags=',
                                                         'verbose'
                                                         ])

for opt, arg in options:
	trace_msg ('opt:' + opt + "; arg=" + arg)

	if opt in ('-d', '--day'):
		today = arg
		today_sec = datetime.strptime(arg, dayTF).timestamp ()
		last_ts = today_sec
		trace_msg ("new: today=" + today + "; today_begin [sec]=" + str(today_sec))
	elif opt in ('-t', '--tag', '--tags'):
		add_tags (arg)
	elif opt in ('-c', '--clear-add-tags'):
		additional_tags = {}
		trace_msg ("clearing additiona tags")
	elif opt in ('-A', '--addsource'):
		source_flag = True
		trace_msg ("Adding source line and file enabled")
	elif opt in ('-v', '--verbose'):
		verbose_flag = True
		trace_msg ("Set verbose flag")
	elif opt in ('-f', '--file'):
		trace_msg ("Going to process file: " + arg)
		process_file (arg)
	elif opt in ('-s', '--elastic-server'):
		elastic_server = arg
		trace_msg ("Set elastic server: " + elastic_server)
	elif opt in ('-p', '--port', '--elastic-port'):
		elastic_port = arg
		trace_msg ("Set elastic server's port: " + elastic_port)
	elif opt in ('-i', '--elastic-index'):
		elastic_index = arg
		trace_msg ("Set elastic index: " + elastic_index)
	elif opt in ('-b', '--bulk-size'):
		bulk_size = int(arg)
		trace_msg ("Set elastic index: " + str(bulk_size))
    elif opt in ('-u', '--user', '--login'):
        es_user = arg
		trace_msg ("Set elastic user: " + es_user)
    elif opt in ('-P', '--pwd', '--password'):
        es_password = arg
		trace_msg ("Set elastic password: " + es_password)
	elif opt in ('-H', '--collector-host'):
		collector_host = arg
		trace_msg ("Set collector host (field: src.host): " + collector_host)
	elif opt in ('-I', 'collector-iface', 'iface', 'collector-interface', 'interface'):
		collector_iface = arg
		trace_msg ("Set collector interface (field: src.iface): " + collector_iface)

trace_msg ('remainder:' + str(remainder))

sys.exit (0)