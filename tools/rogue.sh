#!/bin/bash

rm -f /tmp/rpmdb /tmp/rpmdb.tmp /tmp/rogue /tmp/rogue.tmp
rpm -qal > /tmp/rpmdb
cat /tmp/rpmdb | while read line ; do realpath "$line" >> /tmp/rpmdb.tmp 2> /dev/null; done
cat /tmp/rpmdb >> /tmp/rpmdb.tmp && sort -u /tmp/rpmdb.tmp > /tmp/rpmdb
find / ! -type d ! -path '/dev/*' ! -path '/proc/*' !  -path '/run/*' ! -path '/selinux/*' ! -path '/srv/*' ! -path '/sys/*' ! -path '/tmp/*' ! -path '/var/*' ! -path '/home/*' ! -path '/usr/share/mime/*' | grep -vxFf /tmp/rpmdb | sort > /tmp/rogue.tmp
rm -f /tmp/rogue
cat /tmp/rogue.tmp | while read line; do rpm -qf "$line" | sed -n '/is not owned by any package/s/file \(.*\) is not owned by any package/\1/p' >> /tmp/rogue; done
rm -f /tmp/rpmdb /tmp/rpmdb.tmp /tmp/rogue.tmp
