from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from .models import Question, Answer, Comment, UpVote, DownVote
from django.core.paginator import Paginator
from django.contrib import messages
from . forms import AnswerForm, QuestionForm, ProfileForm
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from django.forms import inlineformset_factory
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm

# Home Page
def home(request):
    return render(request, 'index.html')

#show question
def show_question(request):
    if 'q' in request.GET:
        q = request.GET['q']
        quests = Question.objects.annotate(total_comments=Count(
            'answer__comment')).filter(title__icontains=q).order_by('-id')
    else:
        quests = Question.objects.annotate(
            total_comments=Count('answer__comment')).all().order_by('-id')
    paginator = Paginator(quests, 10)
    page_num = request.GET.get('page', 1)
    quests = paginator.page(page_num)
    return render(request, 'show-question.html', {'quests': quests})

# Detail


def detail(request, id):
    quest = Question.objects.get(pk=id)
    tags = quest.tags.split(',')
    answers = Answer.objects.filter(question=quest)
    answerform = AnswerForm
    if request.method == 'POST':
        answerData = AnswerForm(request.POST)
        if answerData.is_valid():
            answer = answerData.save(commit=False)
            answer.question = quest
            answer.user = request.user
            answer.save()
            messages.success(request, 'Answer has been submitted.')
    return render(request, 'detail.html', {
        'quest': quest,
        'tags': tags,
        'answers': answers,
        'answerform': answerform
    })

# Save Comment


def save_comment(request):
    if request.method == 'POST':
        comment = request.POST['comment']
        answerid = request.POST['answerid']
        answer = Answer.objects.get(pk=answerid)
        user = request.user
        Comment.objects.create(
            answer=answer,
            comment=comment,
            user=user
        )
        return JsonResponse({'bool': True})

# Save Upvote


def save_upvote(request):
    if request.method == 'POST':
        answerid = request.POST['answerid']
        answer = Answer.objects.get(pk=answerid)
        user = request.user
        check = UpVote.objects.filter(answer=answer, user=user).count()
        if check > 0:
            return JsonResponse({'bool': False})
        else:
            UpVote.objects.create(
                answer=answer,
                user=user
            )
            return JsonResponse({'bool': True})

# Save Downvote


def save_downvote(request):
    if request.method == 'POST':
        answerid = request.POST['answerid']
        answer = Answer.objects.get(pk=answerid)
        user = request.user
        check = DownVote.objects.filter(answer=answer, user=user).count()
        if check > 0:
            return JsonResponse({'bool': False})
        else:
            DownVote.objects.create(
                answer=answer,
                user=user
            )
            return JsonResponse({'bool': True})

# User Register


def register(request):
    if request.user.is_authenticated:
	    return redirect('home')
    else:
	    form = CreateUserForm()
	    if request.method == 'POST':
		    form = CreateUserForm(request.POST)
		    if form.is_valid():
			    form.save()
			    user = form.cleaned_data.get('username')
			    messages.success(request, 'Account was created for ' + user)
			    return redirect('login')
	    context = {'form': form}
	    return render(request, 'registration/register.html', context)

#Login
def login(request):
    if request.user.is_authenticated:
	    return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request,username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Username OR password is incorrect')
        return render(request, 'registration/login.html')


    
# Ask Form



def ask_form(request):
    form = QuestionForm
    if request.method == 'POST':
        questForm = QuestionForm(request.POST)
        if questForm.is_valid():
            if request.user.is_authenticated:
                questForm = questForm.save(commit=False)
                questForm.user = request.user
                questForm.save()
                messages.success(request, 'Question has been added.')
            else:
                messages.info(request, 'You need to login first!')
                return redirect('login')
    return render(request, 'ask-question.html', {'form': form})


# Questions according to tag
def tag(request, tag):
    quests = Question.objects.annotate(total_comments=Count(
        'answer__comment')).filter(tags__icontains=tag).order_by('-id')
    paginator = Paginator(quests, 10)
    page_num = request.GET.get('page', 1)
    quests = paginator.page(page_num)
    return render(request, 'tag.html', {'quests': quests, 'tag': tag})

# Profile


def profile(request):
    quests = Question.objects.filter(user=request.user).order_by('-id')
    answers = Answer.objects.filter(user=request.user).order_by('-id')
    comments = Comment.objects.filter(user=request.user).order_by('-id')
    upvotes = UpVote.objects.filter(user=request.user).order_by('-id')
    downvotes = DownVote.objects.filter(user=request.user).order_by('-id')
    if request.method == 'POST':
        profileForm = ProfileForm(request.POST, instance=request.user)
        if profileForm.is_valid():
            profileForm.save()
            messages.success(request, 'Profile has been updated.')
    form = ProfileForm(instance=request.user)
    return render(request, 'registration/profile.html', {
        'form': form,
        'quests': quests,
        'answers': answers,
        'comments': comments,
        'upvotes': upvotes,
        'downvotes': downvotes,
    })

# Tags Page


def tags(request):
    quests = Question.objects.all()
    tags = []
    for quest in quests:
        qtags = [tag.strip() for tag in quest.tags.split(',')]
        for tag in qtags:
            if tag not in tags:
                tags.append(tag)
    # Fetch Questions
    tag_with_count = []
    for tag in tags:
        tag_data = {
            'name': tag,
            'count': Question.objects.filter(tags__icontains=tag).count()
        }
        tag_with_count.append(tag_data)
    return render(request, 'tags.html', {'tags': tag_with_count})
