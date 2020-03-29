#!/bin/bash

##
## Load from GCE Storage to local ES
##

DATA_ROOT="$1"
ROOT_BASENAME=`basename ${DATA_ROOT}`
LOCKFILE=${HOME}/.dir2es.${ROOT_BASENAME}.lck

#cd /home/david_doubrava/RaD/source/docker-elasticsearch/misc

if [ -e ${LOCKFILE} ] ; then
  exit 0
fi

touch ${LOCKFILE}

find ${DATA_ROOT} -name 'tcpdump-*.xz' | while read GSNAME ; do
    BASENAME=`basename ${GSNAME}`
    SHORTNAME=`echo ${BASENAME} | sed -e 's/\.xz$//'`
    IFACE=`echo ${SHORTNAME} | cut -d- -f4`
    YYYYMMDD=`echo ${SHORTNAME} | cut -d- -f2`
    YEAR=`echo ${YYYYMMDD} | cut -c1-4 | sed -e 's/^0*//'`
    MONTH=`echo ${YYYYMMDD} | cut -c5-6 | sed -e 's/^0*//'`
    DAY=`echo ${YYYYMMDD} | cut -c7-8 | sed -e 's/^0*//'`
    cp ${GSNAME} ${BASENAME}
    xz -d ${BASENAME}
    if [ "X" = "X${ZIPKIN_URL}" ] ; then
        ./tcpdump2es_v3.py -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 200 -H gate -I ${IFACE} -s 10.10.11.116 -p 30920 -f ${SHORTNAME}
    else
        ./tcpdump2es_v3_zipkin.py -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 200 -H gate -I ${IFACE} -s 10.10.11.116 -p 30920 -f ${SHORTNAME}
    fi
    rm -v ${SHORTNAME}
    rm ${GSNAME}
done

wait

rm -f ${LOCKFILE}

exit 0

