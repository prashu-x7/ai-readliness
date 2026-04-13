import re

with open('backend/app/core/rules_database.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix literal inner quotes 
text = text.replace('"PREFIX=\\"/API/V\\""', "'PREFIX=\"/API/V\"'")
text = text.replace('"prefix=\\"/api/v\\""', "'prefix=\"/api/v\"'")
text = text.replace('"Prefix=\\"/Api/V\\""', "'Prefix=\"/Api/V\"'")

text = text.replace('"PREFIX=\"/API/V\""', "'PREFIX=\"/API/V\"'")
text = text.replace('"prefix=\"/api/v\""', "'prefix=\"/api/v\"'")
text = text.replace('"Prefix=\"/Api/V\""', "'Prefix=\"/Api/V\"'")

with open('backend/app/core/rules_database.py', 'w', encoding='utf-8') as f:
    f.write(text)
