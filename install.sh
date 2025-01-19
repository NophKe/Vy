#!/bin/sh
PY_SITE_PATH=`python -c "import site; print(site.USER_SITE)"`
mv $PWD $PY_SITE_PATH/vy
chmod +x ./executables/*
cp $PWD/executables/* ~/.local/bin/

