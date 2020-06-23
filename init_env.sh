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
    install_cmd='brew install'
fi

BASEDIR=`dirname $0`

if ! which python > /dev/null; then
   echo -e "Python3 not found! Install? (y/n) \c"
   read
   if [ "$REPLY" = "y" ]; then
      $install_cmd install python3
   fi
fi

pip_opt=''
pip_opt='-i http://pypi.douban.com/simple --trusted-host pypi.douban.com'

if ! which virtualenv > /dev/null; then
   echo -e "virtualenv not found! Install? (y/n) \c"
   read
   if [ "$REPLY" = "y" ]; then
      pip3 install virtualenv $pip_opt
   fi
fi

if [ ! -d "$BASEDIR/ve" ]; then
    virtualenv -p python3 $BASEDIR/ve --no-download
    echo "Virtualenv created."
fi

source $BASEDIR/ve/bin/activate
cd $BASEDIR
export PYTHONPATH=$PYTHONPATH:.

if [ ! -f "$BASEDIR/ve/updated" -o $BASEDIR/requirements.txt -nt $BASEDIR/ve/updated ]; then
    pip install -r $BASEDIR/requirements.txt $pip_opt
    touch $BASEDIR/ve/updated
    echo "Requirements installed."
fi

pip install ipython jupyterlab $pip_opt

echo "env ok"