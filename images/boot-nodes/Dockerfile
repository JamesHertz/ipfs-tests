FROM debian

ARG setup 

ENV HOME=/$setup/home
ENV PATH=$HOME:$PATH
WORKDIR $HOME

COPY bin/$setup-boot ipfs
COPY bin/boot-client images/boot-nodes/start_node.sh ./

ENTRYPOINT ./start_node.sh