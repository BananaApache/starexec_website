import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from bs4 import BeautifulSoup as bs
import json
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
import re

STAREXEC_URL = settings.STAREXEC_URL

# Create your views here.


def _normalize_starexec_url(url):
    url = url.strip().rstrip("/")
    if url and "://" not in url:
        url = "https://" + url
    return url


def _get_starexec_url(request):
    return request.session.get("STAREXEC_URL", STAREXEC_URL)


def get_space_xml_response(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    space_id = int(space_id)
    url = f"{starexec_url}/starexec/secure/download"

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
        print(
            f"HTTP Error: {e.response.status_code} - {e.response.reason}. XML Download failed."
        )
        return None
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}. XML Download failed.")
        return None


def get_space_download_response(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    space_id = int(space_id)
    url = f"{starexec_url}/starexec/secure/download"

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
        print(
            f"HTTP Error: {e.response.status_code} - {e.response.reason}. Download failed."
        )
        return None
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}. Download failed.")
        return None


@login_required
def download_space_file(request, space_id):
    jsessionid = request.session.get("JSESSIONID")

    if not jsessionid:
        return redirect("login")

    api_cookies = {"JSESSIONID": jsessionid}
    starexec_url = _get_starexec_url(request)

    response = get_space_download_response(api_cookies, space_id, starexec_url)

    if response is None:
        return render(
            request,
            "home.html",
            {
                "error": f"Could not initiate download for Space ID {space_id}. Please check permissions."
            },
        )

    filename = f"space_{space_id}.zip"
    content_type = response.headers.get("Content-Type", "application/zip")

    if "Content-Disposition" in response.headers:
        match = re.search(r'filename="(.*)"', response.headers["Content-Disposition"])
        if match:
            filename = match.group(1)

    django_response = StreamingHttpResponse(
        response.iter_content(chunk_size=8192), content_type=content_type
    )

    django_response["Content-Disposition"] = f'attachment; filename="{filename}"'

    content_length = response.headers.get("Content-Length")
    if content_length:
        django_response["Content-Length"] = content_length

    return django_response


@login_required
def download_space_xml_file(request, space_id):
    jsessionid = request.session.get("JSESSIONID")

    if not jsessionid:
        return redirect("login")

    api_cookies = {"JSESSIONID": jsessionid}
    starexec_url = _get_starexec_url(request)

    response = get_space_xml_response(api_cookies, space_id, starexec_url)

    if response is None:
        return render(
            request,
            "home.html",
            {
                "error": f"Could not initiate XML download for Space ID {space_id}. Please check permissions."
            },
        )

    filename = f"space_{space_id}.xml"
    content_type = response.headers.get("Content-Type", "application/xml")

    # Check for filename in Content-Disposition header
    if "Content-Disposition" in response.headers:
        match = re.search(r'filename="(.*)"', response.headers["Content-Disposition"])
        if match:
            filename = match.group(1)

    django_response = StreamingHttpResponse(
        response.iter_content(chunk_size=8192), content_type=content_type
    )

    django_response["Content-Disposition"] = f'attachment; filename="{filename}"'

    content_length = response.headers.get("Content-Length")
    if content_length:
        django_response["Content-Length"] = content_length

    return django_response


