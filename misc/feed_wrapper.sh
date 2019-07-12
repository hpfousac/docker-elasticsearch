#!/bin/bash

ELASTIC_SERVER=10.245.6.201

DATESTRING=$1

INGEST_PIPELINE=tcpdump_pipeline

for IFACE in xl0 re0 gif0 ;  do
	HOUR=0
	echo ${IFACE}
	while [ ${HOUR} -lt 24 ] ; do
		FILE_HOUR=`printf '%02d' ${HOUR}`
		for JSON in `ls tcpdump-${DATESTRING}-${FILE_HOUR}*-${IFACE}.json` ; do
			./feed_bulk.py -f ${JSON} -s ${ELASTIC_SERVER} -i tcpdump-${DATESTRING} --ingest-pipeline=tcpdump_pipeline &
			sleep 1
		done
		HOUR=`expr ${HOUR} + 1`
	done
done

wait
