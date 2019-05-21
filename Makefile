IMAGE_NAME = hpfousac/docker-elasticsearch
TAG_NAME   = 6.7.0
TAG_DATE   = d20190404


refresh:
	docker build -t ${IMAGE_NAME} .
	docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TAG_NAME}
	docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TAG_DATE}

push:
	docker tag ${IMAGE_NAME}:${TAG_NAME} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_NAME}
	docker tag ${IMAGE_NAME}:${TAG_DATE} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_DATE}
	docker tag ${IMAGE_NAME}:latest ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
	docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_NAME}
	docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_DATE}
	docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest

test:
	-mkdir testdata.d
	docker run -d --name elasticsearch_test  -v `pwd`/testdata.d:/data \
		-p 9200:9200 -p 9300:9300 \
		${IMAGE_NAME}:${TAG_DATE}

kill_test:
	-docker kill elasticsearch_test
	-docker rm elasticsearch_test

loc_client_test:
	curl -X POST -H "Content-Type: application/json" -H "Cache-Control: no-cache" -d '{"user" : "Test User", "post_date" : "2019-03-23T12:30:00", "message" : "trying out Elasticsearch"}' "http://localhost:9200/sampleindex/sampletype/"
	clear
	curl -XGET 'localhost:9200/sampleindex/_search?size=10&q=*:*'

loc_kibana_test:
	docker run --name loc_kibana -p 5601:5601 -e "ELASTICSEARCH_URL=http://${ELASTICSRVR}:9200" docker.elastic.co/kibana/kibana:${TAG_NAME}

