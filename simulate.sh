#!/bin/sh

unit_location="10.152.183.79:8000"  # Get the IP address from 'juju status'

while true; do
    for i in {1..3}; do
        curl "http://$unit_location/names"
        echo
        sleep 5
    done

    curl "http://$unit_location/error"
    echo
    sleep 5
done
