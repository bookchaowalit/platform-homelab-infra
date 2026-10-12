---
title: "Solo Empire Self-Hosted Stack — Learning Exercises"
tags: [documentation, infra]
created: 2026-07-09
updated: 2026-08-08
description: "Documentation for Solo Empire Self-Hosted Stack — Learning Exercises."
---

# Solo Empire Self-Hosted Stack — Learning Exercises

Hands-on exercises for each domain covered by the 40-service learning lab.

---

## Phase 1: Infrastructure Basics

### Exercise 1.1 — Docker Fundamentals
**Goal**: Understand container lifecycle and resource usage.

1. List all running containers: `docker ps`
2. Check resource usage: `docker stats`
3. Inspect a container's config: `docker inspect se-grafana`
4. View container logs: `docker logs se-prometheus --tail 50`
5. Exec into a container: `docker exec -it se-alpine sh`

**Questions**:
- What's the difference between `docker stop` and `docker kill`?
- How much RAM does the entire stack consume?

---

### Exercise 1.2 — Docker Compose Orchestration
**Goal**: Understand service dependencies and volume management.

1. View the compose file: `cat docker-compose.yml`
2. List all volumes: `docker volume ls | grep self-hosted`
3. Inspect a volume: `docker volume inspect self-hosted-stack_postgres-data`
4. Find where a volume is mounted on disk: `docker volume inspect --format '{{ .Mountpoint }}' self-hosted-stack_postgres-data`

