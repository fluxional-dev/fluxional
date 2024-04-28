if [ "$*" = "--no-tests" ]
then
    echo "Skipping tests..."
else
    poetry run coverage run -m pytest -vv $@
fi

poetry run mypy fluxional/
poetry run ruff fluxional/ --no-cache
poetry run coverage html