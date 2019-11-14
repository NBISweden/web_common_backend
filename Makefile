SHELL := /bin/bash
XARGS=
USER_ID := $(shell ./getuid.sh)
path_makefile := $(abspath $(lastword $(MAKEFILE_LIST)))
rundir := $(dir $(path_makefile))

# Please change if you have other settings\
DATA_DIR=/data\
BLASTDB_DIR=/data/blastdb\
ROSETTA_DIR=/data/rosetta/rosetta_bin_linux_2016.15.58628_bundle\
SCRATCH_DIR=/scratch\
# Don't change from here\
WEB_STATIC=$(rundir)/proj/pred/static\
USER_ID=$(USER_ID)\

.PHONY: help init up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'init', 'up', 'down', 'clean' or 'ps' '\n"

init:
	@echo "# Please change if you have other settings" > .env
	@echo "DATA_DIR=/data" >> .env
	@echo "BLASTDB_DIR=/data/blastdb" >> .env
	@echo "ROSETTA_DIR=/data/rosetta/rosetta_bin_linux_2016.15.58628_bundle" >> .env
	@echo "SCRATCH_DIR=/scratch" >> .env
	@echo "# Don't change from here" >> .env
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

