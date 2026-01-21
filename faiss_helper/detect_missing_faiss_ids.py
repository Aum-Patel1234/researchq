import faiss 
import psycopg2

def connet_to_db(db_string):
    return psycopg2.connect(db_string)

def detect_missing_faiss_ids(faiss_index_path, conn):
    # Load FAISS index
    index = faiss.read_index("paper.faiss")

    # Wrap with IndexIDMap to store custom IDs
    faiss_ids = faiss.IndexIDMap(index)

    # Connect to PostgreSQL database
    cursor = conn.cursor()

    # Fetch existing IDs from the database
    cursor.execute("SELECT id FROM embedding_chunks;")
    db_ids = {row[0] for row in cursor.fetchall()}

    # Detect missing IDs
    missing_ids = db_ids - set(faiss_ids.id_map)
    print(f"Detected {len(missing_ids)} missing IDs in FAISS index.")

    # Insert missing IDs into the database
    # if missing_ids:
    #     insert_query = "INSERT INTO faiss_ids_table (id) VALUES %s;"
    #     values = [(mid,) for mid in missing_ids]
    #     execute_values(cursor, insert_query, values)
    #     conn.commit()

    # Close database connection
    cursor.close()
    conn.close()

    return missing_ids

def get_vectors_for_ids(missing_ids, conn):
    cursor = conn.cursor()

    query = "SELECT (embedding_chunk_id, embedding) from embedding_vectors where embedding_chunk_id = ANY(%s);"
    cursor.execute(query, (list(missing_ids)))
    results = cursor.fetchall()
    cursor.close()
    return results

def insert_missing_ids_to_faiss_db(missing_ids, results, faiss_index_path):
    # Load FAISS index
    index = faiss.read_index(faiss_index_path)

    # Wrap with IndexIDMap to store custom IDs
    faiss_ids = faiss.IndexIDMap(index)

    # Add missing vectors to FAISS index
    for chunk_id, embedding in results:
        if chunk_id in missing_ids:
            faiss_ids.add_with_ids([embedding], [chunk_id])

    # Save the updated FAISS index
    faiss.write_index(faiss_ids, faiss_index_path)

def main():
    db_string = "dbname='final_year_rag' user='postgres' host='localhost' password='postgres' port=5432"
    faiss_index_path = "paper.faiss"

    conn = connet_to_db(db_string)
    missing_ids = detect_missing_faiss_ids(faiss_index_path, conn)
    if missing_ids:
        results = get_vectors_for_ids(missing_ids, conn)
        insert_missing_ids_to_faiss_db(missing_ids, results, faiss_index_path)

    print(f"Missing FAISS IDs: {missing_ids}")

if __name__ == "__main__":
    main()