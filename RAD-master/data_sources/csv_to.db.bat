ddlgenerator --force-key --drops --inserts --text postgresql provider.csv | psql rad
ddlgenerator --force-key --drops --inserts --text postgresql tgap.csv | psql rad
ddlgenerator --force-key --drops --inserts --text postgresql brown_resources.csv | psql rad

cat normalize_surgeons.sql | psql rad
cat build_master.sql | psql rad

wget -O ~/Dropbox/RAD/rad_resource.csv localhost:8080/resource/:csv
wget -O ~/Dropbox/RAD/rad_provider_procedure.csv localhost:8080/provider_procedure/:csv
wget -O ~/Dropbox/RAD/rad_procedure.csv localhost:8080/procedure/:csv
wget -O ~/Dropbox/RAD/rad_tag.csv localhost:8080/tag/:csv
wget -O ~/Dropbox/RAD/rad_tag_resource.csv localhost:8080/tag_resource/:csv

