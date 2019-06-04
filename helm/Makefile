CHART_NAME = single-elasticsearch



install:
	helm install -f ${CHART_NAME}/values.yaml ${CHART_NAME} --name ${CHART_NAME}-test

check:
	 helm install -f ${CHART_NAME}/values.yaml --dry-run --debug ${CHART_NAME}


uninstall:
	helm delete --purge ${CHART_NAME}-test

