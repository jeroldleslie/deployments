#!/bin/bash

../../../docker/scribengin/docker.sh cluster --clean-containers --run-containers
./LogSampleChainSmallCluster.sh  --stop --clean --build --deploy --start --profile-type=small
