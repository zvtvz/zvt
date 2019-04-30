#!/bin/bash -e

platform='unknown'
unamestr=`uname`
if [[ "$unamestr" == 'Linux' ]]; then
   platform='linux'
elif [[ "$unamestr" == 'Darwin' ]]; then
   platform='mac'
fi

install_cmd='sudo apt-get install'
if [[ "$platform" == 'mac' ]]; then
    install_cmd='sudo brew install'
fi

BASEDIR=`dirname $0`

if ! which python3 > /dev/null; then
   echo -e "Python3 not found! Install? (y/n) \c"
   read
   if [ "$REPLY" = "y" ]; then
      $install_cmd install python3
   fi
fi

if ! which virtualenv > /dev/null; then
   echo -e "virtualenv not found! Install? (y/n) \c"
   read
   if [ "$REPLY" = "y" ]; then
      $install_cmd python-virtualenv
   fi
fi

if [ ! -d "$BASEDIR/ve" ]; then
    virtualenv -p python3 $BASEDIR/ve
    echo "Virtualenv created."
fi

source $BASEDIR/ve/bin/activate
cd $BASEDIR
export PYTHONPATH=$PYTHONPATH:.

if [ ! -f "$BASEDIR/ve/updated" -o $BASEDIR/requirements.txt -nt $BASEDIR/ve/updated ]; then
    pip install -r $BASEDIR/requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
    touch $BASEDIR/ve/updated
    pip install ipython -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
    echo "Requirements installed."
fi

echo "env ok"