from howardbrown import data
from ddlgenerator.ddlgenerator import Table

tbl = Table(data(), force_pk=True, varying_length_text=True)
print(tbl.sql(inserts=True,drops=True,dialect='postgresql').encode('utf8'))
