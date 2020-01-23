#!/bin/bash

. .venv/bin/activate
python scripts/generate-linestring.py 5000
PAYLOAD=$(cat payload.json)
curl -F "geom=${PAYLOAD}" \
     -F "elevation_models=COMB" \
     -H "Referer: https://map.geo.admin.ch" \
     -vv http://service-alti.dev.bgdi.ch/rest/services/profile.json > result_payload.json

#curl -F "geom=@payload.json" \
#     http://localhost:9000/rest/services/profile.json
