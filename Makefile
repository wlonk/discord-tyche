default:
	docker build . -t tychebot:latest

run:
	docker run --rm -it --env-file .env tychebot

shell:
	docker run --rm -it tychebot /bin/bash

lock:
	docker run --rm -it --volume ${PWD}:/app tychebot pip-compile --output-file=requirements.txt requirements.in

clean:
	docker image prune
	docker ps -qa | xargs docker rm
	docker images -q | xargs docker rmi
