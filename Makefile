PYTHON_VERSION ?= python3
IMAGE_NAME     ?= echoserver_client
TAG            ?= latest

build_image:
	docker build -t $(IMAGE_NAME):$(TAG) .

prepare_venv:
	$(PYTHON_VERSION) -m venv venv
ifeq ($(OS),Windows_NT)
	.\venv\Scripts\activate & pip install -e src
else
	bash -c 'source venv/bin/activate; pip install -e src;'
endif
