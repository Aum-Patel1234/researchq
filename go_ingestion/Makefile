APP_NAME=go_ingestion
CMD=./cmd/ingestion   # change if main.go is in root
BINARY=bin/$(APP_NAME)

deps:
	go mod tidy

build:
	go build -o $(BINARY) $(CMD)

run:
	go run $(CMD)

test:
	go test ./... -v

fmt:
	go fmt ./...
	go vet ./...

clean:
	rm -rf bin

docker-build:
	docker build -t $(APP_NAME):latest .

docker-run:
	docker run --rm -it $(APP_NAME):latest
