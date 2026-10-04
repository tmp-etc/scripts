#!/bin/bash

rm -f jason.json
kismetdb_dump_devices --in $1 --out jason.json -s
