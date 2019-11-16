#!/bin/bash

##
## Load from GCE Storage to local ES
##

TS_MASK=$1
MONTH_MASK=`echo ${TS_MASK} | cut -c1-6`
FS_ROOT=/server/stage/david/tcpdump/gate/incoming-data/${MONTH_MASK}

TMP=/home/david/ramdisk/tmp


ls ${FS_ROOT}/tcpdump-${TS_MASK}-*.xz | while read FNAME ; do
    BASENAME=`basename ${FNAME}`
    SHORTNAME=`echo ${BASENAME} | sed -e 's/\.xz$//'`
    IFACE=`echo ${SHORTNAME} | cut -d- -f4`
    YYYYMMDD=`echo ${SHORTNAME} | cut -d- -f2`
    YEAR=`echo ${YYYYMMDD} | cut -c1-4 | sed -e 's/^0*//'`
    MONTH=`echo ${YYYYMMDD} | cut -c5-6 | sed -e 's/^0*//'`
    DAY=`echo ${YYYYMMDD} | cut -c7-8 | sed -e 's/^0*//'`
    cp ${FNAME} ${TMP}/
    xz -d ${TMP}/${BASENAME}
    ./tcpdump2es_v3.py -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 500 -H gate -I ${IFACE} -f ${TMP}/${SHORTNAME}
    rm -v ${TMP}/${SHORTNAME}
done

wait

exit 0
