FROM ubuntu

WORKDIR /ipfs-tests

COPY bin/* /usr/bin

RUN apt-get update \
    && apt-get install iproute2 -y 

ENTRYPOINT ./start_experiment.sh