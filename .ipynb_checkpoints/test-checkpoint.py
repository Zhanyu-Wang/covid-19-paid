import pandas_gbq

# TODO: Set project_id to your Google Cloud Platform project ID.
project_id = "eminent-hall-293522"

sql = """
SELECT country_name, alpha_2_code
FROM `bigquery-public-data.utility_us.country_code_iso`
WHERE alpha_2_code LIKE 'A%'
"""
df = pandas_gbq.read_gbq(sql, project_id=project_id)