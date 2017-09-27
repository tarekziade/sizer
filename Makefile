build:
	docker build -t sizer/glances .

run:
	docker run -v /var/run/docker.sock:/var/run/docker.sock:ro --pid host --rm -it sizer/glances


docker-build:
	sudo docker build -t sizer-glances:latest .

docker-run:
	sudo docker run --name sizer-glances --rm -it sizer-glances:latest

docker-push:
	sudo docker login
	sudo docker run --name sizer-glances -it sizer-glances:latest ls
	sudo docker commit -m "savepoint" -a "sizer-glances" sizer-glances tarekziade/sizer-glances:latest
	sudo docker push tarekziade/sizer-glances

