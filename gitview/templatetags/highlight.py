from pygments import highlight
from pygments.lexers import DiffLexer,get_lexer_for_filename,ClassNotFound,TextLexer
from pygments.formatters import HtmlFormatter
from django import template
register = template.Library()

@register.filter(name='highlightstyle')
def highlightStyle(cssclass):
    return HtmlFormatter().get_style_defs('.'+cssclass)

@register.filter(name='highlightTable')
def highlightCodeTable(code,fileName):
     htmlFormatter=HtmlFormatter(linenos='table')
     try:
         lexer=get_lexer_for_filename(fileName)
     except ClassNotFound:
        lexer=TextLexer()
     return highlight(code,lexer,htmlFormatter)
 
@register.filter(name='highlight')
def highlightCode(code,fileName):
     htmlFormatter=HtmlFormatter()
     try:
         lexer=get_lexer_for_filename(fileName)
     except ClassNotFound:
        lexer=TextLexer()
     return highlight(code,lexer,htmlFormatter)
