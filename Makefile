build:
	docker build -t sizer/glances .

run:
	docker run -v /var/run/docker.sock:/var/run/docker.sock:ro --pid host --rm -it sizer/glances
