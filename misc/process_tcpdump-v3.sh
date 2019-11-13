#!/bin/bash


export FLAG_VERBOSE=0
SOURCE_DIR=
TMP_DIR=/tmp
DATETIME_STAMP=
COLLECTOR_HOST=`hostname`

ES_SERVER=localhost
ES_PORT=9200

ADDITIONAL_OPTS=

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
    $0 -s source_dir -m datetimestamp -w workdir -c colector_host -S es_server -P es_server_port [-v]
    datetimestamp format: (YYYYMMDD)
EOT
}

while getopts "c:vs:S:P:m:w:h?" opt; do
  case $opt in
    h)
      usage
      exit 0
      ;;
    c)
      COLLECTOR_HOST=$OPTARG
      info_msg COLLECTOR_HOST=${COLLECTOR_HOST}
	  ;;
    m)
      DATETIME_STAMP=$OPTARG
      info_msg DATETIME_STAMP=${DATETIME_STAMP}
	  ;;
    s)
      SOURCE_DIR=$OPTARG
      info_msg SOURCE_DIR=${SOURCE_DIR}
      ;;
    S)
      ES_SERVER=$OPTARG
      info_msg ES_SERVER=${ES_SERVER}
      ;;
    P)
      ES_PORT=$OPTARG
      info_msg ES_PORT=${ES_PORT}
      ;;
    v)
      FLAG_VERBOSE=1
	  ADDITIONAL_OPTS="${ADDITIONAL_OPTS} --verbose"
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

if [ X${DATETIME_STAMP} = X ] ; then
	error_msg datetimestamp must be specified
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

MY_DIR=`pwd`

cd ${SOURCE_DIR}
if [ ! $? = 0 ] ; then
	error_msg can not jump to: ${SOURCE_DIR}  
	exit 6
fi

YEAR=`echo ${DATETIME_STAMP}  | awk '{print substr($1,1,4) }'`
MONTH=`echo ${DATETIME_STAMP} | awk '{print substr($1,5,2) }' | sed -e 's/^0//'`
DAY=`echo ${DATETIME_STAMP}   | awk '{print substr($1,7,2) }' | sed -e 's/^0//'`

info_msg DAY=${DAY}.${MONTH}.${YEAR}

for FILE in tcpdump-${DATETIME_STAMP}-*.xz ; do
	if [ -f ${FILE} ] ; then
		info_msg processing file: ${FILE}
		FILENAME=`echo ${FILE} | sed -e 's/\.xz$//'`
		IFACE=`echo ${FILENAME} | cut -d - -f 4`

		info_msg processing file: ${FILE}, uncompresed ${FILENAME}, interface ${IFACE}
		xz -d < ${FILE} > ${TMP_DIR}/${FILENAME}
		${MY_DIR}/tcpdump2es_v3.py --addsource --day=${DAY}.${MONTH}.${YEAR} \
			--collector-host=${COLLECTOR_HOST} --collector-iface=${IFACE} \
			--elastic-server=${ES_SERVER} --elastic-port=${ES_PORT} --elastic-index=tcpdump-v3- \
			--bulk-size=500 \
			${ADDITIONAL_OPTS} \
			--file=${TMP_DIR}/${FILENAME} > /dev/null 2> /dev/null
		rm ${TMP_DIR}/${FILENAME}
	fi
done

exit 0

./process_tcpdump-v3.sh -v -s /server/stage/david/tcpdump/gate/incoming-data/201905 -w /home/david/ramdisk/tmp \
	-t /server/stage/david/tcpdump/gate/json-out/201905 -c gate -m 20190501 \
	-S localhost -P 9200

YYYYMM=201910
START_DAY=1
END_DAY=5
export TZ=UTC

DAY=${START_DAY}
while [ ${DAY} -le ${END_DAY} ] ; do
  FMTDAY=`printf '%02d' ${DAY}`
  echo ${FMTDAY}

  nice -19 ./process_tcpdump-v3.sh -s /server/stage/david/tcpdump/gate/incoming-data/${YYYYMM} \
  	-w /home/david/ramdisk/tmp \
	-c gate -m ${YYYYMM}${FMTDAY} \
	-S localhost -P 9200 &

	sleep 1

  DAY=`expr ${DAY} + 1`

done
