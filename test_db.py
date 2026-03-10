import asyncio
from backend.config import get_supabase
import re

def clean_title(t: str) -> str:
    t = re.sub(r'^.*?\bon linkedin\b[:\-]*', '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'^.*?\'s post\b[:\-]*', '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'#\w+', '', t).strip()
    t = re.split(r'\s*[|\-]\s*|\s+at\s+|\s+in\s+', t, maxsplit=1)[0].strip()
    t_lower = t.lower()
    if not t or 'hiring' in t_lower or 'post' in t_lower or 'like' in t_lower or 'comment' in t_lower:
        return 'Other'
    if len(t) > 25: t = t[:22] + '...'
    return t.title()

supabase = get_supabase()
res = supabase.table('candidates').select('title, tags').execute()

from collections import Counter
roles = []
for c in res.data:
    tags = c.get('tags')
    if tags and isinstance(tags, list) and len(tags) > 0:
        val = str(tags[0]).title()
        roles.append(val)
        print(f"TAG: {repr(tags[0])} -> {repr(val)}")
    else:
        title = c.get('title')
        if title:
            val = clean_title(title)
            roles.append(val)
            print(f"TITLE: {repr(title)} -> {repr(val)}")

print("COUNTS:", Counter(roles).most_common(10))
