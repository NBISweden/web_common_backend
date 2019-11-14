SHELL := /bin/bash
XARGS=
USER_ID := $(shell ./getuid.sh)
path_makefile := $(abspath $(lastword $(MAKEFILE_LIST)))
rundir := $(dir $(path_makefile))

.PHONY: help init up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'init', 'up', 'down', 'clean' or 'ps' '\n"

init:
	@echo "DATA_DIR=  #set datadir, e.g. /data" > .env
	@echo "SCRATCH_DIR=  #set a path with large free diskspace which is writable by all, e.g. /scratch" >> .env
	@echo "WEB_STATIC=$(rundir)/proj/pred/static" >> .env
	@echo "USER_ID=$(USER_ID)" >> .env


up: .env docker-compose.yml
	@docker-compose up -d $(XARGS)

down: #.env
	@docker-compose down -v

clean:
	rm -f .env

ps:
	@docker-compose ps

clean-all: clean clean-volumes

preflight-check:
	@echo "Ensure the system is up"
	sleep 2

