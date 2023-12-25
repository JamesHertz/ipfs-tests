# ipfs-tests
This repository was used to get the experimental results for the **Upgradable DHT design evaluation** paper (soon to be published). Here is a short description of what is in this in this repo:
- folder [*scripts*](scripts) - are the scripts used to build the binaries, generate the images and run the [experiments](#experiments)
- folder [*docker*](docker)  - there is the docker file and a script used on the image
- folder [*repos*](repos)   - it has git submodules of git repositories used to generate the binaries of IPFS with different versions of the DHT
- folder [*parser*](parser) - has a not completed parser for the logs generated on the experiment. The parser generates a set of data stores with all the data from the experiment, such as each node type and its CIDs. This allows to anyone later output whatever information its interested in a convenient way.
- file [*.env*](.env) - this one has the parameters for the experiment, such as its duration (including the 5 minutes waited by the clients before resolving), the number of nodes, the number of CIDs per node, and directories path, etc...

# Repositores
To make this experiment possible, there was a need to change the IPFS repo, along with Libp2p, the Kademilia DHT, and the Kbuckets (the routing table) datastore. Here are the links to those:
- [Secure DHT implementation](https://github.com/JamesHertz/go-libp2p-kad-dht/tree/secure-dht)
- [Normal DHT implementation](https://github.com/JamesHertz/go-libp2p-kad-dht)
<!-- - [Bare DHT implementation](https://github.com/JamesHertz/go-libp2p-bare-dht) - it has the base layer discussed in the paper (it will be updated soon to have all the changes performed) -->
- [New routing table](https://github.com/JamesHertz/go-libp2p-kbucket/tree/experments)
- [Modified IPFS](https://github.com/JamesHertz/kubo/tree/experiments) - about this one, the only things that were touched were configurations to the Routing table that were not possible to be performed outside the code and logs that were added
- [Ipfs client](https://github.com/JamesHertz/ipfs-client) - in this repo there is code for the clients that communicate with the IPFS daemon of the nodes used in the experiment, including both the experimental and bootstrap nodes. These clients enable the execution of the experiment. One of the clients interacts with the experimental nodes, requesting them to publish and resolve CIDs. The other client communicates with the bootstrap nodes to retrieve their addresses. These addresses are then combined into a file, which the previous client uses to request connections to the bootstrap nodes.

# Experiments
The scripts used for the experiment were designed to work in a setup with clusters managed by [oar](http://oar.imag.fr/docs/latest/index.html), but with minimal alterations, it can work on any cluster setup or a simple desktop. If anyone is interested in doing so, please [email me](mailto:jh.furtado@campus.fct.unl.pt), I will be pleased to you help you run my experiments.

Before running the experiment there is a need to generate the IPFS repositories and the CIDs, these values are configured by the values in the beginning [utils.sh](scripts/utils.sh) file. The following command accomplishes these:
```bash
$ ./scripts/script.sh init
```
After having done this, the binaries, the images, the docker swarm, and the network still need to be set up, it's accomplished by the following:
```bash
$ ./scripts/script.sh build --bin && ./scripts/script.sh setup --experiment
```
Finally, to run the experiment, we used the following:
```bash
$ ./scripts/script.sh start <compose-file>
```
Where \<compose-file\> is the compose file that describes the experiments. Up to this point I have prepare two experiments and the compose file for each one of them is in the directory [*config*](config).
# Acknoledgements 
....
