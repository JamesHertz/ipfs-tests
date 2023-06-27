FROM ubuntu
ARG binary

ENV HOME=/$binary/home
ENV PATH=$PATH:$HOME

# the number of files to generate
ENV FILE_NR=5
# size of the file in megabytes
ENV FILE_SIZE=2

WORKDIR $HOME

COPY bin/$binary $HOME/ipfs
COPY bin/ipfs-client images/common/*.sh $HOME

ENTRYPOINT bash start_experience.sh
