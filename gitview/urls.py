from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^commit$', 'gitview.views.commit'),
    url(r'^commits$', 'gitview.views.commits'),
    url(r'^compareCommit$', 'gitview.views.compareCommit'),
    url(r'^new$', 'gitview.views.new'),
    url(r'^graph$', 'gitview.views.graph'),
    url(r'^diff$', 'gitview.views.diff'),
    url(r'^view$', 'gitview.views.view'),
    url(r'^viewgit$', 'gitview.views.viewgit'),
    url(r'^fileContent', 'gitview.views.fileContent'),
    url(r'^rawContent', 'gitview.views.rawContent'),
    url(r'^tree$', 'gitview.views.tree'),
    url(r'^zipTree', 'gitview.views.zipTree'),
    url(r'^$', 'gitview.views.index'),
)
