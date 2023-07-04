FROM ubuntu
ARG binary
ARG mode

ENV HOME=/$binary/home
ENV PATH=$PATH:$HOME
ENV MODE=$mode

# EXPERMENTS PARAMETERS:

# the number of files to generate
ENV FILE_NR=5 
# size of the file in megabytes
ENV FILE_SIZE=2
# number of time an experience is supposed to be runned
ENV EXP_TIMES=2
# the duration of each try
ENV EXP_DURATION=3
# dir where logs will be dumped
ENV SHARED_DIR=/logs

WORKDIR $HOME

COPY bin/$binary $HOME/ipfs
COPY bin/ipfs-client images/common/*.sh $HOME/

RUN apt-get update \
    && apt-get install iputils-ping iproute2 -y 
ENTRYPOINT bash start_experience.sh
