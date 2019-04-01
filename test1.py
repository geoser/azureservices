import resources
import sql.sql_deployment as sd
from sql.sql_parameters import SqlParameters


res = resources.get_all_resource_groups()

res.next()

#params = SqlParameters()
#params.administrator_password = "})&B7Tq33n1f"

#p = sd.get_parameters(params)
#t = sd.get_template()

#resources.create_deployment("89aa748b-0621-4ec3-865a-ab0cde103b13", t, p)

pass