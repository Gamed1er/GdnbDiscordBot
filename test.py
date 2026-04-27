
import json
import re


s = """```json 
{
  "area": "化學領域的科學家",
  "hint": [
    "他首次提出原子理論，改變化學。",
    "他將色盲納入科學研究。",
    "他的姓氏後來成為質量單位。"
  ],
  "ans": "道耳吞",
  "maybe_ans": [
    "約翰·道耳吞",
    "John Dalton",
    "Dalton",
    "約翰道耳吞"
  ]
}
```
"""

json_match = re.search(r'\{.*\}', s, re.DOTALL)
clean_json = json_match.group(0)
json.loads(clean_json)