# ipfs-tests
This repository was used to get the experimental results for the **Upgradable DHT design evaluation** paper (soon to be published). Here is a short description a short description of what is in this in this repo:
- folder *scripts* - here are the scripts used to build the binaries, generate the images and run the experiments, a process that is described in: ...
- folder *images*  - there are the Dockerfile and scripts used inside the containers
- folder *repos*   - it has git submodules of git repositories (those are explained in ... ) used to generate the binaries of IPFS with different versions of the DHT.

# Repositores
To make this experiment possible, there was a need to change the IPFS repo, along with Libp2p, the Kademilia DHT, and the Kbuckets (the routing table) datastore. Here are the links to those:
- [Secure DHT implementation](https://github.com/JamesHertz/go-libp2p-kad-dht/tree/secure-dht)
- [Normal DHT implementation](https://github.com/JamesHertz/go-libp2p-kad-dht)
- [Bare DHT implementation](https://github.com/JamesHertz/go-libp2p-bare-dht) - it has the base layer discussed in the paper (it will be updated soon to have all the changes performed)
- [New routing table](https://github.com/JamesHertz/go-libp2p-kbucket/tree/experments)
- [Modified IPFS](https://github.com/JamesHertz/kubo/tree/experiments) - about this one, the only things that were touched were configurations to the Routing table that were not possible to be performed outside the code and logs that were added
- [Bootstrap IPFS Node](https://github.com/JamesHertz/kubo/tree/boot-node) - as with the latter one, the only thing that we touched were configurations in order to be sure this doesn't participate in the routing, but they do help to find peers
- [Ipfs client](https://github.com/JamesHertz/ipfs-client) -in this repo there is code for the clients that communicate with the IPFS daemon of the nodes used in the experiment, including both the experimental and bootstrap nodes. These clients enable the execution of the experiment. One of the clients interacts with the experimental nodes, requesting them to publish and resolve CIDs. The other client communicates with the bootstrap nodes to retrieve their addresses. These addresses are then combined into a file, which the previous client uses to request connections to the bootstrap nodes.
