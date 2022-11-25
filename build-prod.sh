#!/bin/sh

export $(grep -v '^#' .env.prod | xargs)
docker-compose -f docker-compose.prod.yml --env-file .env.prod build
docker push $DOCKER_REGISTRY_IMAGE
