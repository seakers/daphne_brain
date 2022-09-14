#!/bin/sh

cd /app
env $(cat .env | tr -d '\r') python3 manage.py makemigrations
env $(cat .env | tr -d '\r') python3 manage.py migrate