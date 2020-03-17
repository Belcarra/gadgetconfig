#!/bin/bash

set -x 

for i in *.json; do gadgetconfig --add belcarra-eem-acm.json; gadgetconfig --export > belcarra-eem-acm.json; gadgetconfig --remove belcarra-eem-acm; done
