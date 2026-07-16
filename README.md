### Build:
`docker compose up --build`

### Stop:
`docker compose down`

### Start:
`docker compose up --d`

### Frontend
`http://localhost:3000`
`docker compose restart frontend`

### Backend
`http://localhost:8000`

To Check Logs: `docker compose logs -f backend`

### Neo4j
`http://localhost:7474`

Protocol: `neo4j://`
#### Login:
```
neo4j
password
```
#### To Delete all nodes:
```
MATCH (n)
DETACH DELETE n;
```

### PostgreSQL
`docker exec -it enterprisediscovery-to-deliveryengine-postgres-1 psql -U postgres -d enterprise`

To delete all the data's from the DB
```
DELETE FROM document_chunks;
DELETE FROM documents;
```

### Ollama
`set OLLAMA_NO_GPU=1`

`ollama run qwen2.5-coder:7b`