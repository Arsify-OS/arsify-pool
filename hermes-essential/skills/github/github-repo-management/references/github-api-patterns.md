# GitHub API Quick Patterns (curl + python3)

## List User Repos (not org)
```bash
curl -s "https://api.github.com/users/USERNAME/repos?per_page=50" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, list):
    for r in data:
        vis = 'Private' if r['private'] else 'Public'
        print(f\"{r['name']}  |  {r.get('description','-')}  |  {vis}  |  Stars: {r['stargazers_count']}  |  Updated: {r['updated_at'][:10]}\")
else:
    print(data.get('message', data))
"
```

## Check Single Repo Info
```bash
curl -s "https://api.github.com/repos/OWNER/REPO" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('Name:', d.get('name'))
print('Desc:', d.get('description'))
print('Branch:', d.get('default_branch'))
print('Size:', d.get('size'))
print('SSH:', d.get('ssh_url'))
print('Empty:', d.get('size',0)==0)
"
```

## List Org Repos
```bash
curl -s "https://api.github.com/orgs/ORG_NAME/repos?per_page=50" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, list):
    for r in data:
        print(f\"{r['name']}  |  {r.get('description','-')}  |  {'Private' if r['private'] else 'Public'}\")
else:
    print(data.get('message', data))
"
```

## Notes
- User repos endpoint: `/users/USERNAME/repos`
- Org repos endpoint: `/orgs/ORG_NAME/repos`
- If org returns "Not Found", try as user instead
- No auth needed for public repos; add `-H "Authorization: token $GITHUB_TOKEN"` for private
- Rate limit: 60 req/hour unauthenticated, 5000/hour with token
