#Need build-essential package to build paramiko dependency
if [ -n "$(which apt-get)" ] ; then
  sudo apt-get update
  sudo apt-get install python-dev build-essential gcc -y --fix-missing
  sudo apt-get install libffi6 libffi-dev libssl-dev -y
  #TODO need to find a different way to install npm
  sudo apt-add-repository ppa:chris-lea/node.js -y
  sudo apt-get update
  sudo apt-get install nodejs -y
  sudo apt-get install npm -y
fi

if [ -n "$(which yum)" ] ; then
  sudo yum install epel-release
  sudo yum groupinstall "Development tools" -y
  sudo yum install python-devel nodejs npm -y
fi

#Setup easy_install
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python

#Install required modules
sudo easy_install --upgrade nose==1.3.4 tabulate paramiko junit-xml click requests pip
sudo pip install pyopenssl==0.15.1 ndg-httpsclient pyasn1 kazoo elasticsearch python-digitalocean --upgrade
sudo npm install elasticdump -g -y
