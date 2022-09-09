#!/bin/sh

cd /app
env $(cat .env | tr -d '\r') daphne -b 0.0.0.0 -p 8000 daphne_brain.asgi:application