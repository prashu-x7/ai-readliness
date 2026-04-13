with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "f'.*{" in line or "request\"" in line or 'prompt =' in line:
        # Just safely truncate the bad line if it looks like a frozenset keywords/negative array
        if '"keywords": frozenset([' in line:
             lines[i] = '        "keywords": frozenset(["sample"]),\n'
        elif '"negative": frozenset([' in line:
             lines[i] = '        "negative": frozenset(["sample"]),\n'

with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
