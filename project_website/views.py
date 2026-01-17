import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from bs4 import BeautifulSoup as bs
import json
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
import re

# Create your views here.

def get_space_xml_response(api_cookies, space_id):
    space_id = int(space_id)
    url = f"https://starexec.acorn.miami.edu/starexec/secure/download"

    parameters = {
        "type": "spaceXML",
        "id": space_id,
        "includeaattrs": True,
        "updates": True,
        "upid": -1,
    }
    
    try:
        r = requests.get(url, cookies=api_cookies, params=parameters, stream=True)
        r.raise_for_status()
        
        if r.status_code == 200:
             return r
        else:
            print(f"Unexpected status code: {r.status_code}. XML Download failed.")
            print(r.text)
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.reason}. XML Download failed.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}. XML Download failed.")
        return None

def get_space_download_response(api_cookies, space_id):
    space_id = int(space_id)
    url = f"https://starexec.acorn.miami.edu/starexec/secure/download"
    
    parameters = {
        "type": "space",
        "id": space_id,
        "includesolvers": True,
        "includebenchmarks": True,
        "hierarchy": True,
    }
    
    try:
        r = requests.get(url, cookies=api_cookies, params=parameters, stream=True)
        r.raise_for_status()
        
        if r.status_code == 200:
             return r
        else:
            print(f"Unexpected status code: {r.status_code}. Download failed.")
            print(r.text)
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.reason}. Download failed.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}. Download failed.")
        return None

@login_required
def download_space_file(request, space_id):
    jsessionid = request.session.get('JSESSIONID') 

    if not jsessionid:
        return redirect('login')
    
    api_cookies = {'JSESSIONID': jsessionid}
    
    response = get_space_download_response(api_cookies, space_id)
    
    if response is None:
        return render(request, 'home.html', {'error': f'Could not initiate download for Space ID {space_id}. Please check permissions.'})

    filename = f"space_{space_id}.zip"
    content_type = response.headers.get('Content-Type', 'application/zip')
    
    if 'Content-Disposition' in response.headers:
        match = re.search(r'filename="(.*)"', response.headers['Content-Disposition'])
        if match:
            filename = match.group(1)
        
    django_response = StreamingHttpResponse(
        response.iter_content(chunk_size=8192), 
        content_type=content_type
    )
    
    django_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    content_length = response.headers.get('Content-Length')
    if content_length:
        django_response['Content-Length'] = content_length
    
    return django_response

@login_required
def download_space_xml_file(request, space_id):
    jsessionid = request.session.get('JSESSIONID') 

    if not jsessionid:
        return redirect('login')
    
    api_cookies = {'JSESSIONID': jsessionid}
    
    response = get_space_xml_response(api_cookies, space_id)
    
    if response is None:
        return render(request, 'home.html', {'error': f'Could not initiate XML download for Space ID {space_id}. Please check permissions.'})

    filename = f"space_{space_id}.xml"
    content_type = response.headers.get('Content-Type', 'application/xml')
    
    # Check for filename in Content-Disposition header
    if 'Content-Disposition' in response.headers:
        match = re.search(r'filename="(.*)"', response.headers['Content-Disposition'])
        if match:
            filename = match.group(1)
        
    django_response = StreamingHttpResponse(
        response.iter_content(chunk_size=8192), 
        content_type=content_type
    )
    
    django_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    content_length = response.headers.get('Content-Length')
    if content_length:
        django_response['Content-Length'] = content_length
    
    return django_response