def get_jobs(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    data = {
        "sEcho": "5",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "iSortCol_0": "0",
    }
    response = requests.post(
        f"{starexec_url}/starexec/services/space/{space_id}/jobs/pagination",
        cookies=api_cookies,
        data=data,
    )
    return response.json()


def get_solvers(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    data = {
        "sEcho": "5",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "iSortCol_0": "0",
    }
    response = requests.post(
        f"{starexec_url}/starexec/services/space/{space_id}/solvers/pagination",
        cookies=api_cookies,
        data=data,
    )
    return response.json()


def get_benchmarks(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    data = {
        "sEcho": "5",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "iSortCol_0": "0",
    }
    response = requests.post(
        f"{starexec_url}/starexec/services/space/{space_id}/benchmarks/pagination",
        cookies=api_cookies,
        data=data,
    )
    return response.json()


def get_users(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    data = {
        "sEcho": "5",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "iSortCol_0": "0",
    }
    response = requests.post(
        f"{starexec_url}/starexec/services/space/{space_id}/users/pagination",
        cookies=api_cookies,
        data=data,
    )
    return response.json()


def get_subfolder(api_cookies, space_id, starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    data = {
        "sEcho": "5",
        "iDisplayStart": "0",
        "iDisplayLength": "100",
        "iSortCol_0": "0",
    }
    response = requests.post(
        f"{starexec_url}/starexec/services/space/{space_id}/spaces/pagination",
        cookies=api_cookies,
        data=data,
    )
    return response.json()


@login_required
def get_space_content(request):
    """
    Enhanced to handle specific category clicks (type: jobs, solvers, etc.)
    """
    if request.method == "POST":
        space_id = request.POST.get("space_id")
        space_name = request.POST.get("space_name")
        # CAPTURE THE REQUESTED TYPE
        requested_type = request.POST.get("type", "all")
        jsessionid = request.session.get("JSESSIONID")

        if not space_id or not jsessionid:
            return JsonResponse(
                {"error": "Missing space ID or session token. Please re-login."},
                status=400,
            )

        api_cookies = {"JSESSIONID": jsessionid}
        starexec_url = _get_starexec_url(request)

        # Initialize results dictionary
        results = {"title": f"Space : {space_name}"}

        # ONLY FETCH WHAT IS REQUESTED to optimize performance
        try:
            if requested_type == "all" or requested_type == "jobs":
                results["jobs"] = get_jobs(api_cookies, space_id, starexec_url)

            if requested_type == "all" or requested_type == "solvers":
                results["solvers"] = get_solvers(api_cookies, space_id, starexec_url)

            if requested_type == "all" or requested_type == "benchmarks":
                results["benchmarks"] = get_benchmarks(api_cookies, space_id, starexec_url)

            if requested_type == "all" or requested_type == "users":
                results["users"] = get_users(api_cookies, space_id, starexec_url)

            if requested_type == "all" or requested_type == "subfolders":
                results["subfolders"] = get_subfolder(api_cookies, space_id, starexec_url)

            # Return the requested_type so frontend knows what to render
            return JsonResponse(
                {"success": True, "content": results, "requested_type": requested_type}
            )

        except requests.exceptions.HTTPError as e:
            error_message = f"API HTTP Error: {e.response.status_code} {e.response.reason}. You might not have permission."
            return JsonResponse({"error": error_message}, status=e.response.status_code)
        except requests.exceptions.RequestException:
            error_message = "API connection error: The StarExec server is unavailable."
            return JsonResponse({"error": error_message}, status=503)
        except Exception as e:
            error_message = f"Error processing content: {str(e)}"
            return JsonResponse({"error": error_message}, status=500)

    # Fallback for non-POST requests
    return JsonResponse({"error": "Invalid request method"}, status=405)


def build_space_tree(api_cookies, space_id=-1, level=0, parent_name="", starexec_url=None):
    if starexec_url is None:
        starexec_url = STAREXEC_URL
    params = {
        "id": space_id,
    }

    try:
        response = requests.get(
            f"{starexec_url}/starexec/services/space/subspaces",
            cookies=api_cookies,
            params=params,
        )
        response.raise_for_status()
        subspaces = response.json()

    except (json.JSONDecodeError, ValueError, requests.RequestException) as e:
        print(f"Error fetching data or decoding JSON for space_id {space_id}: {e}")
        return []

    for subspace in subspaces:
        subspace["level"] = level
        subspace["is_child_of_users"] = parent_name == "Users"

        current_id = subspace["attr"]["id"]
        current_data_name = subspace.get("data", "")

        subspace["children"] = build_space_tree(
            api_cookies, current_id, level + 1, current_data_name, starexec_url
        )

    if space_id == -1 and subspaces and len(subspaces) > 0:
        first_node = subspaces[0]
        if first_node.get("attr", {}).get("id") == 1:
            return first_node.get("children", [])

    return subspaces


@login_required
def home(request):
    jsessionid = request.session.get("JSESSIONID")

    if not jsessionid:
        logout(request)
        return redirect("login")

    api_cookies = {"JSESSIONID": jsessionid}
    starexec_url = _get_starexec_url(request)

    try:
        space_tree = build_space_tree(api_cookies, starexec_url=starexec_url)

        context = {"spaces_tree": space_tree, "starexec_url": starexec_url}

        return render(request, "home.html", context)

    except requests.exceptions.HTTPError as e:
        return render(
            request,
            "home.html",
            {"error": f"API Error: {e.response.status_code} {e.response.reason}"},
        )
    except requests.exceptions.RequestException as e:
        return render(request, "home.html", {"error": f"API is unavailable: {e}"})
    except (KeyError, IndexError, TypeError) as e:
        return render(
            request, "home.html", {"error": f"Error processing API response: {e}"}
        )


def login_view(request):
    if request.method == "POST":
        try:
            starexec_url = _normalize_starexec_url(
                request.POST.get("starexec_url", "") or STAREXEC_URL
            )

            api_session = requests.Session()
            api_response = api_session.get(
                f"{starexec_url}/starexec/secure/index.jsp"
            )
            # jsessionid = api_response.cookies.get('JSESSIONID')
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            username_from_form = request.POST.get("email")
            password_from_form = request.POST.get("password")
            data = {
                "j_username": username_from_form,
                "j_password": password_from_form,
                "cookieexists": "false",
            }

            api_response = api_session.post(
                f"{starexec_url}/starexec/secure/j_security_check",
                headers=headers,
                data=data,
            )

            soup = bs(api_response.text, "html.parser")

            if soup.select_one("footer").select_one("a").text.strip() != "Login":
                jsession_cookie_value = api_session.cookies.get("JSESSIONID")
                if jsession_cookie_value:
                    request.session["JSESSIONID"] = jsession_cookie_value
                    request.session["STAREXEC_URL"] = starexec_url
                else:
                    return render(
                        request,
                        "login.html",
                        {
                            "error": "Login succeeded but failed to retrieve session.",
                            "default_starexec_url": starexec_url,
                        },
                    )

                local_user, created = User.objects.get_or_create(
                    username=username_from_form
                )
                if created:
                    local_user.set_unusable_password()
                    local_user.save()

                local_user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, local_user)
                return redirect("/home")
            else:
                return render(
                    request,
                    "login.html",
                    {
                        "error": "Invalid username or password.",
                        "default_starexec_url": starexec_url,
                    },
                )

        except Exception:
            return render(
                request,
                "login.html",
                {"error": "The login service is temporarily unavailable."},
            )

    return render(request, "login.html", {"default_starexec_url": STAREXEC_URL})


def logout_view(request):
    logout(request)
    return redirect("/home")


def _fetch_starexec_html(jsessionid, starexec_url, path):
    """
    Fetch a StarExec page and rewrite relative asset URLs to absolute.
    Returns (content, None) on success or (error_message, status_code) on failure.
    """
    try:
        resp = requests.get(
            f"{starexec_url}{path}",
            cookies={"JSESSIONID": jsessionid},
            timeout=15,
        )
        if resp.status_code != 200:
            return None, resp.status_code

        content = resp.text
        content = content.replace('src="/', f'src="{starexec_url}/')
        content = content.replace("src='/", f"src='{starexec_url}/")
        content = content.replace('href="/', f'href="{starexec_url}/')
        content = content.replace("href='/", f"href='{starexec_url}/")
        return content, None

    except Exception as e:
        return str(e), 500


# ---------------------------------------------------------
# Proxy View to fetch StarExec detail pages (used by modal)
# ---------------------------------------------------------
@login_required
def proxy_starexec_page(request):
    """
    Proxies GET requests to StarExec to bypass CORS and allow embedding in a modal.
    Rewrites relative URLs to absolute so images/CSS work.
    """
    target_path = request.GET.get("target")

    if not target_path:
        return HttpResponse("No target URL provided", status=400)

    if not target_path.startswith("/starexec/"):
        return HttpResponse("Invalid target path", status=400)

    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return HttpResponse("Unauthorized", status=401)

    starexec_url = _get_starexec_url(request)
    content, err = _fetch_starexec_html(jsessionid, starexec_url, target_path)

    if err:
        return HttpResponse(f"Proxy error: {content}", status=err)
    return HttpResponse(content)


# ---------------------------------------------------------
# Dedicated job detail page (used by Cmd/Ctrl+Click)
# ---------------------------------------------------------
@login_required
def job_detail(request, job_id):
    """
    Renders a StarExec job detail page standalone (same content as the modal,
    but as a full browser tab). Reached via Cmd/Ctrl+Click on a job link.
    """
    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return redirect("login")

    starexec_url = _get_starexec_url(request)
    path = f"/starexec/secure/details/job.jsp?id={job_id}"
    content, err = _fetch_starexec_html(jsessionid, starexec_url, path)

    if err:
        return HttpResponse(f"Error loading job {job_id}: {content}", status=err)
    return HttpResponse(content)


@login_required
def proxy_api(request):
    """
    Thin single-request proxy for StarExec JSON services (GET and POST).

    Accepts one StarExec API call per Django request so the view returns as
    quickly as StarExec responds (~1 round-trip).  The multi-step waterfall
    logic (jobspaces → children → pagination) lives in the frontend JS, which
    calls this endpoint once per step and coordinates the sequence itself.

    Security: only paths starting with /starexec/services/ are allowed.
    """
    target_path = request.GET.get("target", "")
    if not target_path.startswith("/starexec/services/"):
        return JsonResponse({"error": "Invalid target path"}, status=400)

    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    starexec_url = _get_starexec_url(request)
    url = f"{starexec_url}{target_path}"
    cookies = {"JSESSIONID": jsessionid}

    try:
        if request.method == "POST":
            # No timeout — pagination endpoints on StarExec can be slow.
            resp = requests.post(url, data=request.POST, cookies=cookies, timeout=None)
        else:
            resp = requests.get(url, cookies=cookies, timeout=10)

        resp.raise_for_status()
        return JsonResponse(resp.json(), safe=False)

    except requests.exceptions.HTTPError as e:
        return JsonResponse(
            {"error": f"StarExec returned {e.response.status_code}"},
            status=e.response.status_code,
        )
    except (ValueError, requests.exceptions.RequestException) as e:
        return JsonResponse({"error": str(e)}, status=502)


@login_required
def get_job_json(request, job_id):
    """
    Proxies StarExec's JSON details endpoint for a job to avoid CORS.
    Returns the raw JSON payload from /starexec/services/details/job/{id}.
    """
    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    starexec_url = _get_starexec_url(request)
    url = f"{starexec_url}/starexec/services/details/job/{job_id}"

    try:
        resp = requests.get(url, cookies={"JSESSIONID": jsessionid}, timeout=10)
        resp.raise_for_status()
        return JsonResponse(resp.json(), safe=False)
    except requests.exceptions.HTTPError as e:
        return JsonResponse(
            {"error": f"StarExec returned {e.response.status_code}"},
            status=e.response.status_code,
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=503)
    except ValueError:
        return JsonResponse({"error": "Invalid JSON from StarExec"}, status=502)


@login_required
def create_job(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    starexec_url = _get_starexec_url(request)
    space_id = request.POST.get("spaceId", "")
    cookies = {"JSESSIONID": jsessionid}

    # Step 1: Fetch add/job.jsp to get StarExec's own CSRF token and solver/config pairs
    csrf_token = ""
    solver_config_pairs = []
    try:
        jsp_resp = requests.get(
            f"{starexec_url}/starexec/secure/add/job.jsp",
            params={"sid": space_id},
            cookies=cookies,
        )
        soup = bs(jsp_resp.text, "html.parser")

        csrf_input = soup.find("input", {"name": "csrfToken"})
        if csrf_input:
            csrf_token = csrf_input.get("value", "")

        # Extract solver/config pairs from the form checkboxes
        solver_inputs = soup.find_all("input", {"name": "solver"})
        config_inputs = soup.find_all("input", {"name": "configs"})
        for s, c in zip(solver_inputs, config_inputs):
            s_val = s.get("value", "")
            c_val = c.get("value", "")
            if s_val and c_val:
                solver_config_pairs.append((s_val, c_val))

    except Exception as e:
        print(f"Warning: could not fetch add/job.jsp: {e}")

    # Step 2: Build the ordered list of POST pairs (preserving multiple solver/configs)
    pause_val = "yes" if request.POST.get("pause") == "true" else "no"
    pre = request.POST.get("preProcess", "").strip() or "-1"
    post = request.POST.get("postProcess", "").strip() or "-1"

    post_pairs = [
        ("sid", space_id),
        ("csrfToken", csrf_token),
        ("name", request.POST.get("name", "")),
        ("desc", request.POST.get("desc", "")),
        ("preProcess", pre),
        ("postProcess", post),
        ("queue", request.POST.get("queue", "")),
        ("wallclockTimeout", request.POST.get("wallclockTimeout", "300")),
        ("cpuTimeout", request.POST.get("cpuTimeout", "300")),
        ("maxMem", request.POST.get("maxMem", "1.0")),
        ("subscribe", "no"),
        ("traversal", request.POST.get("traversal", "depth")),
        ("pause", pause_val),
        ("seed", "0"),
        ("benchmarkingFramework", "RUNSOLVER"),
        ("resultsInterval", "0"),
        ("saveOtherOutput", "false"),
        ("suppressTimestamp", "no"),
        ("killDelay", "0"),
        ("softTimeLimit", "0"),
        ("runChoice", request.POST.get("runChoice", "keepHierarchy")),
    ]
    for solver_id, config_id in solver_config_pairs:
        post_pairs.append(("solver", solver_id))
        post_pairs.append(("configs", config_id))

    from urllib.parse import urlencode
    encoded_body = urlencode(post_pairs)

    url = f"{starexec_url}/starexec/secure/add/job"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": starexec_url,
        "Referer": f"{starexec_url}/starexec/secure/add/job.jsp?sid={space_id}",
        "Connection": "keep-alive",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            data=encoded_body,
            allow_redirects=False,
        )

        new_id = response.cookies.get("New_ID")
        status_msg = response.cookies.get("STATUS_MESSAGE_STRING")

        if response.status_code in (200, 302) and new_id:
            return JsonResponse({"success": True, "job_id": new_id})
        elif status_msg:
            return JsonResponse({"error": status_msg}, status=400)
        elif response.status_code in (200, 302):
            return JsonResponse({"success": True, "job_id": None})
        else:
            snippet = response.text if response.text else ""
            return JsonResponse(
                {"error": f"StarExec returned status {response.status_code}", "detail": snippet},
                status=400,
            )

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=503)


@login_required
def get_queues(request):
    jsessionid = request.session.get("JSESSIONID")
    if not jsessionid:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    starexec_url = _get_starexec_url(request)

    try:
        response = requests.get(
            f"{starexec_url}/starexec/services/cluster/queues",
            cookies={"JSESSIONID": jsessionid},
            timeout=10,
        )
        response.raise_for_status()
        return JsonResponse(response.json(), safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=503)
