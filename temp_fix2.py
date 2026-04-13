import sys
with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '"PREFIX=\"/API/V\""' in line:
        lines[i] = line.replace('"PREFIX=\"/API/V\""', '\'PREFIX=\"/API/V\"\'')
    if '"prefix=\"/api/v\""' in line:
        lines[i] = lines[i].replace('"prefix=\"/api/v\""', '\'prefix=\"/api/v\"\'')
    if '"Prefix=\"/Api/V\""' in line:
        lines[i] = lines[i].replace('"Prefix=\"/Api/V\""', '\'Prefix=\"/Api/V\"\'')

with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
