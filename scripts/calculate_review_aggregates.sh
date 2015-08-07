#!/bin/sh

mysql --host=$RAD_DB_HOSTNAME \ 
	--user=$RAD_DB_USERNAME \
	--password=$RAD_DB_PASSWORD \
	--database=$RAD_DB_NAME < ./calculate_review_aggregates.sql
