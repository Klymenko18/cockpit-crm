FROM postgres:14
ENV POSTGRES_DB=app POSTGRES_USER=app POSTGRES_PASSWORD=app TZ=UTC
COPY docker/postgres/init.sql /docker-entrypoint-initdb.d/00-init.sql
