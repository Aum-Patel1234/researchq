import faiss
import numpy as np
import psycopg2


def connet_to_db(db_string):
    return psycopg2.connect(db_string)


def detect_missing_faiss_ids(faiss_index_path: str, conn):
    # Load FAISS index
    index = faiss.read_index(faiss_index_path)

    if not isinstance(index, faiss.IndexIDMap):
        raise RuntimeError("FAISS index is not an IndexIDMap")

    faiss_ids = set(faiss.vector_to_array(index.id_map))

    # Connect to PostgreSQL database
    cursor = conn.cursor()

    # Fetch existing IDs from the database
    cursor.execute("SELECT id FROM embedding_chunks;")
    db_ids = {row[0] for row in cursor.fetchall()}

    # Detect missing IDs
    missing_ids = db_ids - faiss_ids
    print(f"Detected {len(missing_ids)} missing IDs in FAISS index.")

    # Insert missing IDs into the database
    # if missing_ids:
    #     insert_query = "INSERT INTO faiss_ids_table (id) VALUES %s;"
    #     values = [(mid,) for mid in missing_ids]
    #     execute_values(cursor, insert_query, values)
    #     conn.commit()
    print(f"FAISS vectors: {index.ntotal}")
    print(f"DB chunks: {len(db_ids)}")
    print(f"Missing IDs: {len(missing_ids)}")

    cursor.close()

    return missing_ids


def get_vectors_for_ids(missing_ids, conn):
    cursor = conn.cursor()

    query = """
        SELECT embedding_chunk_id, embedding
        FROM embedding_vectors
        WHERE embedding_chunk_id = ANY(%s);
    """
    cursor.execute(query, (list(missing_ids),))
    results = cursor.fetchall()
    cursor.close()
    return results


def parse_pgvector(embedding):
    if isinstance(embedding, str):
        embedding = embedding.strip("[]")
        return np.fromstring(embedding, sep=",", dtype=np.float32)
    elif isinstance(embedding, (list, tuple)):
        return np.asarray(embedding, dtype=np.float32)
    else:
        return np.asarray(embedding, dtype=np.float32)


def insert_missing_ids_to_faiss_db(missing_ids, results, faiss_index_path):
    # Load FAISS index
    index = faiss.read_index(faiss_index_path)
    print("type of index - ", type(index))
    if not isinstance(index, faiss.IndexIDMap):
        index = faiss.IndexIDMap(index)

    vectors = []
    ids = []

    for chunk_id, embedding in results:
        if chunk_id in missing_ids:
            vec = parse_pgvector(embedding)
            if vec.shape[0] != index.d:
                raise ValueError(f"Embedding dim mismatch: {vec.shape[0]} != {index.d}")

            vectors.append(vec)
            ids.append(chunk_id)

    vectors = np.array(vectors, dtype="float32")
    ids = np.array(ids, dtype="int64")

    index.add_with_ids(vectors, ids)

    faiss.write_index(index, faiss_index_path)
    print(f"Inserted {len(ids)} missing vectors into FAISS.")


def main():
    db_string = "dbname='final_year_rag' user='postgres' host='localhost' password='postgres' port=5432"
    faiss_index_path = "paper.faiss"

    conn = connet_to_db(db_string)
    missing_ids = detect_missing_faiss_ids(faiss_index_path, conn)
    if missing_ids:
        results = get_vectors_for_ids(missing_ids, conn)
        print(results[0][0], type(results[0][1]))
        insert_missing_ids_to_faiss_db(missing_ids, results, faiss_index_path)

    conn.close()
    # print(f"Missing FAISS IDs: {missing_ids}")


if __name__ == "__main__":
    main()
