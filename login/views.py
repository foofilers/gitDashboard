from django.template import loader, RequestContext
from django.http import HttpResponse
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
# Create your views here.

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput)


def loginView(request):
	errorMessage = None
	if request.method == 'POST':
		loginForm = LoginForm(request.POST)
		if loginForm.is_valid():
			user = authenticate(username=request.POST['username'], password=request.POST['password'])
			if user is None:
				logout(request)
				errorMessage = "Login failed"
			else:
				login(request, user)
				nextPage = request.POST['nextPage']
				if nextPage is not None and nextPage != '':
					return redirect(to=nextPage)
	else:
		loginForm = LoginForm()
	try:
		nextPage = request.GET['next']
	except KeyError:
		nextPage = reverse('gitview.views.index')
	t = loader.get_template('login.html')
	c = RequestContext(request, {'loginForm': loginForm, 'nextPage': nextPage, 'errorMessage': errorMessage})
	return HttpResponse(t.render(c))


def logoutView(request):
	logout(request)
	t = loader.get_template('logout.html')
	c = RequestContext(request)
	return HttpResponse(t.render(c))
