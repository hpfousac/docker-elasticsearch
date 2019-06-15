#!/bin/bash

ELASTIC_SERVER=10.245.6.188

for IFACE in xl0 re0 gif0 ;  do
	HOUR=0
	echo ${IFACE}
	while [ ${HOUR} -lt 24 ] ; do
		FILE_HOUR=`printf '%02d' ${HOUR}`
		for JSON in `ls tcpdump-20190614-${FILE_HOUR}*-${IFACE}.json` ; do
			echo feed -f ${JSON} -s ${ELASTIC_SERVER} -i tcpdump
		done
		HOUR=`expr ${HOUR} + 1`
	done
done

