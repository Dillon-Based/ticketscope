# The Postgres image (AD-9): the CloudNativePG `standard` PostgreSQL 18 image,
# which already carries pgvector, plus the PGDG pg_textsearch package.
# The Cluster preloads pg_textsearch through shared_preload_libraries.
ARG BASE_IMAGE=ghcr.io/cloudnative-pg/postgresql:18-standard-trixie
FROM ${BASE_IMAGE}

ARG PG_TEXTSEARCH_VERSION=1.5.1

USER root
# The base image already has the apt.postgresql.org (PGDG) source configured.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      "postgresql-18-pg-textsearch=${PG_TEXTSEARCH_VERSION}-*" \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
USER 26
