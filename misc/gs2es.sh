#!/bin/bash

##
## Load from GCE Storage to local ES
##

GS_ROOT=gs://eu-mezisklad/gate/${HOSTNAME}
LOCKFILE=${HOME}/.gs2es.${HOSTNAME}.lck

cd /home/david_doubrava/RaD/source/docker-elasticsearch/misc

if [ -e ${LOCKFILE} ] ; then
  exit 0
fi

touch ${LOCKFILE}

gsutil ls ${GS_ROOT}'/tcpdump-*.xz' | while read GSNAME ; do
    BASENAME=`basename ${GSNAME}`
    SHORTNAME=`echo ${BASENAME} | sed -e 's/\.xz$//'`
    IFACE=`echo ${SHORTNAME} | cut -d- -f4`
    YYYYMMDD=`echo ${SHORTNAME} | cut -d- -f2`
    YEAR=`echo ${YYYYMMDD} | cut -c1-4 | sed -e 's/^0*//'`
    MONTH=`echo ${YYYYMMDD} | cut -c5-6 | sed -e 's/^0*//'`
    DAY=`echo ${YYYYMMDD} | cut -c7-8 | sed -e 's/^0*//'`
    gsutil cp ${GSNAME} ${BASENAME}
    xz -d ${BASENAME}
    ./tcpdump2es_v3.py -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 200 -H gate -I ${IFACE} -f ${SHORTNAME}
    rm -v ${SHORTNAME}
    gsutil rm ${GSNAME}
done

wait

rm -f ${LOCKFILE}

exit 0

