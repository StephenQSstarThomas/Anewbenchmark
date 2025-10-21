docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.49-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /run/user/$UID/docker.sock:/var/run/docker.sock \
    -v /home/shiqiu/OpenHands/shared:/shared \
    --add-host host.docker.internal:169.229.219.180 \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.49