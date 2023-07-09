FROM debian
ARG binary
ARG mode

ENV HOME=/$binary/home
ENV PATH=$PATH:$HOME
ENV MODE=$mode

WORKDIR $HOME
COPY bin/$binary $HOME/ipfs
COPY bin/ipfs-client images/*.sh images/common/*.sh ./

RUN apt-get update \
    && apt-get install iproute2 -y 

ENTRYPOINT ./start_experiment.sh
