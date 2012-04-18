from django import template
import md5
register = template.Library()
 
@register.filter(name='gravatarImageUrl')
def gravatarImageUrl(email,size):
    md5Email=md5.new(email).hexdigest()
    return "http://www.gravatar.com/avatar/"+md5Email+"?d=mm&s="+str(size)
    
