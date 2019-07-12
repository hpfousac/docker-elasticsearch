#!/bin/bash

ELASTIC_SERVER=10.177.71.13
ELASTIC_PORT=30920

DATESTRING=$1

INGEST_PIPELINE=tcpdump_pipeline

for IFACE in xl0 re0 gif0 ;  do
	HOUR=0
	echo ${IFACE}
	while [ ${HOUR} -lt 24 ] ; do
		FILE_HOUR=`printf '%02d' ${HOUR}`
		for JSON_XZ in `ls tcpdump-${DATESTRING}-${FILE_HOUR}*-${IFACE}.json.xz` ; do
			JSON=`echo ${JSON_XZ} | sed -e 's/\.xz$//'`
			xz -d < ${JSON_XZ} > /tmp/${JSON}
			./feed_bulk.py -f /tmp/${JSON} -s ${ELASTIC_SERVER} -p ${ELASTIC_PORT} -i tcpdump-${DATESTRING} --ingest-pipeline=tcpdump_pipeline &
			sleep 1
		done
		HOUR=`expr ${HOUR} + 1`
	done
done

wait

rm -f /tmp/tcpdump-${DATESTRING}-${FILE_HOUR}*.json

exit 0
