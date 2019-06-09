CHART_NAME = single-elasticsearch

install:
	helm install -f ${CHART_NAME}/values.yaml ${CHART_NAME} --name ${CHART_NAME}-test

uninstall:
	helm delete --purge ${CHART_NAME}-test


install-minikube-uran:
	helm install -f ${CHART_NAME}/values-minikube-on-uran.yaml ${CHART_NAME} --name ${CHART_NAME}-uran

uninstall-minikube-uran:
	helm delete --purge ${CHART_NAME}-uran

install-sgc.int:
	helm install -f ${CHART_NAME}/values.sgc.int.yaml ${CHART_NAME} --name ${CHART_NAME}-sgc --namespace cluster-monitoring

uninstall-sgc.int:
	helm delete --purge ${CHART_NAME}-sgc
