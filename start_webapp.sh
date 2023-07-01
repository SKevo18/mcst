#/usr/bin/bash
cd "$(dirname "$0")"

gunicorn -w 4 'mcst.web.app:WEB' -b unix:./webapp.sock
