FROM ubuntu

ENV HOME=/ipfs-tests/home
WORKDIR $HOME

COPY bin/* /usr/bin
COPY docker/start_experiment.sh ./

RUN apt-get update \
    && apt-get install iproute2 -y 

ENTRYPOINT ./start_experiment.sh