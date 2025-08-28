# Default values for arguments
IMAGE_NAME ?= echoserver_client
TAG        ?= latest

build:
	docker build -t $(IMAGE_NAME):$(TAG) .