from django.shortcuts import render_to_response
from django.template import RequestContext
from gitengine.gitolite import GitoliteAdmin
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def index(request):
    if not request.user.is_staff:
        return render_to_response("notAlowed.html",RequestContext(request))
    admin=GitoliteAdmin(settings.GITOLITE_PATH,settings.GITOLITE_URL)
    feedback=""
    fbcolor='green'
    if request.method=="POST":
        saveOk=True
        action= request.POST['action']
        if action.lower().find("save")!=-1:
            content=request.POST['content']
            message=request.POST['message']
            if (message==''):
                feedback="Error: message cannot be empty"
                fbcolor='red'
                saveOk=False
            else:
                admin.save(content, request.POST['message'])
                feedback="Saved"
        if action.lower().find("push")!=-1 and saveOk:
            admin.push()
            content=admin.getConf()
            if len(feedback)>0:
                feedback+=" & "
            feedback+="Pushed"
        if action.lower().find("reset")!=-1:
            content=admin.getConf()
            feedback+="Reset Complete"
    else:
        admin.pull()
        content=admin.getConf()
    return render_to_response("gitolite.html",RequestContext(request,{'repo':admin,'content':content,'fbcolor':fbcolor,'feedback':feedback}))