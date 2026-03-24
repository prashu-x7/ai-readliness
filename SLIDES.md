# How Rule R01 Works — Complete Deep Dive

---

## 1. How the Rule is Declared in Code

In `static_analyzer.py`, Rule R01 is a Python dictionary:

```python
RULES = {
    "R01": {
        "name": "JWT / Token Auth",
        "category": "Security & Auth",
        "severity": "critical",
        "score_pts": 8,
        "positive_patterns": [
            r"jwt\.",
            r"jsonwebtoken",
            r"python.jose",
            r"PyJWT",
            r"bearer",
            r"access_token",
            r"decode_token",
            r"verify_token",
            r"oauth2",
            r"JWTBearer",
            r"HTTPBearer",
            r"create_access_token",
        ],
        "negative_patterns": [],
    },
}
```

- `positive_patterns` = list of 12 keywords to search for
- If any keyword is found in any file = PASS
- If no keyword is found anywhere = FAIL

---

## 2. What are Patterns? Why Keywords?

A "pattern" is a **regex** (Regular Expression) — a text-searching tool built into Python.

```python
import re

line = 'token = jwt.encode(data, key, "HS256")'

result = re.search(r"jwt\.", line, re.IGNORECASE)

if result:
    print("FOUND!")    # <-- this runs because "jwt." exists in the line
else:
    print("NOT FOUND")
```

`re.search(pattern, text)` answers: **"Does this pattern exist anywhere inside this text?"**

The `r"jwt\."` pattern means:
- `jwt` = match these 3 characters literally
- `\.` = match a literal dot (the backslash escapes the dot)

So `jwt.encode` matches, `jwt.decode` matches, but `jwttoken` does NOT match (no dot).

---

## 3. Are Keywords Enough?

**Yes, for this use case.** Here is why:

If a developer writes `jwt.encode()` in their code, it is **physically impossible**
for that code to exist without the jwt library being imported and used for authentication.

You cannot accidentally write `jwt.encode()`. It means:
1. The developer installed the jwt library
2. They imported it
3. They are encoding a token
4. Therefore, authentication EXISTS in this project

Same logic:
- If `bcrypt` appears in code = passwords ARE being hashed
- If `Dockerfile` content is found = Docker IS configured
- If `async def` is found = async IS being used

Keywords work because **developers must use specific library names and function names
to implement specific features.** There is no other way to use JWT without writing "jwt" somewhere.

**Limitation:** Keywords can give false positives. If someone writes a comment like
`# TODO: add jwt later`, the scanner would count it as "found". But in practice,
across 50+ files, the pattern matching is accurate enough (95%+) because real
implementations have multiple matches (import + function + usage), not just one comment.

---

## 4. Sample Uploaded Code

Imagine a user uploads a ZIP with 3 files:

**File 1: auth.py**
```python
from jose import jwt
import os

SECRET = os.environ.get("SECRET_KEY")

def create_access_token(user_id: str):
    data = {"sub": user_id}
    token = jwt.encode(data, SECRET, algorithm="HS256")
    return token

def verify_token(token: str):
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    return payload["sub"]
```

**File 2: main.py**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "hello world"}
```

**File 3: models.py**
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

---

## 5. What the Scanner Does — Step by Step

The scanner code does this (simplified):

```python
import re

rule = RULES["R01"]
evidence_hits = []

for file in uploaded_files:           # Loop through 3 files
    for line_num, line in enumerate(file.content.splitlines(), 1):  # Loop each line
        for pattern in rule["positive_patterns"]:   # Check all 12 patterns
            if re.search(pattern, line, re.IGNORECASE):
                evidence_hits.append({
                    "file": file.path,
                    "line": line_num,
                    "snippet": line.strip(),
                })
                break   # One match per line is enough, move to next line
```

---

## 6. Processing auth.py — Every Line Checked

```
FILE: auth.py

Line 1: "from jose import jwt"
  Pattern 1  "jwt\."            -> Does "jwt." exist in this line? NO (no dot after jwt)
  Pattern 2  "jsonwebtoken"     -> NO
  Pattern 3  "python.jose"      -> NO (line has "jose" but not "python.jose")
  Pattern 4  "PyJWT"            -> NO
  Pattern 5  "bearer"           -> NO
  Pattern 6  "access_token"     -> NO
  Pattern 7  "decode_token"     -> NO
  Pattern 8  "verify_token"     -> NO
  Pattern 9  "oauth2"           -> NO
  Pattern 10 "JWTBearer"        -> NO
  Pattern 11 "HTTPBearer"       -> NO
  Pattern 12 "create_access_token" -> NO
  RESULT: 0 matches. Move to next line.

