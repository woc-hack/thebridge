
.PHONY: build
build:
	docker build -f Dockerfile -t ght_api .

.PHONY: run
run:
	docker run -v /var/run/mysqld:/var/mysqld -p 9002:9002 --name ght_api_instance ght_api
