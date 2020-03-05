#!/usr/bin/env bash

echo "Updating python dependencies"

echo "docker build -t $IMAGE -f 'tools/Dockerfile' ."

docker build -t $IMAGE -f "tools/Dockerfile" .
