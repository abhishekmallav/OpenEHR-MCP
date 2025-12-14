#!/bin/bash

echo "closing any running containers and removing volumes..."
docker compose down -v

echo "starting database container and initializing database..."
docker compose up -d db

echo "waiting for database to be ready..."
sleep 10

echo "creating roles and database..."
docker exec -i ehrbase-db psql -U postgres << 'EOF'
CREATE ROLE ehrbase WITH LOGIN PASSWORD 'ehrbase';
CREATE ROLE ehrbase_restricted WITH LOGIN PASSWORD 'ehrbase_restricted';
CREATE DATABASE ehrbase ENCODING 'UTF-8' LOCALE 'C' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE ehrbase TO ehrbase;
GRANT ALL PRIVILEGES ON DATABASE ehrbase TO ehrbase_restricted;
EOF

sleep 2
echo "configuring database schemas and extensions..."
docker exec -i ehrbase-db psql -U postgres -d ehrbase << 'EOF'
REVOKE CREATE ON SCHEMA public from PUBLIC;
CREATE SCHEMA IF NOT EXISTS ehr AUTHORIZATION ehrbase;
GRANT USAGE ON SCHEMA ehr to ehrbase_restricted;
ALTER DEFAULT PRIVILEGES FOR USER ehrbase IN SCHEMA ehr GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ehrbase_restricted;
ALTER DEFAULT PRIVILEGES FOR USER ehrbase IN SCHEMA ehr GRANT SELECT ON SEQUENCES TO ehrbase_restricted;
CREATE SCHEMA IF NOT EXISTS ext AUTHORIZATION ehrbase;
GRANT USAGE ON SCHEMA ext to ehrbase_restricted;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA ext;
ALTER DATABASE ehrbase SET search_path TO ext;
ALTER DATABASE ehrbase SET intervalstyle = 'iso_8601';
ALTER FUNCTION jsonb_path_query(jsonb,jsonpath,jsonb,boolean) ROWS 1;
EOF

sleep 2
echo "verifying roles and database..."
docker exec -it ehrbase-db psql -U postgres -c "\du"

sleep 2
echo "listing databases..."
docker exec -it ehrbase-db psql -U postgres -c "\l"

sleep 2
echo "starting ehrbase container..."
docker compose up -d ehrbase

echo "check the logs with"
echo "  docker compose logs -f ehrbase"
echo "  docker compose logs -f db" 

echo "check the status with"
echo "  curl http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4"