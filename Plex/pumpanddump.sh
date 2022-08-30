#!/bin/bash
# Original code written by the crew at ZenDRIVE and good to share because `This is the way` https://www.youtube.com/watch?v=1iSz5cuCXdY

echo "Beginning Plex DB pump and dump"
echo "================================================"

sqplex="/opt/plexsql/Plex Media Server"

function usage {
  echo ""
  echo "Usage: pumpandump.sh plex "
  echo ""
  echo "where plex is the name of your plex docker container, plex plex2 plex3"
  exit 1
}

if [ -z "$1" ]; then
  echo "please provide the name of your plex docker container"
  usage
fi
# install JQ if not installed
if hash jq 2> /dev/null; then echo "OK, you have jq installed. We will use that."; else sudo apt install jq -y; fi
echo "================================================"

echo "Attempting to inspect your Plex Docker container"
echo "================================================"
dbp1=$(docker inspect "${1}" | jq -r ' .[].HostConfig.Binds[] | select( . | contains("/config:rw"))')
if [ -z "$dbp1" ]
then
      echo "Unable to extract config path from ${1} container."
      echo "Cannot continue, exiting."
      echo "================================================"
      exit 1
fi
dbp1=${dbp1%%:*}
dbp1=${dbp1#/}
dbp1=${dbp1%/}
dbp2="Library/Application Support/Plex Media Server/Plug-in Support/Databases"
dbpath="${dbp1}/${dbp2}"
plexdbpath="/${dbpath}"
USER=$(stat -c '%U' "$plexdbpath/com.plexapp.plugins.library.db")
GROUP=$(stat -c '%G' "$plexdbpath/com.plexapp.plugins.library.db")
plexdocker="${1}"

echo "Plex DB Path:"
echo "${plexdbpath}"
echo "Plex Docker:"
echo "${plexdocker}"
echo "================================================"
echo "stopping ${plexdocker} container"
docker stop "${plexdocker}"
echo "copying PMS binary out of ${plexdocker}"
docker cp "${plexdocker}":/usr/lib/plexmediaserver/ /opt/plexsql
cd "$plexdbpath"
echo "================================================"
echo "backing up database"
cp com.plexapp.plugins.library.db com.plexapp.plugins.library.db.original
if [ -z com.plexapp.plugins.library.db.original ]
then
      echo "Database backup failed."
      echo "Cannot continue, exiting."
      echo "================================================"
      exit 1
fi
echo "cleaning/resetting folders"
rm -rf "/${dbp1}"/Library/Application Support/Plex Media Server/Codecs/*

echo "================================================"
echo "removing pointless items from database"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DROP index 'index_title_sort_naturalsort'"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE from schema_migrations where version='20180501000000'"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE FROM statistics_bandwidth;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE FROM statistics_media;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE FROM statistics_resources;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE FROM accounts;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "DELETE FROM devices;"
echo "================================================"
echo "fixing dates on stuck files"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = originally_available_at WHERE added_at <> originally_available_at AND originally_available_at IS NOT NULL;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = DATETIME('now', '-1 days') WHERE DATETIME(added_at) > DATETIME('now');"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = DATETIME('now', '-1 days') WHERE DATETIME(originally_available_at) > DATETIME('now');"
echo "================================================"
echo "dumping and removing old database"
"${sqplex}" --sqlite com.plexapp.plugins.library.db .dump > dump.sql
rm com.plexapp.plugins.library.db
echo "================================================"
echo "making adjustments to new db"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "pragma page_size=32768; vacuum;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "pragma default_cache_size = 20000000; vacuum;"
echo "================================================"
echo "importing old data"
"${sqplex}" --sqlite com.plexapp.plugins.library.db <dump.sql
echo "================================================"
echo "optimize database and fix times"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "vacuum"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "pragma optimize"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = originally_available_at WHERE added_at <> originally_available_at AND originally_available_at IS NOT NULL;"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = DATETIME('now', '-1 days') WHERE DATETIME(added_at) > DATETIME('now');"
"${sqplex}" --sqlite com.plexapp.plugins.library.db "UPDATE metadata_items SET added_at = DATETIME('now', '-1 days') WHERE DATETIME(originally_available_at) > DATETIME('now');"
echo "================================================"
echo "reown to $USER:$GROUP"
sudo chown "$USER:$GROUP" "${plex}"/*

# Start Applications
echo "================================================"
echo "restarting plex container"
docker start "${plexdocker}"

echo "================================================"
echo "Plex DB PnD complete"
