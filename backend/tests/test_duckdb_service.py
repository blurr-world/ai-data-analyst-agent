import pandas as pd
from app.services.duckdb_service import create_connection, is_name_valid


# df = pd.DataFrame({
#     "id": [1, 2, 3, 4],
#     "name": ["John", "Alex", "David", "Sarah"],
#     "salary": [30000, 50000, 60000, 40000]
# })

# con = create_connection(df=df)

# result = con.execute("""
#     SELECT *
#     FROM uploaded_data
#     WHERE salary > 40000
# """).df()

# con.close()
# print(result)

print(is_name_valid("select * from all"))