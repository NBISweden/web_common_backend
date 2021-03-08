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
	@echo "# Please change if you have different settings" > .env
	@echo "DATA_DIR=/data" >> .env
	@echo "TOPCONSDB_DIR=/data/topcons2_database" >> .env
	@echo "BLASTDB_DIR=/data/blastdb" >> .env
	@echo "ROSETTA_DIR=/data/rosetta/rosetta_bin_linux_2016.15.58628_bundle" >> .env
	@echo "SCRATCH_DIR=/scratch" >> .env
	@echo "" >> .env
	@echo "# Please don't change from here" >> .env
	@echo "WEB_STATIC=${rundir}/proj/pred/static" >> .env
	@echo "USER_ID=$(USER_ID)" >> .env


up: .env docker-compose-apps.yml
	@docker-compose -f docker-compose-apps.yml up -d $(XARGS)

down: #.env
	@docker-compose -f docker-compose-apps.yml down -v

clean:
	rm -f .env

ps:
	@docker-compose -f docker-compose-apps.yml ps

clean-all: clean clean-volumes

preflight-check:
	@echo "Ensure the system is up"
	sleep 2

