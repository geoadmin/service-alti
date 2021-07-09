SHELL = /bin/bash

.DEFAULT_GOAL := help

SERVICE_NAME := service-alti

CURRENT_DIR := $(shell pwd)

# Test report configuration
TEST_REPORT_DIR ?= $(CURRENT_DIR)/tests/report
TEST_REPORT_FILE ?= nose2-junit.xml

# Docker variables
DOCKER_IMG_LOCAL_TAG = swisstopo/$(SERVICE_NAME):local

# Find all python files that are not inside a hidden directory (directory starting with .)
PYTHON_FILES := $(shell find ./* -type f -name "*.py" -print)

# PIPENV files
PIP_FILE = $(CURRENT_DIR)/Pipfile
PIP_FILE_LOCK = $(CURRENT_DIR)/Pipfile.lock
VENV := $(shell pipenv --venv)

# default configuration
HTTP_PORT ?= 5000
DTM_BASE_PATH ?= $(CURRENT_DIR)
LOGS_DIR ?= $(CURRENT_DIR)/logs

# Docker metadata
GIT_HASH := `git rev-parse HEAD`
GIT_BRANCH := `git symbolic-ref HEAD --short 2>/dev/null`
GIT_DIRTY := `git status --porcelain`
GIT_TAG := `git describe --tags || echo "no version info"`
AUTHOR := $(USER)

# Commands
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask
YAPF := $(VENV)/bin/yapf
ISORT := $(VENV)/bin/isort
NOSE := $(VENV)/bin/nose2
PYLINT := $(VENV)/bin/pylint


all: help


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo -e " \033[1mSetup TARGETS\033[0m "
	@echo "- setup              Create the python virtual environment with developper tools"
	@echo "- ci                 Create the python virtual environment and install requirements based on the Pipfile.lock"
	@echo -e " \033[1mFORMATING, LINTING AND TESTING TOOLS TARGETS\033[0m "
	@echo "- format             Format the python source code"
	@echo "- ci-check-format    Format the python source code and check if any files has changed. This is meant to be used by the CI."
	@echo "- lint               Lint the python source code"
	@echo "- format-lint        Format and lint the python source code"
	@echo "- test               Run the tests"
	@echo -e " \033[1mLOCAL SERVER TARGETS\033[0m "
	@echo "- serve              Run the project using the flask debug server. Port can be set by Env variable HTTP_PORT (default: 5000)"
	@echo "- gunicornserve      Run the project using the gunicorn WSGI server. Port can be set by Env variable DEBUG_HTTP_PORT (default: 5000)"
	@echo -e " \033[1mDocker TARGETS\033[0m "
	@echo "- dockerbuild        Build the project localy (with tag := $(DOCKER_IMG_LOCAL_TAG)) using the gunicorn WSGI server inside a container"
	@echo "- dockerpush         Build and push the project localy (with tag := $(DOCKER_IMG_LOCAL_TAG))"
	@echo "- dockerrun          Run the project using the gunicorn WSGI server inside a container (exposed port: 5000)"
	@echo "- shutdown           Stop the aforementioned container"
	@echo -e " \033[1mCLEANING TARGETS\033[0m "
	@echo "- clean              Clean genereated files"
	@echo "- clean_venv         Clean python venv"


# Build targets. Calling setup is all that is needed for the local files to be installed as needed.

.PHONY: setup
setup:
	mkdir -p $(LOGS_DIR)
	pipenv install --dev
	pipenv shell


.PHONY: ci
ci:
	# Create virtual env with all packages for development using the Pipfile.lock
	pipenv sync --dev


# linting target, calls upon yapf to make sure your code is easier to read and respects some conventions.

.PHONY: format
format:
	$(YAPF) -p -i --style .style.yapf $(PYTHON_FILES)
	$(ISORT) $(PYTHON_FILES)

.PHONY: ci-check-format
ci-check-format: format
	@if [[ -n `git status --porcelain` ]]; then \
	 	>&2 echo "ERROR: the following files are not formatted correctly:"; \
		>&2 git status --porcelain; \
		exit 1; \
	fi


.PHONY: lint
lint:
	$(PYLINT) $(PYTHON_FILES)


.PHONY: format-lint
format-lint: format lint


# Test target

.PHONY: test
test:
	mkdir -p $(TEST_REPORT_DIR)
	DTM_BASE_PATH=$(DTM_BASE_PATH) $(NOSE) \
		-c tests/unittest.cfg \
		--verbose \
		--junit-xml-path $(TEST_REPORT_DIR)/$(TEST_REPORT_FILE) \
		-s tests/


# Serve targets. Using these will run the application on your local machine. You can either serve with a wsgi front (like it would be within the container), or without.

.PHONY: serve
serve:
	LOGS_DIR=$(LOGS_DIR) DTM_BASE_PATH=$(DTM_BASE_PATH) FLASK_APP=$(subst -,_,$(SERVICE_NAME)) FLASK_DEBUG=1 $(FLASK) run \
	--host=0.0.0.0 \
	--port=$(HTTP_PORT)


.PHONY: gunicornserve
gunicornserve:
	LOGS_DIR=$(LOGS_DIR) DTM_BASE_PATH=$(DTM_BASE_PATH) $(PYTHON) wsgi.py


# Docker related functions.

.PHONY: dockerbuild
dockerbuild:
	docker build \
		--build-arg GIT_HASH="$(GIT_HASH)" \
		--build-arg GIT_BRANCH="$(GIT_BRANCH)" \
		--build-arg GIT_DIRTY="$(GIT_DIRTY)" \
		--build-arg VERSION="$(GIT_TAG)" \
		--build-arg AUTHOR="$(AUTHOR)" \
		-t $(DOCKER_IMG_LOCAL_TAG) .


.PHONY: dockerpush
dockerpush:
	docker push $(DOCKER_IMG_LOCAL_TAG)


.PHONY: dockerrun
dockerrun:
	LOGS_DIR=$(LOGS_DIR) DTM_BASE_PATH=. HTTP_PORT=$(HTTP_PORT) docker-compose up --build


.PHONY: shutdown
shutdown:
	HTTP_PORT=$(HTTP_PORT) docker-compose down


# Clean targets

.PHONY: clean_venv
clean_venv:
	pipenv --rm


.PHONY: clean
clean: clean_venv
	@# clean python cache files
	find . -name __pycache__ -type d -print0 | xargs -I {} -0 rm -rf "{}"
	rm -rf $(TEST_REPORT_DIR)
	rm -rf $(LOGS_DIR)
