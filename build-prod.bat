@echo off

FOR /F "eol=# tokens=*" %%i IN (%~dp0.env.prod) DO SET %%i

echo Building %DOCKER_REGISTRY_IMAGE%
echo ---------------------------------

docker-compose -f docker-compose.prod.yml --env-file .env.prod build && ^
docker push %DOCKER_REGISTRY_IMAGE%

FOR /F "eol=# tokens=*" %%i IN (%~dp0.env) DO SET %%i
