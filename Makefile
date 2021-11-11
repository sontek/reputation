HERE = $(shell pwd)

.PHONY: all

all: 
	@echo Please run make dev or make prod

dev:
	docker-compose -f docker-compose.yml up --build

prod:
	docker build api/ -t sontek/baddies-api
	docker build redis/ -t sontek/baddies-redis

push-prod:
	docker push sontek/baddies-api
	docker push sontek/baddies-redis

format-code:
	docker-compose run api black api/

lint:
	# docker-compose build
	docker-compose run api flake8

test:
	# docker-compose build
	docker-compose run api pytest -vvv

