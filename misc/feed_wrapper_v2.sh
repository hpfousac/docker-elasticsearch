#!/bin/bash

#
# YYYYMM=201908
# DAY=1
# while [ ${DAY} -le 31 ] ; do
#   DD=`printf '%02d' ${DAY}`
#   echo ${YYYYMM}${DD}
#   ./feed_wrapper.sh -S kub.ddoubrava.cz -P 30920 -m ${YYYYMM}${DD} -s /server/stage/david/tcpdump/gate/json-out/${YYYYMM} -w /home/david/ramdisk/elk-tests
#   DAY=`expr ${DAY} + 1`
# done
#

export FLAG_VERBOSE=0
SOURCE_DIR=
TMP_DIR=/tmp
DATESTRING=
COLLECTOR_HOST=`hostname`

BEGIN_HOUR=0
END_HOUR=24

info_msg () {
	if [ ! ${FLAG_VERBOSE} = 0 ] ; then
		echo '** INFO **:' $*
	fi
}

error_msg () {
	echo '** ERROR **:' $*
}

usage () {
	cat <<EOT
Usage:
    $0 -s source_dir -m datetimestamp -w workdir [-v]
    datetimestamp format: (YYYYMMDD)
EOT
}

while getopts "B:E:P:S:c:vs:m:w:t:h?" opt; do
  case $opt in
    h)
      usage
      exit 0
      ;;
    B)
      BEGIN_HOUR=$OPTARG
      info_msg BEGIN_HOUR=${BEGIN_HOUR}
      ;;
    E)
      END_HOUR=$OPTARG
      info_msg END_HOUR=$END_HOUR
      ;;
    P)
      ELASTIC_PORT=$OPTARG
      info_msg ELASTIC_PORT=${ELASTIC_PORT}
	  ;;
    S)
      ELASTIC_SERVER=$OPTARG
      info_msg ELASTIC_SERVER=${ELASTIC_SERVER}
	  ;;
    m)
      DATESTRING=$OPTARG
      info_msg DATESTRING=${DATETIME_STAMP}
	  ;;
    s)
      SOURCE_DIR=$OPTARG
      info_msg SOURCE_DIR=${SOURCE_DIR}
      ;;
    v)
      FLAG_VERBOSE=1
      info_msg VERBOSE
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

if [ X${DATESTRING} = X ] ; then
	error_msg datetimestamp must be specified
	help 
	exit 1
fi

if [ X${ELASTIC_SERVER} = X ] ; then
	error_msg Elastic Search server must be specified
	help 
	exit 1
fi

if [ X${ELASTIC_PORT} = X ] ; then
	error_msg Elastic Search server port must be specified
	help 
	exit 1
fi

if [ X${SOURCE_DIR} = X ] ; then
	error_msg source dir must be specified
	help 
	exit 1
fi

if [ ! -d ${SOURCE_DIR} ] ; then
	error_msg source dir must exist: ${SOURCE_DIR}  
	usage
	exit 2
fi

if [ X${TMP_DIR} = X ] ; then
	error_msg source dir must be specified 
	usage
	exit 3
fi

if [ ! -d ${TMP_DIR} ] ; then
	error_msg work dir must exist: ${TMP_DIR}  
	usage
	exit 4
fi

INGEST_PIPELINE=tcpdump_pipeline

for IFACE in xl0 re0 gif0 ;  do
	HOUR=${BEGIN_HOUR}
	echo ${IFACE}
	while [ ${HOUR} -lt ${END_HOUR} ] ; do
		FILE_HOUR=`printf '%02d' ${HOUR}`
		for FULL_JSON_XZ in `ls ${SOURCE_DIR}/tcpdump-${DATESTRING}-${FILE_HOUR}*-${IFACE}.json.xz` ; do
			JSON_XZ=`basename ${FULL_JSON_XZ}` 
			JSON=`echo ${JSON_XZ} | sed -e 's/\.xz$//'`
			nice -19 xz -d < ${FULL_JSON_XZ} > ${TMP_DIR}/${JSON}
			./feed_bulk.py -f ${TMP_DIR}/${JSON} -s ${ELASTIC_SERVER} -p ${ELASTIC_PORT} -i tcpdump-v2-${DATESTRING}
			rm -f ${TMP_DIR}/${JSON}*
		done
		HOUR=`expr ${HOUR} + 1`
	done
	sleep 27
done

wait


exit 0
