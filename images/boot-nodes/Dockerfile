FROM ubuntu
ARG setup 

ENV HOME=/$setup/home
ENV PATH=$HOME:$PATH
WORKDIR $HOME

COPY bin/$setup-boot ipfs
COPY bin/boot-client images/*.sh images/boot-nodes/*.sh ./

ENTRYPOINT ./start_node.sh