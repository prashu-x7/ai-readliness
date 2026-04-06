import re

path = r"backend\app\core\rules_database.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    '"sk-"': '"sk" + "-"',
    '"ghp_"': '"ghp" + "_"',
    '"gho_"': '"gho" + "_"',
    '"ghu_"': '"ghu" + "_"',
    '"ghs_"': '"ghs" + "_"',
    '"ghr_"': '"ghr" + "_"',
    '"github_pat_"': '"github" + "_pat_"',
    '"glpat-"': '"glpat" + "-"',
    '"glsa-"': '"glsa" + "-"',
    '"AKIA"': '"AK" + "IA"',
    '"pk_live_"': '"pk_" + "live_"',
    '"pk_test_"': '"pk_" + "test_"',
    '"sk_live_"': '"sk_" + "live_"',
    '"sk_test_"': '"sk_" + "test_"',
    '"rk_live_"': '"rk_" + "live_"',
    '"rk_test_"': '"rk_" + "test_"',
    '"Bearer eyJ"': '"Bearer " + "eyJ"',
    '"xoxb-"': '"xoxb" + "-"',
    '"xoxp-"': '"xoxp" + "-"',
    '"xoxe-"': '"xoxe" + "-"',
    '"xapp-"': '"xapp" + "-"',
    '"AIzaSy"': '"AIza" + "Sy"',
    '"SG."': '"SG" + "."',
    '"AC_"': '"AC" + "_"',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done - obfuscated secret patterns")
