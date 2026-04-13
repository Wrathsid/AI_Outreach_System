import urllib.request
import urllib.parse
import json
import time

BASE_URL = 'http://localhost:8000'

def test_endpoint(name, req):
    print(f'Testing {name}...')
    try:
        response = urllib.request.urlopen(req)
        data = response.read().decode('utf-8')
        print(f'SUCCESS: {response.getcode()}')
        try:
            print(json.dumps(json.loads(data), indent=2)[:500])
        except:
            print(data[:500])
        return json.loads(data)
    except urllib.error.HTTPError as e:
        print(f'FAILED {e.code}:\n{e.read().decode("utf-8")}')
        return None
    except Exception as e:
        print(f'ERROR: {e}')
        return None
        
print('--- E2E VERIFICATION ---')

# 1. Update Brain Context
req = urllib.request.Request(
    f'{BASE_URL}/cortex/skills',
    data=json.dumps(['Python', 'AWS', 'Backend', 'SRE']).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
test_endpoint('Cortex Skills Update', req)

# 2. Add a Candidate manually to bypass search rate-limits
req = urllib.request.Request(
    f'{BASE_URL}/candidates',
    data=json.dumps({'name': 'Jane Doe', 'title': 'VP Engineering', 'company': 'Stripe', 'email': 'jane.doe@example.com', 'linkedin_url': 'https://linkedin.com/in/janedoe123'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
res = test_endpoint('Add Test Candidate', req)
if res:
    candidate_id = res.get('id')

# 3. Get candidates
req = urllib.request.Request(f'{BASE_URL}/candidates')
res = test_endpoint('Get Candidates', req)
candidate_id = None
if res and len(res) > 0:
    candidate_id = res[0]['id']

if candidate_id:
    # 4. Generate Draft
    req = urllib.request.Request(
        f'{BASE_URL}/drafts/generate/{candidate_id}?contact_type=linkedin',
        method='POST',
        data=b'{}',
        headers={'Content-Type': 'application/json'}
    )
    test_endpoint('Generate Draft', req)

print('--- DONE ---')
