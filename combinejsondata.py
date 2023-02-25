import os
import json


folder_path = "pathtofolder"


combined_data = {}

files=[ 'italian_data.json', 'ethiopian_data.json','chinese_data.json', 'american_data.json', 'mexican_data.json', 'japanese_data.json', 'indian_data.json','french_data.json','spanish_data.json']

result = list()
for f1 in files:
    with open(f1, 'r') as infile:
        result.extend(json.load(infile))

with open('data.json', 'w') as output_file:
    json.dump(result, output_file)

