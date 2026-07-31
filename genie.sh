#!/bin/bash
PACKAGE=nucosObs
VENV=./venv
if [ -d "$VENV" ]; then
  echo "remove virtual env first"
  sleep 2
  rm -rf "$VENV"
fi


###################################
echo "----------------------------------------------------"
{
conda create --name $PACKAGE'3_8' python=3.8 -y
source activate $PACKAGE'3_8'
} || { 
virtualenv -p $(which python3) $VENV/py3
source $VENV/py3/bin/activate 
}
pip install --upgrade pip
pip install -r requirements-dev.txt
python setup.py sdist

###################################
echo "----------------------------------------------------"
sleep 1
echo "python used: "
which python
python info.py
###################################
echo "----------------------------------------------------"
sleep 1
echo "now install the nucosObs in python 3"
python setup.py install
####################################
echo "----------------------------------------------------"
sleep 1
echo "now run test in py3"
python -m pytest
echo "test done in:"
python info.py
sleep 3

source deactivate
echo "after deactivate"
python info.py
sleep 3
###################################