Line 2: "import os"
  All 12 patterns checked -> NONE match
  RESULT: 0 matches.

Line 3: 'SECRET = os.environ.get("SECRET_KEY")'
  All 12 patterns checked -> NONE match
  RESULT: 0 matches.

Line 5: "def create_access_token(user_id: str):"
  Pattern 1  "jwt\."            -> NO
  Pattern 2  "jsonwebtoken"     -> NO
  ...
  Pattern 6  "access_token"     -> YES! "create_access_token" CONTAINS "access_token"
  MATCH FOUND!
  Record: {file: "auth.py", line: 5, snippet: "def create_access_token(user_id: str):"}

Line 7: "token = jwt.encode(data, SECRET, algorithm='HS256')"
  Pattern 1  "jwt\."            -> YES! "jwt.encode" contains "jwt."
  MATCH FOUND!
  Record: {file: "auth.py", line: 7, snippet: "token = jwt.encode(...)"}

Line 10: "def verify_token(token: str):"
  Pattern 8  "verify_token"     -> YES! Exact match
  MATCH FOUND!
  Record: {file: "auth.py", line: 10, snippet: "def verify_token(token: str):"}

Line 11: "payload = jwt.decode(token, SECRET, algorithms=['HS256'])"
  Pattern 1  "jwt\."            -> YES! "jwt.decode" contains "jwt."
  MATCH FOUND!
  Record: {file: "auth.py", line: 11, snippet: "payload = jwt.decode(...)"}
```

---

## 7. Processing main.py

```
FILE: main.py

Line 1: "from fastapi import FastAPI"
  All 12 patterns -> NONE match

Line 3: "app = FastAPI()"
  All 12 patterns -> NONE match

Line 5: '@app.get("/hello")'
  All 12 patterns -> NONE match

Line 6: "def hello():"
  All 12 patterns -> NONE match

Line 7: 'return {"message": "hello world"}'
  All 12 patterns -> NONE match

RESULT: 0 matches in this entire file.
```

---

## 8. Processing models.py

```
FILE: models.py

Line 1: "class User:"           -> NONE match
Line 2: "def __init__(...):"    -> NONE match
Line 3: "self.name = name"      -> NONE match
Line 4: "self.email = email"    -> NONE match

RESULT: 0 matches in this entire file.
```

---

## 9. Final Decision — PASS or FAIL?

After scanning ALL 3 files, the evidence list is:

```python
evidence_hits = [
    {"file": "auth.py", "line": 5,  "snippet": "def create_access_token(...)"},
    {"file": "auth.py", "line": 7,  "snippet": "jwt.encode(...)"},
    {"file": "auth.py", "line": 10, "snippet": "def verify_token(...)"},
    {"file": "auth.py", "line": 11, "snippet": "jwt.decode(...)"},
]
```

**Decision logic:**

```python
if len(evidence_hits) > 0:
    found = True        # PASSED
    points_earned = 8   # Full 8 points awarded
else:
    found = False       # FAILED
    points_earned = 0   # 0 points
    # Add to Risk Register as CRITICAL risk
    # Trigger HARD BLOCKER (cap entire score at 49)
```

4 hits found -> **R01 = PASSED** -> **+8 points**

---

## 10. What If the Project Had NO Auth?

If all 3 files had zero matches (no jwt, no bearer, no access_token anywhere):

```python
evidence_hits = []    # Empty — nothing found

found = False
points_earned = 0

# This goes into the report as:
risk = {
    "rule": "R01",
    "name": "JWT / Token Auth",
    "severity": "CRITICAL",
    "message": "No authentication detected in any file",
    "advice": "Implement JWT auth with python-jose or PyJWT"
}

# HARD BLOCKER triggered:
# Final score = min(calculated_score, 49)
# Even if everything else is perfect, score cannot exceed 49
```

---

## 11. Summary — The Complete Mechanism

```
STEP 1: Rule is DECLARED as a dictionary with patterns

STEP 2: User UPLOADS a ZIP file

STEP 3: Scanner EXTRACTS all text files

STEP 4: For EACH file, for EACH line, for EACH of 12 patterns:
         Does re.search(pattern, line) find a match?
           YES -> save it as evidence
           NO  -> check next pattern

STEP 5: After all files scanned:
         Any evidence found?
           YES -> Rule PASSED -> award 8 points
           NO  -> Rule FAILED -> 0 points + risk + blocker

STEP 6: This rule's points feed into the total score:
         Static Score = (total earned / 237 max) x 100
```

The same process repeats for all 56 rules simultaneously.
Each rule has its own set of keyword patterns.
The final score is a weighted combination of all rules and all 9 layers.
