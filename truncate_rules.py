import re
import math

with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if 'frozenset([' in lines[i] and len(lines[i]) > 300:
        # Keep the start, but chop it down to just a few reasonable keywords.
        # Format is usually '        "keywords": frozenset(["keyword1", "keyword2"...]),'
        # Let's find the property name if any
        prop_match = re.search(r'^\s*"(.*?)"\s*:\s*frozenset\(\[', lines[i])
        
        if prop_match:
            prop = prop_match.group(1)
            lines[i] = f'        "{prop}": frozenset(["sample_key_1", "sample_key_2"]),\n'
        else:
            lines[i] = '        "keywords": frozenset(["sample_key_1"]),\n'

with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
