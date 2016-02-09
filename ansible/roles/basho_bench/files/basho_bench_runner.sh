#!/usr/bin/env bash

##def

fst=$1
scd=$2

file_path='etc'
file_temp='http_fix_1min.conf.template'

##fun

function check_args {
  re='^[0-9]+$'
  if ! [[ $fst =~ $re ]] || ! [[ $scd =~ $re ]] ; then
    echo "error: Not a number" >&2; exit 1
  fi
  #TODO add all the error cases here $1 > $2 etc
}

##ops

check_args

for i in $(seq $1 1000 $2); do
  sed "s-_FIX_-${i}-" "$file_path/$file_temp" > "$file_path/$file_temp.${i}"
done

