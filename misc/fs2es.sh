#!/bin/bash

##
## Load from GCE Storage to local ES
##

# default values
ADDITIONAL_OPTS=

ES_SERVER=localhost
ES_PORT=9200

TMP_DIR=/tmp

usage () {
  echo $0 
}

while getopts "P:S:c:vs:d:w:h?" opt; do
  case $opt in
    h)
      usage
      exit 0
      ;;
    v)
      FLAG_VERBOSE=1
      ADDITIONAL_OPTS="${ADDITIONAL_OPTS} --verbose"
      info_msg VERBOSE
	  ;;
    S)
      ES_SERVER=$OPTARG
      info_msg ES_SERVER=${ES_SERVER}
      ;;
    P)
      ES_PORT=$OPTARG
      info_msg ES_PORT=${ES_PORT}
      ;;
    c)
      COLLECTOR_HOST=$OPTARG
      info_msg COLLECTOR_HOST=${COLLECTOR_HOST}
	  ;;
    d)
      DATETIME_STAMP=$OPTARG
      info_msg DATETIME_STAMP=${DATETIME_STAMP}
	  ;;
    s)
      SOURCE_DIR=$OPTARG
      info_msg SOURCE_DIR=${SOURCE_DIR}
      ;;
    w)
      TMP_DIR=$OPTARG
      info_msg TMP_DIR=${TMP_DIR}
	  ;;
    \?)
      # allow other args to pass on to mavproxy
      usage
      exit 0
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      exit 3
  esac
done

MONTH_MASK=`echo ${DATETIME_STAMP} | cut -c1-6`
#FS_ROOT=/server/stage/david/tcpdump/${COLLECTOR_HOST}/incoming-data/${MONTH_MASK}


ls ${SOURCE_DIR}/tcpdump-${DATETIME_STAMP}-*.xz | while read FNAME ; do
    BASENAME=`basename ${FNAME}`
    SHORTNAME=`echo ${BASENAME} | sed -e 's/\.xz$//'`
    IFACE=`echo ${SHORTNAME} | cut -d- -f4`
    YYYYMMDD=`echo ${SHORTNAME} | cut -d- -f2`
    YEAR=`echo ${YYYYMMDD} | cut -c1-4 | sed -e 's/^0*//'`
    MONTH=`echo ${YYYYMMDD} | cut -c5-6 | sed -e 's/^0*//'`
    DAY=`echo ${YYYYMMDD} | cut -c7-8 | sed -e 's/^0*//'`
    cp ${FNAME} ${TMP_DIR}/
    xz -d ${TMP_DIR}/${BASENAME}
    ./tcpdump2es_v3.py -s ${ES_SERVER} -p ${ES_PORT} -d ${DAY}.${MONTH}.${YEAR} -A -i tcpdump-v3- -b 500 -H ${COLLECTOR_HOST} -I ${IFACE} ${ADDITIONAL_OPTS} -f ${TMP_DIR}/${SHORTNAME}
    rm -v ${TMP_DIR}/${SHORTNAME}
done

wait

exit 0
