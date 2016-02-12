#!/bin/sh

function print_usage() { 
  echo "Usage:"
  echo "    --local-aws-pem   Local aws pem file path which need be copied to remote hosting machine, ex: --aws-pem-file=/home/download/test.pem"
  echo "    --host-ip         Host machines public IP (usually it may be neverwinterdp monitoring machine), ex: --user=neverwinterdp, default=neverwinterdp"
  echo "    --user            Host machines user, ex: --user=neverwinterdp, default=neverwinterdp"
  echo "    --key-path        Path to private key to communicate with host machine, ex: --key-path=~/.ssh/id_rsa, default=~/.ssh/id_rsa"
}

function validate() {
  OPT_NAME=$1
  VALUE=$2
  if [ -z "$VALUE" -a "$VALUE" != " " ]; then
    echo "ERROR: $OPT_NAME is mandatory"
    print_usage
    exit 1
  fi
}

function get_opt() {
  OPT_NAME=$1
  DEFAULT_VALUE=$2
  shift
  
  #Par the parameters
  for i in "$@"; do
    index=$(($index+1))
    if [[ $i == $OPT_NAME* ]] ; then
      value="${i#*=}"
      echo "$value"
      return
    fi
  done
  echo $DEFAULT_VALUE
}

LOCAL_AWS_PEM=$(get_opt --local-aws-pem ' ' $@)
USER=$(get_opt --user 'neverwinterdp' $@)
HOST_IP=$(get_opt --host-ip 'monitoring-1' $@)
KEY_PATH=$(get_opt --key-path '~/.ssh/id_rsa' $@)

validate --local-aws-pem "$LOCAL_AWS_PEM"
validate --host-ip "$LOCAL_AWS_PEM"
validate --user "$USER"
validate --key-path "$KEY_PATH"

echo "1. Removing old ~/aws.pem..."
ssh $USER@$HOST_IP "rm ~/aws.pem"

echo "2. Copying $LOCAL_AWS_PEM to hosts ~/aws.pem..."
scp -p $LOCAL_AWS_PEM $USER@$HOST_IP:~/aws.pem

echo "3. Updating ~/.ssh/config..."
printf '%s\n%s\n %s\n %s\n %s\n %s\n' 'StrictHostKeyChecking no' 'Host *us-west-2.compute.amazonaws.com' 'User centos' 'IdentityFile ~/aws.pem' 'RequestTTY auto' 'StrictHostKeyChecking no' | ssh $USER@$HOST_IP "cat > ~/.ssh/config"
