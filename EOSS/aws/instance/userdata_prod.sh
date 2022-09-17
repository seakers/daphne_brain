#!/bin/bash
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)
sudo service docker start
sudo $(sudo aws ecr get-login --region us-east-2 --no-include-email)
sudo docker pull 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator
ENV_STRING=""
JSON_TAGS=$(aws ec2 describe-tags --filters "Name=resource-id,Values=${INSTANCE_ID}" --region=us-east-2)
for row in $(echo ${JSON_TAGS} | jq -c '.Tags[]'); do
        var_key=$(echo ${row} | jq -r '.Key')
        var_value=$(echo ${row} | jq -r '.Value')
        ENV_STRING+="--env ${var_key}=${var_value} "
done
sudo docker run --name=evaluator ${ENV_STRING} 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator:latest