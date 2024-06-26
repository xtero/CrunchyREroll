#!/bin/bash

SCRIPT_DIR=$(dirname $(readlink -f "$0"))
VENV_PATH="$SCRIPT_DIR/.venv"

txtrst='\e[0m'    # Rest
txtblk='\e[0;30m' # Black - Regular
txtred='\e[0;31m' # Red
txtgrn='\e[0;32m' # Green
txtylw='\e[0;33m' # Yellow
txtblu='\e[0;34m' # Blue
txtpur='\e[0;35m' # Purple
txtcyn='\e[0;36m' # Cyan
txtwht='\e[0;37m' # White

msg(){
    echo -e -n "${txtrst}$@${txtrst}"
}

info(){
    echo -e -n "${txtblu}$@${txtrst}"
}

ok(){
    echo -e -n "${txtgrn}$@${txtrst}"
}

error(){
    echo -e -n "${txtred}$@${txtrst}"
}

msg "Checking autoenv\n"
if [ ! -e "$HOME/.autoenv" ]; then
    info "Installing autoenv "
    curl -L -s 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh 1>/dev/null 2>&1
    echo "AUTOENV_ENABLE_LEAVE=\"true\"" >> ~/.bashrc
    ok "Done\n"
fi

msg "Checking python virtual environment\n"
if [ ! -e "$VENV_PATH" ]; then
    info "Installing virtual environment "
    python3 -m venv "$VENV_PATH" 2>&1 1>/dev/null 
    ok "Done\n"
fi

$VENV_PATH/bin/pip install wheel==0.42.0
msg "Checking python depenencies\n"
$VENV_PATH/bin/pip install -r requirements.txt

PYTHON_VERSION=$($VENV_PATH/bin/python -V | awk '{ print $2}' | awk -F '.' '{ print $1"."$2}')
sed -i 's|id="xbmc.python" version="2.25.0"|id="xbmc.python" version="3.0.0"|' $VENV_PATH/lib/python$PYTHON_VERSION/site-packages/addondev/data/xbmc.python/addon.xml
sed -i 's|backwards-compatibility abi="2.1.0"|backwards-compatibility abi="3.0.0"|' $VENV_PATH/lib/python$PYTHON_VERSION/site-packages/addondev/data/xbmc.python/addon.xml
sed -i 's|from collections import Mapping, OrderedDict|from collections import OrderedDict\nfrom collections.abc import Mapping|' $VENV_PATH/lib/python$PYTHON_VERSION/site-packages/addondev/support.py
