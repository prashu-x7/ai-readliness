with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines[211] = '        "keywords": frozenset(["url_prefix", "api_version", "acceptheaderversioning", "namespaceversioning"]),\n'
with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