**Challenge**: Add a new service to docker-compose.yml (e.g., [Adminer](https://hub.docker.com/_/adminer) for PostgreSQL admin).

---

### Exercise 1.3 — Reverse Proxy with Traefik
**Goal**: Understand how Traefik routes traffic to services.

1. Access Traefik dashboard: http://localhost:3001
2. Examine the labels on a service:
   ```bash
   docker inspect se-grafana | grep -A 10 "labels"
   ```
3. Check Traefik's dynamic config: `docker logs se-traefik | grep "Configuration loaded"`

**Challenge**: Add a new route in Traefik for a service. What labels are needed?

---

## Phase 2: Data Engineering

### Exercise 2.1 — DuckDB Analytics
**Goal**: Practice SQL analytics with DuckDB.

1. Access DuckDB via the Jupyter notebook or CLI
2. Create a sample table:
   ```sql
   CREATE TABLE metrics (
     timestamp TIMESTAMP DEFAULT now(),
     service VARCHAR,
     cpu_usage DOUBLE,
     memory_mb INTEGER
   );
   ```
3. Insert sample data and run aggregations:
   ```sql
   SELECT service, AVG(cpu_usage), MAX(memory_mb)
   FROM metrics
   GROUP BY service
   ORDER BY AVG(cpu_usage) DESC;
   ```

**Challenge**: Import a CSV file into DuckDB and query it.

---

### Exercise 2.2 — Prefect Orchestration
**Goal**: Understand workflow orchestration.

1. Access Prefect UI: http://localhost:3020
2. Create a simple flow:
   ```python
   from prefect import flow, task
   
   @task
   def extract():
       return [1, 2, 3, 4, 5]
   
   @task
   def transform(data):
       return [x * 2 for x in data]
   
   @task
   def load(data):
       print(f"Loading: {data}")
   
   @flow
   def etl_pipeline():
       data = extract()
       transformed = transform(data)
       load(transformed)
   
   if __name__ == "__main__":
       etl_pipeline()
   ```
3. Register and run the flow in Prefect UI.

**Challenge**: Add error handling and retries to the flow.

---

### Exercise 2.3 — InfluxDB Time-Series
**Goal**: Store and query time-series data.

1. Access InfluxDB UI: http://localhost:3010
2. Create a bucket called `metrics`
3. Write data via API:
   ```bash
   curl -X POST "http://localhost:8086/api/v2/write?org=solo-empire&bucket=metrics" \
     -H "Authorization: Token ${INFLUX_TOKEN}" \
     -d 'cpu,host=server1 usage=45.2
   cpu,host=server2 usage=78.9'
   ```
4. Query with Flux:
   ```flux
   from(bucket: "metrics")
     |> range(start: -1h)
     |> filter(fn: (r) => r._measurement == "cpu")
   ```

**Challenge**: Set up a continuous query to downsample data.

---

## Wave 1: Security

### Exercise W1.1 — Vaultwarden Password Manager
**Goal**: Understand secrets management.

1. Access Vaultwarden: http://localhost:3015
2. Create an account and add some test entries
3. Explore the API: https://vaultwarden.example.com/api/docs

**Challenge**: Set up emergency access with a trusted contact.

---

### Exercise W1.2 — Step CA (PKI)
**Goal**: Understand certificate authority operations.

1. Check Step CA status:
   ```bash
   docker exec se-step-ca step-ca --version
   ```
2. Generate a certificate:
   ```bash
   docker exec se-step-ca step certificate create \
     "test.example.com" test.crt test.key \
     --ca /certs/root_ca.crt \
     --ca-key /certs/root_ca_key
   ```
3. Inspect the certificate:
   ```bash
   docker exec se-step-ca step certificate inspect test.crt
   ```

**Challenge**: Set up automatic certificate renewal.

---

## Wave 2: Databases

### Exercise W2.1 — PostgreSQL
**Goal**: Master relational database operations.

1. Connect to PostgreSQL:
   ```bash
   docker exec -it se-postgres psql -U postgres
   ```
2. Create a database and table:
   ```sql
   CREATE DATABASE learning;
   \c learning
   CREATE TABLE users (
     id SERIAL PRIMARY KEY,
     name VARCHAR(100),
     email VARCHAR(255) UNIQUE,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```
3. Insert and query data:
   ```sql
   INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
   SELECT * FROM users;
   ```

**Challenge**: Create an index and measure query performance with `EXPLAIN ANALYZE`.

---

### Exercise W2.2 — Valkey (Redis)
**Goal**: Understand in-memory data structures.

1. Connect to Valkey:
   ```bash
   docker exec -it se-valkey valkey-cli
   ```
2. Practice data structures:
   ```
   SET user:1 "Alice"
   GET user:1
   HSET user:2 name "Bob" age 30
   HGETALL user:2
   LPUSH queue "task1" "task2"
   LRANGE queue 0 -1
   ```
3. Set expiration: `SET session:abc "data" EX 60`

**Challenge**: Implement a rate limiter using Valkey.

---

### Exercise W2.3 — Qdrant Vector Database
**Goal**: Understand vector similarity search.

1. Access Qdrant dashboard: http://localhost:3025
2. Create a collection via API:
   ```bash
   curl -X PUT "http://localhost:6333/collections/test_collection" \
     -H "Content-Type: application/json" \
     -d '{"vectors": {"size": 4, "distance": "Dot"}}'
   ```
3. Add vectors:
   ```bash
   curl -X PUT "http://localhost:6333/collections/test_collection/points" \
     -H "Content-Type: application/json" \
     -d '{"points": [{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]}, {"id": 2, "vector": [0.2, 0.1, 0.4, 0.3]}]}'
   ```
4. Search:
   ```bash
   curl -X POST "http://localhost:6333/collections/test_collection/points/search" \
     -H "Content-Type: application/json" \
     -d '{"vector": [0.15, 0.25, 0.35, 0.45], "limit": 2}'
   ```

**Challenge**: Build a simple semantic search engine with Ollama embeddings.

---

## Wave 3: Messaging

### Exercise W3.1 — NATS Messaging
**Goal**: Understand pub/sub and queue patterns.

1. Subscribe to a topic:
   ```bash
   docker exec -it se-nats nats sub "test.>" --server nats://localhost:4222
   ```
2. Publish a message (in another terminal):
   ```bash
   docker exec -it se-nats nats pub "test.hello" "Hello NATS!" --server nats://localhost:4222
   ```

**Challenge**: Implement a request-reply pattern.

---

### Exercise W3.2 — Mosquitto (MQTT)
**Goal**: Understand IoT messaging protocols.

1. Subscribe to a topic:
   ```bash
   docker exec -it se-mosquitto mosquitto_sub -t "sensors/temperature" -v
   ```
2. Publish a message:
   ```bash
   docker exec -it se-mosquitto mosquitto_pub -t "sensors/temperature" -m "22.5"
   ```

**Challenge**: Set up MQTT with TLS using Step CA certificates.

---

### Exercise W3.3 — RabbitMQ
**Goal**: Understand message queues and exchanges.

1. Access RabbitMQ Management: http://localhost:3019 (guest/guest)
2. Create a queue via UI or CLI:
   ```bash
   docker exec se-rabbitmq rabbitmqadmin declare queue name=test_queue durable=true
   ```
3. Publish a message:
   ```bash
   docker exec se-rabbitmq rabbitmqadmin publish routing_key=test_queue payload='"Hello"'
   ```
4. Consume the message:
   ```bash
   docker exec se-rabbitmq rabbitmqadmin get queue=test_queue ackmode=ack_requeue_false
   ```

**Challenge**: Set up a topic exchange with multiple bindings.

---

## Wave 4: API & Code Hosting

### Exercise W4.1 — Gitea Git Hosting
**Goal**: Understand self-hosted Git operations.

1. Access Gitea: http://localhost:3003
2. Create an account and repository
3. Clone via SSH:
   ```bash
   git clone git@localhost:username/repo.git
   ```
4. Set up a webhook to trigger Woodpecker CI.

**Challenge**: Mirror an external repository and set up auto-sync.

---

### Exercise W4.2 — Woodpecker CI
**Goal**: Understand CI/CD pipelines.

1. Access Woodpecker: http://localhost:3004
2. Create a `.woodpecker.yml` pipeline:
   ```yaml
   steps:
     - name: test
       image: alpine
       commands:
         - echo "Running tests..."
         - echo "All tests passed!"
     
     - name: build
       image: alpine
       commands:
         - echo "Building..."
   ```
3. Push to Gitea and watch the pipeline run.

**Challenge**: Add a deployment step that triggers on tags.

---

## Wave 5: File Storage

### Exercise W5.1 — Filebrowser
**Goal**: Understand file management interfaces.

1. Access Filebrowser: http://localhost:3016 (admin/admin)
2. Upload files via the web UI
3. Create shared links for files
4. Explore the API: http://localhost:3016/api

**Challenge**: Set up user permissions for different directories.

---

### Exercise W5.2 — Garage (S3-compatible)
**Goal**: Understand object storage.

1. Install AWS CLI or use `s3cmd`
2. Configure credentials (get from Garage admin)
3. Create a bucket:
   ```bash
   aws --endpoint-url http://localhost:3900 s3 mb s3://test-bucket
   ```
4. Upload a file:
   ```bash
   aws --endpoint-url http://localhost:3900 s3 cp test.txt s3://test-bucket/
   ```
5. List objects:
   ```bash
   aws --endpoint-url http://localhost:3900 s3 ls s3://test-bucket/
   ```

**Challenge**: Set up bucket policies and presigned URLs.

---

## Wave 6: Communication

### Exercise W6.1 — Listmonk Email Marketing
**Goal**: Understand email campaign management.

1. Access Listmonk: http://localhost:3017 (listmonk/listmonk)
2. Create a subscriber list
3. Design a campaign template
4. Schedule a test campaign

**Challenge**: Set up double opt-in for new subscribers.

---

### Exercise W6.2 — Gotify Push Notifications
**Goal**: Understand push notification systems.

1. Access Gotify: http://localhost:3018 (admin/gotify)
2. Create an application
3. Send a notification:
   ```bash
   curl -X POST "http://localhost:3018/message?token=YOUR_APP_TOKEN" \
     -F "title=Test" -F "message=Hello from Gotify!"
   ```

**Challenge**: Integrate Gotify with backup script alerts.

---

## Wave 7: Documentation

### Exercise W7.1 — Wiki.js
**Goal**: Understand knowledge management systems.

1. Access Wiki.js: http://localhost:3021
2. Create a page with Markdown
3. Set up page permissions
4. Explore the GraphQL API

**Challenge**: Create a documentation structure for the self-hosted stack.

---

## Wave 8: Machine Learning

### Exercise W8.1 — Ollama LLM
**Goal**: Understand local LLM inference.

1. Pull a model:
   ```bash
   docker exec -it se-ollama ollama pull llama2
   ```
2. Run inference:
   ```bash
   docker exec -it se-ollama ollama run llama2 "What is Docker?"
   ```
3. List models: `docker exec -it se-ollama ollama list`

**Challenge**: Build a simple RAG pipeline with Qdrant and Ollama.

---

### Exercise W8.2 — Jupyter Notebooks
**Goal**: Practice interactive computing.

1. Access Jupyter: http://localhost:3022
2. Create a new Python notebook
3. Install packages: `!pip install pandas matplotlib`
4. Create a visualization:
   ```python
   import matplotlib.pyplot as plt
   import numpy as np
   
   x = np.linspace(0, 10, 100)
   plt.plot(x, np.sin(x))
   plt.title("Sine Wave")
   plt.show()
   ```

**Challenge**: Connect Jupyter to DuckDB and visualize query results.

---

## Wave 9: Networking

### Exercise W9.1 — CoreDNS
**Goal**: Understand DNS resolution.

1. Query CoreDNS:
   ```bash
   dig @localhost -p 5300 example.com
   ```
2. Check CoreDNS logs: `docker logs se-coredns`
3. Examine the Corefile: `docker exec se-coredns cat /etc/coredns/Corefile`

**Challenge**: Add a custom DNS record for a local service.

---

### Exercise W9.2 — Caddy Web Server
**Goal**: Understand modern web server configuration.

1. Access Caddy: http://localhost:3026
2. Check Caddy's automatic HTTPS: `docker logs se-caddy`
3. Examine the Caddyfile: `docker exec se-caddy cat /etc/caddy/Caddyfile`

**Challenge**: Configure Caddy as a reverse proxy for a new service.

---

### Exercise W9.3 — AdGuard Home
**Goal**: Understand DNS-level ad blocking.

1. Access AdGuard: http://localhost:3028 (admin/admin)
2. Check query statistics
3. Add a custom filter list
4. Test ad blocking by visiting ad-heavy sites

**Challenge**: Set up custom filtering rules for specific domains.

---

## Wave 10: Observability

### Exercise W10.1 — Prometheus + Grafana
**Goal**: Understand metrics collection and visualization.

1. Access Prometheus: http://localhost:3005
2. Query metrics: `container_cpu_usage_seconds_total`
3. Access Grafana: http://localhost:3006 (admin/admin)
4. Import a dashboard (ID: 13496 for Docker)
5. Create a custom panel showing container memory usage.

**Challenge**: Set up an alert rule for high CPU usage.

---

### Exercise W10.2 — Loki Logs
**Goal**: Understand log aggregation.

1. Access Grafana Explore: http://localhost:3006/explore
2. Select Loki as data source
3. Query logs: `{container_name="se-postgres"}`
4. Parse JSON logs: `{container_name="se-traefik"} | json`

**Challenge**: Create a dashboard combining logs and metrics.

---

### Exercise W10.3 — Tempo Tracing
**Goal**: Understand distributed tracing.

1. Access Tempo: http://localhost:3024
2. Search for traces in Grafana
3. Examine a trace waterfall view

**Challenge**: Instrument a simple app to send traces to Tempo.

---

### Exercise W10.4 — Gatus Health Monitoring
**Goal**: Understand service health checking.

1. Access Gatus: http://localhost:3027
2. Review the health checks: `cat gatus/config.yaml`
3. Check endpoint history and uptime percentages

**Challenge**: Add a new endpoint with custom conditions.

---

## Capstone Projects

### Project 1: Full-Stack Monitoring Dashboard
Build a dashboard that shows:
- Service health (Gatus)
- Resource usage (Prometheus + Grafana)
- Recent logs (Loki)
- Backup status (custom script)

### Project 2: CI/CD Pipeline with GitOps
- Push code to Gitea
- Woodpecker runs tests
- On success, deploy to a staging environment
- Gatus verifies deployment health

### Project 3: Data Pipeline E2E
- Extract data from an API (Prefect flow)
- Store in PostgreSQL and InfluxDB
- Visualize in Grafana
- Set up alerts for anomalies

### Project 4: Secure Development Environment
- Use Step CA for internal TLS
- Vaultwarden for secrets
- Gitea for code
- Woodpecker for CI
- AdGuard for DNS security

---

## Tips for Success

1. **Start small**: Complete one exercise per day
2. **Take notes**: Document what you learn in Wiki.js
3. **Break things**: It's a learning lab — experiment freely
4. **Restore from backups**: Test the backup script regularly
5. **Monitor everything**: Use Gatus + Grafana to observe your experiments

---

## Resources

- [Docker Docs](https://docs.docker.com/)
- [Traefik Docs](https://doc.traefik.io/traefik/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [Redis Commands](https://redis.io/commands)
- [Flux Language Guide](https://docs.influxdata.com/influxdb/v2/reference/flux/)

---

**Total exercises**: 30+ hands-on challenges across 10 domains
**Estimated time**: 40-60 hours for complete lab mastery
