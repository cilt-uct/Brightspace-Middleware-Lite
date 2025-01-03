#! /bin/bash

source base.sh
version=`cat VERSION`
echo "Building version: $version"

# checking if registry is running locally
if [ ! "$(docker ps -a -q -f name=registry)" ]; then
    docker run -d -p 5000:5000 --restart always --name registry registry:2
elif [ "$(docker ps -a -q -f status=exited -f name=registry)" ]; then
    docker container start registry
fi

status_code=$(curl -I -k -s -m 5 http://localhost:5000/ | head -n 1 | cut -d ' ' -f 2)

docker_build() {
    name=$1
    path=$2

    cp VERSION $path/VERSION

    # build it
    docker build -t $name:latest $path && docker build -t $name:$version $path

    if [ $? -eq 0 ] && [ "$status_code" == "200" ]; then

        # tag it and push
        docker tag $name:$version $local_registry/$name:$version
        docker tag $name:latest $local_registry/$name:latest

        docker push $local_registry/$name:$version
        docker push $local_registry/$name:latest
    fi
}

# Build D2L
docker_build middleware .
