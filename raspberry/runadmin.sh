#!/bin/sh

SERVICE="http://80.69.173.121/"

# Move to script directory.
BASE=$(dirname $0)
cd $BASE

# Detect IP and create URL.
IP=$(/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')
PORT=8080
URL="http://$IP:$PORT/ticket/"

echo "Registering URL ($URL)."
curl --data "location=admin&printer=$URL" ${SERVICE}rest/register-print-url/

echo "Stopping existing uwsgi."
pkill uwsgi

echo "Starting up uwsgi."
nohup uwsgi --plugin python,http --http :$PORT --wsgi-file print_ticket.py > /dev/null 2>&1 &

