-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create initial schema
CREATE SCHEMA IF NOT EXISTS logs;

-- Grant permissions
GRANT ALL ON SCHEMA logs TO logsuser;
