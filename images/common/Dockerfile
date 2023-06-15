FROM ubuntu

ENV HOME=/ipfs-default/home
ENV PATH=$PATH:$HOME

# the number of files to generate
ENV FILE_NR=5
# size of the file in megabytes
ENV FILE_SIZE=2

WORKDIR $HOME
COPY ipfs* start_experience.sh $HOME
ENTRYPOINT bash start_experience.sh
