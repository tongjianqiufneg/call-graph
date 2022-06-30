from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import requests
import json

ms_identity_web = settings.MS_IDENTITY_WEB


def index(request):
    return render(request, "auth/status.html")


@ms_identity_web.login_required
def token_details(request):
    return render(request, 'auth/token.html')


@ms_identity_web.login_required
def call_ms_graph(request):
    ms_identity_web.acquire_token_silently()
    graph = 'https://graph.microsoft.com/v1.0/users'
    authZ = f'Bearer {ms_identity_web.id_data._access_token}'
    results = requests.get(graph, headers={'Authorization': authZ}).json()
    print("=====>", results)
    # trim the results down to 5 and format them.
    if 'value' in results:
        results['num_results'] = len(results['value'])
        results['value'] = results['value'][:5]
    else:
        results['value'] = [{'displayName': 'call-graph-error', 'id': 'call-graph-error'}]
    return render(request, 'auth/call-graph.html', context=dict(results=results))


# 自定义页面
def base(request):
    return render(request, "base.html")


# 获取个人信息
@ms_identity_web.login_required
def call_ms_graph_me(request):
    ms_identity_web.acquire_token_silently()
    url_me = 'https://graph.microsoft.com/v1.0/me'
    authZ = f'Bearer {ms_identity_web.id_data._access_token}'
    resp_me = requests.get(url_me, headers={'Authorization': authZ}).json()
    url_manager = 'https://graph.microsoft.com/v1.0/me/manager'
    resp_manager = requests.get(url_manager, headers={'Authorization': authZ}).json()
    manager = resp_manager.get("mail")
    return render(request, 'auth/call-graph_me.html', {"results": resp_me, "manager": manager})


# 查询邮箱账号状态或职位
@ms_identity_web.login_required
def emails_query(request):
    if request.method == "GET":
        return render(request, "emails_query.html")
    else:
        emails = request.POST.get("emails")
        user_keyword = request.POST.get("user_keyword")
        print(emails, user_keyword)
        emails = emails.replace("\r", "")
        emails = emails.split("\n")
        import requests

        ms_identity_web.acquire_token_silently()
        # 获取接入token
        authZ = f'Bearer {ms_identity_web.id_data._access_token}'
        # print("-------->", authZ)
        # 构造请求头
        headers = {'Authorization': authZ}

        payload = {}
        users = []
        # 判断查询的是用户状态还是职位
        if user_keyword == "accountEnabled":
            for email in emails:
                user = {}
                url = "https://graph.microsoft.com/v1.0/users/{}?$select={}".format(email, user_keyword)
                response = requests.request("GET", url, headers=headers, data=payload)
                r = response.json()
                user['UPN'] = email
                user['accountEnabled'] = r.get(user_keyword)
                users.append(user)
            return render(request, "emails_status.html", {"users": users})
        else:
            for email in emails:
                user = {}
                url = "https://graph.microsoft.com/v1.0/users/{}?$select={}".format(email, user_keyword)
                response = requests.request("GET", url, headers=headers, data=payload)
                r = response.json()
                user['UPN'] = email
                user['jobTitle'] = r.get(user_keyword)
                users.append(user)
        return render(request, "emails_jobTitle.html", {"users": users})
    return HttpResponse("Server系统内部错误")


def emails_status(request):
    pass


@ms_identity_web.login_required
def emails_disabled(request):
    if request.method == "GET":
        return render(request, "emails_disabled_query.html")
    else:
        emails = request.POST.get("emails")
        # 预留关键字选项
        # user_keyword = request.POST.get("user_keyword")
        emails = emails.replace("\r", "")
        emails = emails.split("\n")
        ms_identity_web.acquire_token_silently()
        # 获取接入token
        authZ = f'Bearer {ms_identity_web.id_data._access_token}'
        # print("-------->", authZ)
        # 构造请求头
        headers = {'Authorization': authZ}
        # 请求参数json字符串
        payload = json.dumps({
            "accountEnabled": "false"  # 禁用邮箱账号
            # "accountEnabled": "true" # 启用邮箱账号
        })
        # 请求头
        headers = {
            'Authorization': authZ,
            'Content-Type': 'application/json'
        }
        # 遍历邮箱列表
        users = []
        for email in emails:
            user = {}
            # print('========>',email)
            url = "https://graph.microsoft.com/v1.0/users/{}".format(email)
            response = requests.request("PATCH", url, headers=headers, data=payload)
            # print(response.text)
            # print('----->', response.text, response.status_code)
            if response.status_code == 204:
                user['UPN']=email
                user['status']='成功'
                users.append(user)
                print('----->', response.text, response.status_code)
            else:
                error_code = response.json().get("error").get("code")
                user['UPN']=email
                user['status']=error_code
                users.append(user)
    return render(request,"emails_disabled_resp.html",{"users":users})
