#!/bin/sh
# Change the autogenerated user password to "debianlive"

password="2rOBlGiZ0Ggiw" # as in $(echo "efa" | mkpasswd -s)
sed -i -e 's/\(_PASSWORD=\)\(.*\)/\1\"'${password}'\"/' /lib/live/config/002-user-setup
update-initramfs -tu -kall

