#!/usr/bin/env bash
docker build -t kafka_mongo .
docker tag c_utility_scoring:latest trungtv:5005/c_utility_scoring:d.1.1.2
docker push trungtv:5005/c_utility_scoring:d.1.1.2

docker build -t c_utility_scoring .
docker tag c_utility_scoring:latest webapp:5005/c_utility_scoring:p.1.0.4
docker push webapp:5005/c_utility_scoring:p.1.0.4
