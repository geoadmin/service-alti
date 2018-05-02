SHELL = /bin/bash
# Variables
APACHE_ENTRY_PATH := $(shell if [ '$(APACHE_BASE_PATH)' = 'main' ]; then echo ''; else echo /$(APACHE_BASE_PATH); fi)
KEEP_VERSION ?= 'false'
LAST_VERSION := $(shell if [ -f '.venv/last-version' ]; then cat .venv/last-version 2> /dev/null; else echo '-none-'; fi)
VERSION := $(shell if [ '$(KEEP_VERSION)' = 'true' ] && [ '$(LAST_VERSION)' != '-none-' ]; then echo $(LAST_VERSION); else python -c "print __import__('time').strftime('%s')"; fi)
BRANCH_STAGING := $(shell if [ '$(DEPLOY_TARGET)' = 'dev' ]; then echo 'test'; else echo 'integration'; fi)
BRANCH_TO_DELETE :=
CURRENT_DIRECTORY := $(shell pwd)
DEPLOYCONFIG ?=
DEPLOY_TARGET ?=
GIT_BRANCH := $(shell if [ -f '.venv/deployed-git-branch' ]; then cat .venv/deployed-git-branch 2> /dev/null; else git rev-parse --symbolic-full-name --abbrev-ref HEAD; fi)
HTTP_PROXY := http://ec2-52-28-118-239.eu-central-1.compute.amazonaws.com:80
INSTALL_DIRECTORY := .venv
MODWSGI_USER := www-data
NO_TESTS ?= withtests
PYTHON_FILES := $(shell find alti/* -path alti/static -prune -o -type f -name "*.py" -print)
SHORTENER_ALLOWED_DOMAINS := admin.ch, swisstopo.ch, bgdi.ch
SHORTENER_ALLOWED_HOSTS :=
TEMPLATE_FILES := $(shell find -type f -name "*.in" -print)
USER_SOURCE ?= rc_user
WSGI_APP := $(CURRENT_DIRECTORY)/apache/application.wsgi
PYPI_URL ?= https://pypi.org/simple/

# Commands
AUTOPEP8_CMD := $(INSTALL_DIRECTORY)/bin/autopep8
FLAKE8_CMD := $(INSTALL_DIRECTORY)/bin/flake8
MAKO_CMD := $(INSTALL_DIRECTORY)/bin/mako-render
NOSE_CMD := $(INSTALL_DIRECTORY)/bin/nosetests
PIP_CMD := $(INSTALL_DIRECTORY)/bin/pip
PSERVE_CMD := $(INSTALL_DIRECTORY)/bin/pserve
PSHELL_CMD := $(INSTALL_DIRECTORY)/bin/pshell
PYTHON_CMD := $(INSTALL_DIRECTORY)/bin/python

# Linting rules
PEP8_IGNORE := "E128,E221,E241,E251,E272,E501,E711,E731"

# E128: continuation line under-indented for visual indent
# E221: multiple spaces before operator
# E241: multiple spaces after ':'
# E251: multiple spaces around keyword/parameter equals
# E272: multiple spaces before keyword
# E501: line length 79 per default
# E711: comparison to None should be 'if cond is None:' (SQLAlchemy's filter syntax requires this ignore!)
# E731: do not assign a lambda expression, use a def

# Colors
RESET := $(shell tput sgr0)
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)

# Versions
PYTHON_VERSION := $(shell python --version 2>&1 | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
PYTHONPATH ?= .venv/lib/python${PYTHON_VERSION}/site-packages:/usr/lib64/python${PYTHON_VERSION}/site-packages

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo "- user               Build the user specific version of the app"
	@echo "- all                Build the app"
	@echo "- serve              Serve the application with pserve"
	@echo "- shell              Enter interactive shell with app loaded in the background"
	@echo "- test               Launch the tests (no e2e tests)"
	@echo "- lint               Run the linter"
	@echo "- autolint           Run the autolinter"
	@echo "- deploybranch       Deploy current branch to dev (must be pushed before hand)"
	@echo "- deploybranchint    Deploy current branch to dev and int (must be pushed before hand)"
	@echo "- deploybranchdemo   Deploy current branch to dev and demo (must be pushed before hand)"
	@echo "- deletebranch       List deployed branches or delete a deployed branch (BRANCH_TO_DELETE=...)"
	@echo "- deploydev          Deploys master to dev (SNAPSHOT=true to also create a snapshot)"
	@echo "- deployint          Deploys a snapshot to integration (SNAPSHOT=201512021146)"
	@echo "- deployprod         Deploys a snapshot to production (SNAPSHOT=201512021146)"
	@echo "- clean              Remove generated files"
	@echo "- cleanall           Remove all the build artefacts"
	@echo
	@echo "Variables:"
	@echo "APACHE_ENTRY_PATH:   ${APACHE_ENTRY_PATH}"
	@echo "API_URL:             ${API_URL}"
	@echo "BRANCH_STAGING:      ${BRANCH_STAGING}"
	@echo "GIT_BRANCH:          ${GIT_BRANCH}"
	@echo "SERVER_PORT:         ${SERVER_PORT}"
	@echo


.PHONY: user
user:
	source $(USER_SOURCE) && make all

.PHONY: all
all: setup templates lint fixrights

setup: .venv .venv/hooks

templates: .venv/last-version apache/wsgi.conf development.ini production.ini

.PHONY: dev
dev:
	source rc_dev && make all

.PHONY: int
int:
	source rc_int && make all

.PHONY: prod
prod:
	source rc_prod && make all

.PHONY: serve
serve:
	PYTHONPATH=${PYTHONPATH} ${PSERVE_CMD} development.ini --reload

.PHONY: shell
shell:
	PYTHONPATH=${PYTHONPATH} ${PSHELL_CMD} development.ini

.PHONY: test
test:
	PYTHONPATH=${PYTHONPATH} ${NOSE_CMD} alti/tests/ -e .*e2e.*

.PHONY: lint
lint:
	@echo "${GREEN}Linting python files...${RESET}";
	${FLAKE8_CMD} --ignore=${PEP8_IGNORE} $(PYTHON_FILES) && echo ${RED}

.PHONY: autolint
autolint:
	@echo "${GREEN}Auto correction of python files...${RESET}";
	${AUTOPEP8_CMD} --in-place --aggressive --aggressive --verbose --ignore=${PEP8_IGNORE} $(PYTHON_FILES)

.PHONY: deploybranch
deploybranch:
	@echo "${GREEN}Deploying branch $(GIT_BRANCH) to dev...${RESET}";
	./scripts/deploybranch.sh

.PHONY: deletebranch
deletebranch:
	./scripts/delete_branch.sh $(BRANCH_TO_DELETE)

.PHONY: deploybranchint
deploybranchint:
	@echo "${GREEN}Deploying branch $(GIT_BRANCH) to dev and int...${RESET}";
	./scripts/deploybranch.sh int

.PHONY: deploybranchdemo
deploybranchdemo:
	@echo "${GREEN}Deploying branch $(GIT_BRANCH) to dev and demo...${RESET}";
	./scripts/deploybranch.sh demo

# Remove when ready to be merged
.PHONY: deploydev
deploydev:
	@if test "$(SNAPSHOT)" = "true"; \
	then \
		scripts/deploydev.sh -s; \
	else \
		scripts/deploydev.sh; \
	fi

.PHONY: deployint
deployint:
	scripts/deploysnapshot.sh $(SNAPSHOT) int $(NO_TESTS) $(DEPLOYCONFIG)

.PHONY: deployprod
deployprod:
	scripts/deploysnapshot.sh $(SNAPSHOT) prod $(NO_TESTS) $(DEPLOYCONFIG)

.PHONY: deploydemo
deploydemo:
	scritps/deploysnapshot.sh $(SNAPSHOT) demo

rc_branch.mako:
	@echo "${GREEN}Branch has changed${RESET}";
rc_branch: rc_branch.mako
	@echo "${GREEN}Creating branch template...${RESET}"
	${MAKO_CMD} \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "deploy_target=$(DEPLOY_TARGET)" \
		--var "branch_staging=$(BRANCH_STAGING)" $< > $@

deploy/deploy-branch.cfg.in:
	@echo "${GREEN]}Template file deploy/deploy-branch.cfg.in has changed${RESET}";
deploy/deploy-branch.cfg: deploy/deploy-branch.cfg.in
	@echo "${GREEN}Creating deploy/deploy-branch.cfg...${RESET}";
	${MAKO_CMD} --var "git_branch=$(GIT_BRANCH)" $< > $@

deploy/conf/00-branch.conf.in:
	@echo "${GREEN}Templat file deploy/conf/00-branch.conf.in has changed${RESET}";
deploy/conf/00-branch.conf: deploy/conf/00-branch.conf.in
	@echo "${GREEN}Creating deploy/conf/00-branch.conf...${RESET}"
	${MAKO_CMD} --var "git_branch=$(GIT_BRANCH)" $< > $@

apache/application.wsgi.mako:
	@echo "${GREEN}Template file apache/application.wsgi.mako has changed${RESET}";
apache/application.wsgi: apache/application.wsgi.mako
	@echo "${GREEN}Creating apache/application.wsgi...${RESET}";
	${MAKO_CMD} \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "modwsgi_config=$(MODWSGI_CONFIG)" $< > $@

apache/wsgi.conf.in:
	@echo "${GREEN}Template file apache/wsgi.conf.in has changed${RESET}";
apache/wsgi.conf: apache/wsgi.conf.in apache/application.wsgi
	@echo "${GREEN}Creating apache/wsgi.conf...${RESET}";
	${MAKO_CMD} \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "branch_staging=$(BRANCH_STAGING)" \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "modwsgi_user=$(MODWSGI_USER)" \
		--var "wsgi_threads=$(WSGI_THREADS)" \
		--var "wsgi_processes=$(WSGI_PROCESSES)" \
		--var "wsgi_app=$(WSGI_APP)" $< > $@

development.ini.in:
	@echo "${GREEN}Template file development.ini.in has changed${RESET}";
development.ini: development.ini.in
	@echo "${GREEN}Creating development.ini....${RESET}";
	${MAKO_CMD} \
		--var "app_version=$(VERSION)" \
		--var "server_port=$(SERVER_PORT)" $< > $@

production.ini.in:
	@echo "${GREEN}Template file production.ini.in has changed${RESET}";
production.ini: production.ini.in
	@echo "${GREEN}Creating production.ini...${RESET}";
	${MAKO_CMD} \
		--var "app_version=$(VERSION)" \
		--var "server_port=$(SERVER_PORT)" \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "api_url=$(API_URL)" \
		--var "http_proxy=$(HTTP_PROXY)" $< > $@

.venv/hooks: .venv/bin/git-secrets ./scripts/install-git-hooks.sh
	@echo "${GREEN}Installing git hooks${RESET}";
	./scripts/install-git-hooks.sh
	touch $@

requirements.txt:
	@echo "${GREEN}File requirements.txt has changed${RESET}";
.venv: requirements.txt
	@echo "${GREEN}Setting up virtual environement...${RESET}";
	@if [ ! -d $(INSTALL_DIRECTORY) ]; \
	then \
		virtualenv $(INSTALL_DIRECTORY); \
		${PIP_CMD} install --upgrade pip==9.0.1 setuptools --index-url ${PYPI_URL} ; \
	fi
	${PIP_CMD} install --index-url ${PYPI_URL} --find-links local_eggs/ -e .

.venv/bin/git-secrets: .venv
	@echo "${GREEN}Installing git secrets${RESET}";
	if [ ! -d ".git" ]; then git init; fi
	rm -rf .venv/git-secrets
	git clone https://github.com/awslabs/git-secrets .venv/git-secrets
	cd .venv/git-secrets && make install PREFIX=..
	(git config --local --get-regexp secret && git config --remove-section secrets) || cd
	.venv/bin/git-secrets --register-aws

.venv/last-version::
	mkdir -p $(dir $@)
	test $(VERSION) != $(LAST_VERSION) && echo $(VERSION) > .venv/last-version || :

fixrights:
	@echo "${GREEN}Fixing rights...${RESET}";
	chgrp -f -R geodata . || :
	chmod -f -R g+srwX . || :

.PHONY: clean
clean:
	rm -rf production.ini
	rm -rf development.ini
	rm -rf apache/wsgi.conf
	rm -rf apache/application.wsgi
	rm -rf rc_branch
	rm -rf deploy/deploy-branch.cfg
	rm -rf deploy/conf/00-branch.conf

.PHONY: cleanall
cleanall: clean
	rm -rf .venv
	rm -rf *.egg-info
