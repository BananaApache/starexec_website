
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from bs4 import BeautifulSoup as bs
import json
from django.http import JsonResponse 


# Create your views here.


def get_jobs(api_cookies, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = requests.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/jobs/pagination", cookies=api_cookies, data=data)
    
    return response.json()


def get_solvers(api_cookies, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = requests.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/solvers/pagination", cookies=api_cookies, data=data)
    
    return response.json()


def get_benchmarks(api_cookies, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = requests.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/benchmarks/pagination", cookies=api_cookies, data=data)
    
    return response.json()


def get_users(api_cookies, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = requests.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/users/pagination", cookies=api_cookies, data=data)
    
    return response.json()


def get_subfolder(api_cookies, space_id):
    data = {
        'sEcho': '5',
        'iDisplayStart': '0',
        'iDisplayLength': '100',
        'iSortCol_0': '0',
    }
    
    response = requests.post(f"https://starexec.ccs.miami.edu/starexec/services/space/{space_id}/spaces/pagination", cookies=api_cookies, data=data)
    
    return response.json()


@login_required
def get_space_content(request):
    if request.method == 'POST':
        space_id = request.POST.get('space_id')
        space_name = request.POST.get('space_name')
        jsessionid = request.session.get('JSESSIONID')

        if not space_id or not jsessionid:
            return JsonResponse({'error': 'Missing space ID or session token. Please re-login.'}, status=400)

        api_cookies = {'JSESSIONID': jsessionid}
        
        print("Fetching content for Space ID:", space_id)
        jobs = get_jobs(api_cookies, space_id)
        print("Jobs fetched:", jobs)
        solvers = get_solvers(api_cookies, space_id)
        print("Solvers fetched:", solvers)
        benchmarks = get_benchmarks(api_cookies, space_id)
        print("Benchmarks fetched:", benchmarks)
        users = get_users(api_cookies, space_id)
        print("Users fetched:", users)
        subfolders = get_subfolder(api_cookies, space_id)
        print("Subfolders fetched:", subfolders)

        try:
            results = {
                'jobs': jobs,
                'solvers': solvers,
                'benchmarks': benchmarks,
                'users': users,
                'subfolders': subfolders,
                'title': f'Space : {space_name}'
            }
            
            return JsonResponse({'success': True, 'content': results})

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
        response = requests.get("https://starexec.ccs.miami.edu/starexec/services/space/subspaces", cookies=api_cookies, params=params)
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
        print(space_tree)
        
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
            
            api_response = api_session.get("https://starexec.ccs.miami.edu/starexec/secure/index.jsp")
            jsessionid = api_response.cookies.get('JSESSIONID')
         
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            username_from_form = request.POST.get('email')
            password_from_form = request.POST.get('password')
                        
            data = {
                'j_username': username_from_form,
                'j_password': password_from_form,
                'cookieexists': 'false'
            }
            
            api_response = api_session.post("https://starexec.ccs.miami.edu/starexec/secure/j_security_check",
                                            headers=headers,
                                            data=data
                                           )
            
            # print(api_response.status_code)
            soup = bs(api_response.text, 'html.parser')
            # print("USERNAME:", soup.select_one("footer").select_one("a").text)
            
            if soup.select_one("footer").select_one("a").text.strip() != "Login":
                jsession_cookie_value = api_session.cookies.get('JSESSIONID')

                if jsession_cookie_value:
                    request.session['JSESSIONID'] = jsession_cookie_value
                else:
                    context = {'error': 'Login succeeded but failed to retrieve session.'}
                    return render(request, 'login.html', context)

                local_user, created = User.objects.get_or_create(username=username_from_form)
                if created:
                    local_user.set_unusable_password()
                    local_user.save()
                
                local_user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, local_user)

                return redirect('/home')

            else:
                print("Login failed.")
                return render(request, 'login.html', {'error': 'Invalid username or password.'})

        except Exception as e:
            print("Exception during login:", str(e))
            context = {'error': 'The login service is temporarily unavailable.'}
            return render(request, 'login.html', context)
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    
    return redirect('/home')

