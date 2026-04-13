with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines[25] = '        "negative": frozenset(["md5", "sha1"]),\n'
with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
