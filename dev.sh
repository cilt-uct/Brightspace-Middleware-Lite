#! /bin/bash

bash ./base.sh
cp .env.run app/service/.env
cp VERSION app/service/VERSION
cd app/service/
uvicorn api:app --reload --port 9091 --root-path="/lite"
