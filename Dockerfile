# Split out the wheel build into the non-slim image
# See https://github.com/docker-library/python/issues/869
FROM python:3.12 AS build
COPY requirements.txt ./
RUN --mount=type=cache,target=/var/cache/buildkit/pip \
    pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/mdiluz/matchy
LABEL org.opencontainers.image.description="Matchy matches matchees"
LABEL org.opencontainers.image.licenses=Unlicense

WORKDIR /usr/src/app
COPY requirements.txt ./
COPY --from=build /wheels /wheels
RUN --mount=type=cache,target=/var/cache/buildkit/pip \
    pip install --find-links /wheels --no-index -r requirements.txt

COPY . .
CMD ["python", "py/matchy.py"]