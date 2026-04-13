import sys
with open('backend/app/core/rules_database.py', 'r') as f:
    content = f.read()
content = content.replace('"PREFIX=\"/API/V\""', '\'PREFIX=\"/API/V\"\'')
content = content.replace('"prefix=\"/api/v\""', '\'prefix=\"/api/v\"\'')
content = content.replace('"Prefix=\"/Api/V\""', '\'Prefix=\"/Api/V\"\'')
content = content.replace('"allowedOrigins(\\"*\\")"', '\'allowedOrigins("*")\'')
content = content.replace('"origin: \'*\'"', '\'origin: \"*\"\'')
content = content.replace('"allow_origins=[\\"*\\"]"', '\'allow_origins=["*"]\'')
content = content.replace('"origins: \\"*\\""', '\'origins: \"*\"\'')
content = content.replace('"origin: \\"*\\""', '\'origin: \"*\"\'')
content = content.replace('"origins: \'*\'"', '\'origins: \"*\"\'')
with open('backend/app/core/rules_database.py', 'w') as f:
    f.write(content)
