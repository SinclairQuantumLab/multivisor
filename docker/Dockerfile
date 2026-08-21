# syntax=docker/dockerfile:1
FROM python:3.12-alpine AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

WORKDIR /usr/app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/app/venv

COPY . multivisor/
WORKDIR /usr/app/multivisor

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra rpc --extra web --no-editable

FROM python:3.12-alpine

RUN mkdir /var/log/supervisord

COPY --from=build /usr/app/venv /usr/app/venv

ENV PATH=/usr/app/venv/bin:$PATH

COPY docker/multivisor/multivisor.conf /etc/
COPY docker/supervisord/ /etc/supervisord
COPY docker/bin/* /usr/local/bin/
