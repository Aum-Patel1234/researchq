package main

import (
	"fmt"
	"go_ingestion/db"
	"log"
	"os"

	"github.com/joho/godotenv"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
		return
	}

	dbPool := db.ConnectToDb()
	defer dbPool.Close()

	const query = "nlp"
	var semanticScholarApiKey = os.Getenv("SPRINGER_NATURE_META_APIKEY")
	var springerNatureApiKey = os.Getenv("SPRINGER_NATURE_OPEN_ACCESS_APIKEY")
	if semanticScholarApiKey == "" || springerNatureApiKey == "" {
		log.Fatal("Required API keys are missing. Exiting...")
	}

	fmt.Println("Executed Successfully")
}
