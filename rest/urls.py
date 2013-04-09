from django.conf.urls import patterns, url
urlpatterns = patterns('',
    url(r'checkLDAPUser$', 'rest.utility.checkLDAPUser'),
    url(r'searchRepos', 'rest.search.searchRepos'),
)