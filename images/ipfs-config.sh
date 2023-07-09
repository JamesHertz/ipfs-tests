function setup-ipfs-repo(){

    # gets the repo
    cp -r "$EXP_REPOS_DIR/repo-$REPO_ID" ~/.ipfs

    # to reset the it's addresses
    ipfs config profile apply default-networking 

    # remove bootstraps 
    ipfs bootstrap rm --all

    # to avoid confusion
    ipfs config Discovery.MDNS.Enabled --bool false 

    # reduce resource consuntion
    ipfs config Swarm.ConnMgr.LowWater --json 20
    ipfs config Swarm.ConnMgr.HighWater --json 50
}