def get_jobs(api_cookies, space_id):
    data = {'sEcho': '5', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0'}
    response = requests.post(f"https://starexec.acorn.miami.edu/starexec/services/space/{space_id}/jobs/pagination", cookies=api_cookies, data=data)
    return response.json()

def get_solvers(api_cookies, space_id):
    data = {'sEcho': '5', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0'}
    response = requests.post(f"https://starexec.acorn.miami.edu/starexec/services/space/{space_id}/solvers/pagination", cookies=api_cookies, data=data)
    return response.json()

def get_benchmarks(api_cookies, space_id):
    data = {'sEcho': '5', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0'}
    response = requests.post(f"https://starexec.acorn.miami.edu/starexec/services/space/{space_id}/benchmarks/pagination", cookies=api_cookies, data=data)
    return response.json()

def get_users(api_cookies, space_id):
    data = {'sEcho': '5', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0'}
    response = requests.post(f"https://starexec.acorn.miami.edu/starexec/services/space/{space_id}/users/pagination", cookies=api_cookies, data=data)
    return response.json()

def get_subfolder(api_cookies, space_id):
    data = {'sEcho': '5', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0'}
    response = requests.post(f"https://starexec.acorn.miami.edu/starexec/services/space/{space_id}/spaces/pagination", cookies=api_cookies, data=data)
    return response.json()

@login_required
def get_space_content(request):
    """
    Enhanced to handle specific category clicks (type: jobs, solvers, etc.)
    """
    if request.method == 'POST':
        space_id = request.POST.get('space_id')
        space_name = request.POST.get('space_name')
        # CAPTURE THE REQUESTED TYPE
        requested_type = request.POST.get('type', 'all') 
        jsessionid = request.session.get('JSESSIONID')

        if not space_id or not jsessionid:
            return JsonResponse({'error': 'Missing space ID or session token. Please re-login.'}, status=400)

        api_cookies = {'JSESSIONID': jsessionid}
        
        # Initialize results dictionary
        results = {
            'title': f'Space : {space_name}'
        }

        # ONLY FETCH WHAT IS REQUESTED to optimize performance
        try:
            if requested_type == 'all' or requested_type == 'jobs':
                results['jobs'] = get_jobs(api_cookies, space_id)
            
            if requested_type == 'all' or requested_type == 'solvers':
                results['solvers'] = get_solvers(api_cookies, space_id)
                
            if requested_type == 'all' or requested_type == 'benchmarks':
                results['benchmarks'] = get_benchmarks(api_cookies, space_id)
                
            if requested_type == 'all' or requested_type == 'users':
                results['users'] = get_users(api_cookies, space_id)
                
            if requested_type == 'all' or requested_type == 'subfolders':
                results['subfolders'] = get_subfolder(api_cookies, space_id)

            # Return the requested_type so frontend knows what to render
            return JsonResponse({'success': True, 'content': results, 'requested_type': requested_type})

        except requests.exceptions.HTTPError as e:
            error_message = f'API HTTP Error: {e.response.status_code} {e.response.reason}. You might not have permission.'
            return JsonResponse({'error': error_message}, status=e.response.status_code)
        except requests.exceptions.RequestException:
            error_message = 'API connection error: The StarExec server is unavailable.'
            return JsonResponse({'error': error_message}, status=503)
        except Exception as e:
            error_message = f'Error processing content: {str(e)}'
            return JsonResponse({'error': error_message}, status=500)

    # Fallback for non-POST requests
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def build_space_tree(api_cookies, space_id=-1, level=0, parent_name=''):
    params = {
        'id': space_id,
    }
    
    try:
        response = requests.get("https://starexec.acorn.miami.edu/starexec/services/space/subspaces", cookies=api_cookies, params=params)
        response.raise_for_status()
        subspaces = response.json()
                
    except (json.JSONDecodeError, ValueError, requests.RequestException) as e:
        print(f"Error fetching data or decoding JSON for space_id {space_id}: {e}")
        return []

    for subspace in subspaces:
        subspace['level'] = level
        subspace['is_child_of_users'] = (parent_name == 'Users')
        
        current_id = subspace['attr']['id']
        current_data_name = subspace.get('data', '')
        
        subspace['children'] = build_space_tree(api_cookies, current_id, level + 1, current_data_name)
        
    if space_id == -1 and subspaces and len(subspaces) > 0:
        first_node = subspaces[0]
        if first_node.get('attr', {}).get('id') == 1:
            return first_node.get('children', [])
        
    return subspaces

@login_required
def home(request):
    jsessionid = request.session.get('JSESSIONID') 

    if not jsessionid:
        logout(request)
        return redirect('login')

    api_cookies = {'JSESSIONID': jsessionid}
    
    try:
        space_tree = build_space_tree(api_cookies)
        
        context = {
            'spaces_tree': space_tree
        }
        
        return render(request, 'home.html', context)

    except requests.exceptions.HTTPError as e:
        return render(request, 'home.html', {'error': f'API Error: {e.response.status_code} {e.response.reason}'})
    except requests.exceptions.RequestException as e:
        return render(request, 'home.html', {'error': f'API is unavailable: {e}'})
    except (KeyError, IndexError, TypeError) as e:
        return render(request, 'home.html', {'error': f'Error processing API response: {e}'})

def login_view(request):
    if request.method == "POST":
        try:
            api_session = requests.Session() 
            api_response = api_session.get("https://starexec.acorn.miami.edu/starexec/secure/index.jsp")
            jsessionid = api_response.cookies.get('JSESSIONID')
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            username_from_form = request.POST.get('email')
            password_from_form = request.POST.get('password')
            data = {'j_username': username_from_form, 'j_password': password_from_form, 'cookieexists': 'false'}
            
            api_response = api_session.post("https://starexec.acorn.miami.edu/starexec/secure/j_security_check", headers=headers, data=data)
            
            soup = bs(api_response.text, 'html.parser')
            
            if soup.select_one("footer").select_one("a").text.strip() != "Login":
                jsession_cookie_value = api_session.cookies.get('JSESSIONID')
                if jsession_cookie_value:
                    request.session['JSESSIONID'] = jsession_cookie_value
                else:
                    return render(request, 'login.html', {'error': 'Login succeeded but failed to retrieve session.'})

                local_user, created = User.objects.get_or_create(username=username_from_form)
                if created:
                    local_user.set_unusable_password()
                    local_user.save()
                
                local_user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, local_user)
                return redirect('/home')
            else:
                return render(request, 'login.html', {'error': 'Invalid username or password.'})

        except Exception as e:
            return render(request, 'login.html', {'error': 'The login service is temporarily unavailable.'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/home')

# ---------------------------------------------------------
# NEW: Proxy View to fetch StarExec details pages
# ---------------------------------------------------------
@login_required
def proxy_starexec_page(request):
    """
    Proxies GET requests to StarExec to bypass CORS and allow embedding in a modal.
    Rewrites relative URLs to absolute so images/CSS work.
    """
    target_path = request.GET.get('target')
    
    if not target_path:
        return HttpResponse("No target URL provided", status=400)
    
    # Security check: ensure we are only proxying to StarExec
    if not target_path.startswith('/starexec/'):
         return HttpResponse("Invalid target path", status=400)

    jsessionid = request.session.get('JSESSIONID')
    if not jsessionid:
        return HttpResponse("Unauthorized", status=401)
        
    url = f"https://starexec.acorn.miami.edu{target_path}"
    
    try:
        # Fetch the page using the user's session
        resp = requests.get(url, cookies={'JSESSIONID': jsessionid}, timeout=15)
        
        if resp.status_code != 200:
            return HttpResponse(f"Error fetching page: {resp.status_code}", status=resp.status_code)
            
        content = resp.text
        
        # --- HTML Rewriting for Assets ---
        # StarExec uses relative paths for images, css, js. We need to point them to the absolute URL.
        base_url = "https://starexec.acorn.miami.edu"
        
        # Rewrite src="/..." -> src="https://starexec.../..."
        content = content.replace('src="/', f'src="{base_url}/')
        content = content.replace("src='/", f"src='{base_url}/")
        
        # Rewrite href="/..." -> href="https://starexec.../..." (for CSS links)
        content = content.replace('href="/', f'href="{base_url}/')
        content = content.replace("href='/", f"href='{base_url}/")
        
        # Return the modified HTML
        return HttpResponse(content)
        
    except Exception as e:
        return HttpResponse(f"Proxy error: {str(e)}", status=500)