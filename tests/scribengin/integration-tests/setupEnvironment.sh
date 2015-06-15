function usage(){
  echo "  Usage: "
  echo "       ./integrationScript.sh /path/to/NeverwinterDP/"
  echo "  Or you can set an environment variable:"
  echo "       export NEVERWINTERDP_HOME=/path/to/NeverwinterDP/"
  echo "       ./integrationScript.sh"
}

NEVERWINTER_HOME=$1

#If the command line arg isn't passed in,
#then get neverwinterdp_home from environment variable
if [ "$NEVERWINTER_HOME" = "" ] ; then
  NEVERWINTER_HOME="$NEVERWINTERDP_HOME"
fi

if [ ! -d $NEVERWINTER_HOME ] ; then
  echo "$NEVERWINTER_HOME is not a valid directory!"
  usage
  exit
elif [ "$NEVERWINTER_HOME" = "" ] ; then
  echo "NEVERWINTERDP_HOME is not set!"
  usage
  exit
fi


ROOT=$( dirname $( dirname $( dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ))))


export ANSIBLE_HOST_KEY_CHECKING=False
export NEVERWINTERDP_HOME=$NEVERWINTER_HOME
