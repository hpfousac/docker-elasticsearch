IMAGE_NAME = hpfousac/docker-elasticsearch
TAG_NAME   = 6.7.0



refresh:
	docker build -t ${IMAGE_NAME} .
	docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${TAG_NAME}

push:
	docker tag ${IMAGE_NAME}:${TAG_NAME} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_NAME}
	docker tag ${IMAGE_NAME}:latest ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
	docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG_NAME}
	docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest

