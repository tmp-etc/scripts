#!/bin/bash

ansible-playbook -i "$1," -u root configure.yaml
