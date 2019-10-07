#!/bin/bash

##
## Load from GCE Storage to local ES
##

GS_ROOT=gs://eu-mezisklad/gate
LOCKFILE=${HOME}/.gs2es.lck

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
    echo gsutil cp ${GSNAME} ${BASENAME}
    echo xz -d ${BASENAME}
    echo ./tcpdump2es_v3.py -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 10 -H gate -I ${IFACE} -f ${SHORTNAME}
    echo rm -v ${SHORTNAME}
done

wait

rm -f ${LOCKFILE}

exit 0
