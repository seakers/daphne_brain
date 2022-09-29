#!/bin/bash

INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

# --> 1. Get container image
sudo service docker start
sudo $(sudo aws ecr get-login --region us-east-2 --no-include-email)
sudo docker pull 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator

# --> 2. Get container env variables from instance tags
ENV_STRING=""
JSON_TAGS=$(aws ec2 describe-tags --filters "Name=resource-id,Values=${INSTANCE_ID}" --region=us-east-2)
for row in $(echo ${JSON_TAGS} | jq -c '.Tags[]'); do
        var_key=$(echo ${row} | jq -r '.Key')
        var_value=$(echo ${row} | jq -r '.Value')
        ENV_STRING+="--env ${var_key}=${var_value} "
done


# --> 3. Start container
sudo docker run --name=evaluator ${ENV_STRING} 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator:latest



# --> Design Evaluator AMI Setup Commands
#sudo yum -y update
#sudo yum -y install jq wget
#sudo amazon-linux-extras install docker
#sudo groupadd docker
#sudo usermod -aG docker ec2-user
#sudo systemctl enable amazon-ssm-agent
#sudo systemctl start amazon-ssm-agent
#sudo $(sudo aws ecr get-login --region us-east-2 --no-include-email)
#sudo docker pull 923405430231.dkr.ecr.us-east-2.amazonaws.com/design-evaluator