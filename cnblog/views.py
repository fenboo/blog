import json

from django.contrib import auth
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from cnblog.form import UserForm
from cnblog.models import Article, UserInfo, Article2Tag, Category, Tag
from bs4 import BeautifulSoup

from django.shortcuts import render,HttpResponse,redirect
from utils.code import check_code

def code(request):
    """
    生成图片验证码
    :param request:
    :return:
    """
    img,random_code = check_code()
    request.session['random_code'] = random_code
    from io import BytesIO
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

def index(request):
    article_list = Article.objects.all()
    return render(request, "index.html", locals())


def login(request):
    if request.method == "GET":
        return render(request ,"login.html")
    user = request.POST.get("user")
    pwd = request.POST.get("pwd")
    code = request.POST.get("code")
    if code.upper() != request.session['random_code'].upper():
        return render(request,"login.html",{"msg":"验证码输入有误！"})
    user = auth.authenticate(username=user, password=pwd)
    if user:
        auth.login(request, user)
        return redirect('/index/')
    return render(request, "login.html",{"msg":"验证码输入有误！"})

def logout(request):
    auth.logout(request)

    return redirect('/index/')


def homesite(request, username, **kwargs):
    """
    查询
    :param request:
    :param username:
    :return:
    """

    # print("kwargs", kwargs)
    # 查询当前站点的用户对象
    user = UserInfo.objects.filter(username=username).first()
    if not user:
        return render(request, "not_found.html")
    # 查询当前站点对象
    blog = user.blog
    print("aaa", blog)
    print("bbb", user)

    # 查询当前用户发布的所有文章
    if not kwargs:
        article_list = Article.objects.filter(user__username=username)
        # article_list1=UserInfo.objects.filter(username=username).values_list('article__title')
        # print("aaaa",article_list1)
        # print("aa11",article_list)
    else:
        condition = kwargs.get("condition")
        params = kwargs.get("params")
        # print(condition)
        if condition == "category":
            article_list = Article.objects.filter(user__username=username).filter(category__title=params)
            # print(article_list)
        elif condition == "tag":
            article_list = Article.objects.filter(user__username=username).filter(tags__title=params)
        else:
            year, month = params.split("/")
            article_list = Article.objects.filter(user__username=username).filter(create_time__year=year,
                                                                                  create_time__month=month)

    if not article_list:
        return render(request, "not_found.html")
    # 查询当前用户发布的所有文章
    # article_list = Article.objects.filter(user__username=username)
    # 查询当前站点每一个分类的名称以及对应的文章数
    # cate_list = Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list('title', 'c')
    # cate_list = Category.objects.filter(title=blog)
    # print(cate_list)
    # 查询当前站点每一个标签的名称以及对应的文章数
    # tag_list = Tag.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    # print(tag_list)
    # 日期归档
    # date_list = Article.objects.filter(user=user).extra(select={"y_m_date":"strftime('%%Y/%%m',create_time)"}).values("y_m_date").annotate(c=Count("title")).values_list("y_m_date","c")

    return render(request, "homesite.html", locals())


def article_detail(request, username, article_id):
    user = UserInfo.objects.filter(username=username).first()
    # 查询当前站点对象
    blog = user.blog

    article_obj = Article.objects.filter(pk=article_id).first()
    # print(article_obj)
    comment_list = Comment.objects.filter(article_id=article_id)
    print()
    return render(request, "article_detail.html", locals())


