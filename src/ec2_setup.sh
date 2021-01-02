#!/bin/bash

# Docker Installation
cd home/ec2-user
mkdir log

sudo yum update -y > log/setup 2> log/setup_e
sudo yum install docker -y >> log/setup 2>> log/setup_e
sudo usermod -aG docker ec2-user >> log/setup 2>> log/setup_e
sudo systemctl start docker >> log/setup 2>> log/setup_e
sudo systemctl enable docker >> log/setup 2>> log/setup_e

sudo curl -L --fail https://raw.githubusercontent.com/linuxserver/docker-docker-compose/master/run.sh -o /usr/local/bin/docker-compose >> log/setup_e 2>> log/setup_e
sudo chmod +x /usr/local/bin/docker-compose >> log/setup_e 2>> log/setup_e

# S3 Sync
aws s3 sync s3://$PROJECT/deployment_files . > log/setup 2> log/setup_e

# in all repos
for d in */ ; do
  cd "$d"

  # Docker compose up
  docker-compose up --detach > log/setup 2> log/setup_e
  
  # Configure
  sh setup.sh > ../log/setup 2> ../log/setup_e
  if %errorlevel% neq 0 exit /b %errorlevel%

  cd -
done

# Clean up
sudo rm -rf . > log/setup 2> log/setup_e