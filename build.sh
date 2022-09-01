#!/bin/bash
# This script provides three options: 
#   1) upload to AWS [./build.sh "up"]
#   2) run interactively in bash [./build.sh "it"],
#   3) run unit tests [./build.sh] 

# settings
imageName=REDACTED
containerName=REDACTED
ecrURIBase=REDACTED
ecrRepoName=REDACTED
accountName=pc-admin
region=REDACTED
functionName=REDACTED

# refresh requirements
source venv/bin/activate
pip freeze > src/requirements.txt

# remove old container/image if exists
echo Re-building Docker image...
docker rm -f $containerName
docker image rm $imageName:latest


# remove old container/image if exists
echo Re-building Docker image...
docker rm -f $containerName
docker image rm $imageName:latest

# re-build docker image
docker build -t $imageName .
echo Docker build complete!

if [[ $1 = "up" ]]
then
  # re-build docs and copy over to web app directory
  echo Re-building documentation and moving to pca/ directory...
  cd docs
  make html
  cd ..
  cp -r docs/build/html ~/dev/wa/pca/public
  echo Documentation moved - push from VS Code to trigger Vercel re-build.
  
  # push to AWS ECR
  echo Pushing container to AWS Elastic Container Registry...
  aws ecr get-login-password --region $region --profile $accountName | docker login --username AWS --password-stdin $ecrURIBase
  docker tag $imageName:latest $ecrURIBase/$ecrRepoName:latest 
  docker push $ecrURIBase/$ecrRepoName
  echo Image pushed to AWS ECR! Waiting 5s before updating lambda function...

  sleep 5

  # update lambda function
  echo Updating Lambda code base...
  aws lambda update-function-code --function-name $functionName --profile $accountName --image-uri $ecrURIBase/$ecrRepoName:latest
  echo Code base updated!
else
  if [[ $1 = "it" ]]
  then
    # interactive usage
    echo Running container interactively...
    docker run --name $containerName --env-file .env --entrypoint /bin/bash -it $imageName
    # mv app/z/* .
  else
    # start container for local tests
    echo "Starting docker container for local testing"
    docker run -d --name $containerName --env-file .env $imageName

    if [[ $1 = "z" ]]
    then
      echo Running scratch file...
      docker exec $containerName python3 z.py
    else
      echo Running python unit tests...
      docker exec $containerName python -m unittest
    fi
    echo TESTING COMPLETE!
  fi
fi