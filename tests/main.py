
import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup as bs
import json

load_dotenv()

def get_session():

    s = requests.Session()

    response = s.get("https://starexec.ccs.miami.edu/starexec/secure/index.jsp")
    jsessionid = response.cookies.get('JSESSIONID')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'j_username': os.getenv("j_username"),
        'j_password': os.getenv("j_password"),
        'cookieexists': 'false' 
    }

    response = s.post("https://starexec.ccs.miami.edu/starexec/secure/j_security_check", headers=headers, data=data)

    print(response.status_code)
    soup = bs(response.text, 'html.parser')
    print(soup.select_one("footer").select_one("a").text)
    
    return s

def get_jobs(s: requests.Session, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/jobs/pagination", data=data)
    
    return response.json()

def get_solvers(s: requests.Session, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/solvers/pagination", data=data)
    
    return response.json()

def get_benchmarks(s: requests.Session, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/benchmarks/pagination", data=data)
    
    return response.json()

def get_users(s: requests.Session, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/users/pagination", data=data)
    
    return response.json()

def get_subfolder(s: requests.Session, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/spaces/pagination", data=data)
    
    return response.json()

# def get_subspace(s: requests.Session, space_id):
#     params = {
#         'id': space_id
#     }
    
#     response = s.get("https://starexec.ccs.miami.edu/starexec/services/space/subspaces", params=params)
    
#     return response.json()

# def recurse_subspace(s: requests.Session, space_id=-1):
    
#     params = {
#         'id': space_id,
#     }
    
#     subspaces = s.get('https://starexec.ccs.miami.edu/starexec/services/space/subspaces', params=params).json()
    
#     for subspace in subspaces:
#         if space_id != -1:
#             print(subspace['data'])
#         next_subspace_id = subspace['attr']['id']
#         recurse_subspace(s, next_subspace_id)

def build_space_tree(s: requests.Session, space_id=-1):
    params = {
        'id': space_id,
    }
    
    try:
        url = 'https://starexec.ccs.miami.edu/starexec/services/space/subspaces'
        response = s.get(url, params=params)
        subspaces = response.json()
        
    except (json.JSONDecodeError, ValueError):
        return []

    for subspace in subspaces:
        current_id = subspace['attr']['id']
        subspace['children'] = build_space_tree(s, current_id)
        
    return subspaces

s = get_session()

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = s.get(
    'https://starexec.ccs.miami.edu/starexec/services/space/subspaces',
    headers=headers,
)

subspaces = response.json()
root_space_id = subspaces[0]['attr']['id']
print(f"root_space_id: {root_space_id}")

data = {
    'sEcho': '5',
    'iDisplayStart': '0',
    'iDisplayLength': '100',
    'iSortCol_0': '0',
}

data = s.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{root_space_id}/spaces/pagination", data=data).json()

for space in data['aaData']:
    soup = bs(space[0], 'html.parser')

    space_id = soup.select_one("input").get("value")
    
    print(get_jobs(s, space_id))
    print(get_solvers(s, space_id))
    print(get_benchmarks(s, space_id))
    print(get_users(s, space_id))
    print(get_subfolder(s, space_id))
    
    print("Space Tree:")
    print(build_space_tree(s, -1))
    
    # print(get_subspace(s, space_id))
