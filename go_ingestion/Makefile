APP_NAME=go_ingestion
CMD=./main.go    # change if main.go is in root
BINARY=bin/$(APP_NAME)

deps:
	go mod tidy
	go mod vendor

build:
	go build -o $(BINARY) $(CMD)

run:
	./bin/go_ingestion

test:
	go test ./... -v

fmt:
	go fmt ./...
	go vet ./...

clean:
	rm -rf bin vendor

docker-build:
	docker build -t $(APP_NAME):latest .

docker-run:
	docker run --rm -it $(APP_NAME):latest
