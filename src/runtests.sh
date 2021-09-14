docker-compose -f local.yml run --rm django isort .
docker-compose -f local.yml run --rm django flake8
# docker-compose -f local.yml run --rm django mypy rard
docker-compose -f local.yml run --rm django coverage run -m pytest
docker-compose -f local.yml run --rm django coverage html
docker-compose -f local.yml run --rm django coverage report
