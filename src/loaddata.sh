#!/bin/sh
set -eu
if [ -z $1 ]
then
echo "Usage: ./loaddata.sh <json-filename-to-load>"
exit 1
fi
for environment in local development production
do
container=$(docker ps -f status=running -f ancestor=rard_${environment}_django --format "{{.ID}}")
if [ -n "${container}" ]
then
echo ${environment} environment
docker cp $1 ${container}:/app/dump.json
docker exec -it ${container} /bin/bash -c ". /entrypoint && LOADING=true python ./manage.py loaddata /app/dump.json"
exit 0
fi
done
echo "Error: no RARD Django container running"
exit 1
