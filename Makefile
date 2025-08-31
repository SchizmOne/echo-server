PYTHON_VERSION ?= python3
IMAGE_NAME     ?= echoserver
TAG            ?= latest

build_image:
	docker build -t $(IMAGE_NAME):$(TAG) .

prepare_venv:
	$(PYTHON_VERSION) -m venv venv
ifeq ($(OS),Windows_NT)
	.\venv\Scripts\activate & python -m pip install --upgrade pip setuptools wheel & pip install -e .
else
	bash -c 'source venv/bin/activate; python -m pip install --upgrade pip setuptools wheel; pip install -e .;'
endif
