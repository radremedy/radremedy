#!/bin/sh

flake8 . > ./standards.log

# See if we have a non-empty file
if [ -s ./standards.log ]
then
 echo "Python standards check FAILED. Check standards.log for details."
 exit 1
else
 echo "Python standards check PASSED."
fi