def register(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = request.POST.get('name')
            pwd = request.POST.get('pwd')
            user_list = UserInfo.objects.all().values('username')
            for name in user_list:
                if user == name['username']:
                    i_error = "您的用户名重复"
                    return render(request, 'register.html', locals())
            else:
                UserInfo.objects.create_user(username=user, password=pwd)
            return render(request, 'login.html')
        else:
            g_error = form.errors.get("__all__")
            if g_error:
                g_error = g_error[0]
            return render(request, "register.html", locals())
    else:
        form = UserForm()
    return render(request, "register.html", locals())


from cnblog.models import ArticleUpDown, Comment


def digg(request):
    is_up = json.loads(request.POST.get("is_up"))
    article_id = request.POST.get("article_id")
    user_id = request.user.pk
    response = {'state': True, "msg": None}
    obj = ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()
    if obj:
        response["state"] = False
        response["handled"] = obj.is_up
    else:
        with transaction.atomic():
            new_obj = ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)
            if is_up:
                Article.objects.filter(pk=article_id).update(up_count=F("up_count") + 1)
            else:
                Article.objects.filter(pk=article_id).update(down_count=F("down_count") + 1)

    return JsonResponse(response)


def comment(request):
    # 获取数据
    user_id = request.user.pk
    article_id = request.POST.get("article_id")
    content = request.POST.get("content")
    pid = request.POST.get("pid")
    # 生成评论对象
    with transaction.atomic():
        comment = Comment.objects.create(user_id=user_id, article_id=article_id, content=content, parent_comment_id=pid)
        Article.objects.filter(pk=article_id).update(comment_count=F("comment_count") + 1)

    response = {"state": True}
    response["timer"] = comment.create_time.strftime("%Y-%m-%d %X")
    response["content"] = comment.content
    response["user"] = request.user.username

    return JsonResponse(response)


def backend(request):
    user = request.user
    article_list = Article.objects.filter(user=user)
    return render(request, "backend/backend.html", locals())


def add_article(request):
    if request.method == "POST":

        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        cate_pk = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")


        soup = BeautifulSoup(content, "html.parser")
        # 文章过滤：
        for tag in soup.find_all():
            # print(tag.name)
            if tag.name in ["script", ]:
                tag.decompose()

        # 切片文章文本
        desc = soup.text[0:150]

        article_obj = Article.objects.create(title=title, content=str(soup), user=user, category_id=cate_pk, desc=desc)

        for tag_pk in tags_pk_list:
            Article2Tag.objects.create(article_id=article_obj.pk, tag_id=tag_pk)

        return redirect("/backend/")


    else:

        blog = request.user.blog
        cate_list = Category.objects.filter(blog=blog)
        tags = Tag.objects.filter(blog=blog)
        return render(request, "backend/add_article.html", locals())


from blog import settings
import os


def upload(request):
    print(request.FILES)
    obj = request.FILES.get("upload_img")
    name = obj.name

    path = os.path.join(settings.BASE_DIR, "static", "upload", name)
    with open(path, "wb") as f:
        for line in obj:
            f.write(line)

    import json

    res = {
        "error": 0,
        "url": "/static/upload/" + name
    }

    return HttpResponse(json.dumps(res))


def delete_article(request, id):
    # Article.objects.filter(nid=id).delete()
    return HttpResponse(str(id))


def compile_article(request,id):
    # html提取数据
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        cate_pk = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")
        # 修改数据库内容
        soup = BeautifulSoup(content,'html.parser')
        for tag in soup.find_all():
            if tag.name in ['script',]:
                tag.decompose()
        desc = soup.text[0:150]
        Article.objects.filter(nid=id).update(title=title, desc=desc,content=str(soup),category_id=cate_pk,user=user)
        Article2Tag.objects.filter(article_id=id).all().delete()
        for i in tags_pk_list:
            Article2Tag.objects.create(article_id=id, tag_id=i)

        return redirect('/backend/')
    # 后台查找发送数据
    article_obj = Article.objects.filter(nid=id).first()
    tag_list = Article2Tag.objects.filter(article_id=id).values_list("tag_id")
    tag_list_id = []
    for i in tag_list:
        tag_list_id.append(i[0])
    blog = request.user.blog
    cate_list = Category.objects.filter(blog=blog)
    tags = Tag.objects.filter(blog=blog)
    print(cate_list,blog,tags,article_obj)
    cate_id = cate_list.filter(blog=blog, article__pk=id).values_list('pk').first()[0]

    return render(request, "backend/add_article.html",locals())
