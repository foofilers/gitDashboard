from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^commit$', 'gitview.views.commit'),
    url(r'^commits$', 'gitview.views.commits'),
    url(r'^compareCommit$', 'gitview.views.compareCommit'),
    url(r'^new$', 'gitview.views.new'),
    url(r'^graph$', 'gitview.views.graph'),
    url(r'^diff$', 'gitview.fileViews.diff'),
    url(r'^view$', 'gitview.fileViews.view'),
    url(r'^viewgit$', 'gitview.views.viewgit'),
    url(r'^viewgit/$', 'gitview.views.viewgit'),
    url(r'^fileContent', 'gitview.fileViews.fileContent'),
    
    url(r'^rawContent', 'gitview.fileViews.rawContent'),
    url(r'^tree$', 'gitview.fileViews.tree'),
    url(r'^zipTree', 'gitview.fileViews.zipTree'),
    url(r'^gitolite$', 'gitview.gitolite.index'),
    url(r'^gitoliteFile', 'gitview.gitolite.fileContent'),
    url(r'^$', 'gitview.views.index'),
)
