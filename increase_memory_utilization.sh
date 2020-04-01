#!/bin/bash

do_increase=true
do_count=1
while [ $do_increase ]
do
echo "do_count is $do_count"
dd if=/dev/zero of=/dev/null bs=128M &
dd if=/dev/zero of=/dev/null bs=512M &
dd if=/dev/zero of=/dev/null bs=1024M &
if [ $do_count -eq 50  ]
then
break
fi
((do_count++))
done
