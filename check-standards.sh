#!/bin/sh

flake8 . > ./standards.log

# See if we have a non-empty file
if [ -s ./standards.log ]
then
 echo "Code standards check FAILED. Check standards.log for details."
else
 echo "Code standards check PASSED."
fi
