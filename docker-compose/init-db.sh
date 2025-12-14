#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE ehrbase WITH LOGIN PASSWORD 'ehrbase';
    CREATE ROLE ehrbase_restricted WITH LOGIN PASSWORD 'ehrbase_restricted';
    CREATE DATABASE ehrbase ENCODING 'UTF-8' TEMPLATE template0;
    GRANT ALL PRIVILEGES ON DATABASE ehrbase TO ehrbase;
    GRANT ALL PRIVILEGES ON DATABASE ehrbase TO ehrbase_restricted;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ehrbase" <<-EOSQL
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    CREATE SCHEMA IF NOT EXISTS ehr AUTHORIZATION ehrbase;
    GRANT USAGE ON SCHEMA ehr TO ehrbase_restricted;
    ALTER DEFAULT PRIVILEGES FOR USER ehrbase IN SCHEMA ehr GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ehrbase_restricted;
    ALTER DEFAULT PRIVILEGES FOR USER ehrbase IN SCHEMA ehr GRANT SELECT ON SEQUENCES TO ehrbase_restricted;
    CREATE SCHEMA IF NOT EXISTS ext AUTHORIZATION ehrbase;
    GRANT USAGE ON SCHEMA ext TO ehrbase_restricted;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA ext;
    ALTER DATABASE ehrbase SET search_path TO ext;
    ALTER DATABASE ehrbase SET intervalstyle = 'iso_8601';
EOSQL
