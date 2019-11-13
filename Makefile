SHELL := /bin/bash
XARGS=
USER_ID := $(shell ./getuid.sh)

.PHONY: help init up down clean ps

help:
	@echo "Usage: make <target>\n"
	@echo "where <target> is: 'init', 'up', 'down', 'clean' or 'ps' '\n"

init:
	@echo "USER_ID=$(USER_ID)" > .env


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

