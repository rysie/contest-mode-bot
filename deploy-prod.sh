#!/bin/sh
export $(grep -v '^#' .env.prod | xargs)

docker pull $DOCKER_REGISTRY_IMAGE
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
