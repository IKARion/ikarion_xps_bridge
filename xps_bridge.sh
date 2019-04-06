#!/bin/bash

SELF=$(basename "${0}");
PROG="${SELF%%.*}.py"
CMD="/opt/python-3.6.8/bin/python3 ${PWD}/${PROG}"
DATE=$(date '+%Y%m%d_%H%M%S')

start() {
  if (( ! $(ps -ef | grep -v "grep" | grep "${PWD}/${PROG}" | wc -l) > 0 )); then
    #export FLASK_ENV=development
    mkdir -p "${PWD}/log"
    #nohup ${CMD} ${1} 2> >(grep --line-buffered -v " 200 -" 1>> "${PWD}/log/${SELF%%.*}.err") 1>> "${PWD}/log/${SELF%%.*}.out" &
    ${CMD}
  fi
}

stop() {
  if (( $(ps -ef | grep -v "grep" | grep "${PWD}/${PROG}" | wc -l) > 0 )); then
    PID=$(ps -aux | grep -v "grep" | grep "${PROG}" | tr -s ' ' | cut -d' ' -f2)
    kill -9 "${PID}"
  fi
}

reset() {
  stop
  cat "${PWD}/log/${SELF%%.*}.out" | grep -v "DEV@" | grep -v "@query" > "${PWD}/log/${SELF%%.*}.tmp" 2> /dev/null
  rm -f "${PWD}/log/${SELF%%.*}.out"
  mv "${PWD}/log/${SELF%%.*}.tmp" "${PWD}/log/${SELF%%.*}.out"
  rm -f "${PWD}/log/${SELF%%.*}.err"
  start
}

silent() {
  stop
  start silent
}

restart() {
  stop
  start
}

case "${1}" in
    start)
	start
	;;
    stop)
	stop
	;;
    reset)
        reset
        ;;
    silent)
        silent
        ;;
    restart)
	stop
	start
	;;
    *)
	echo "usage: ${PROG} {start|stop|reset|restart}"
	exit 1
esac

exit 0
