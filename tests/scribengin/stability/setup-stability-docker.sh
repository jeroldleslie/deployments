#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

$SCRIPT_DIR/../../../docker/scribengin/docker.sh cluster --clean-containers --run-containers 

