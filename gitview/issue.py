from suds.client import Client,WebFault
import re
from xml.sax._exceptions import SAXParseException
import logging
class Mantis1_7IssuePane():
    
    def __init__(self,message,parseMessage,wsdlUrl,issueUrl,username,password):
        self.message=message
        self.parseMessage=parseMessage
        self.wsdlUrl=wsdlUrl
        self.issueUrl=issueUrl
        self.username=username
        self.password=password
        
        pattern = parseMessage.replace("%ID%",'([0-9]*)')
        gr = re.search(pattern,message)
        self.issueId=int(gr.group(1))

    def renderHtml(self):
        """ Return html rendered REMEMBER to render inside <div> """
        
        result="<table width='100%'>"
        result+='<tr><td colspan="2" style="text-align:center;"><img src="/static/images/mantis_logo.gif" height="40" title="Mantis"/></td></tr>'
        try:
            soapClient = Client(self.wsdlUrl)
            issue = soapClient.service.mc_issue_get(self.username,self.password,self.issueId)
            self.issue=issue
            result+="<tr><td>Id:</td><td><a href=\""+Mantis1_7IssuePane.getMantisLink(self.message, self.parseMessage, self.issueUrl)+'">'+str(self.issueId)+"</a></td></tr>";
            result+="<tr><td>Project:</td><td>"+str(self.issue.project.name)+"</td></tr>";
            result+="<tr><td>Category:</td><td>"+str(self.issue.category)+"</td></tr>";
            result+="<tr><td>Summary:</td><td>"+str(self.issue.summary)+"</td></tr>";
            result+="<tr><td>Status:</td><td>"+str(self.issue.status.name)+"</td></tr>";
            
        except SAXParseException:
            logging.getLogger(self.__class__).error("SaxParseException")
        except WebFault as error:
            faultString=error.fault.faultstring
            edpos = faultString.find('Error Description')
            if edpos>-1:
                errorMsg=faultString[edpos:faultString.find(",",edpos)]
            else:
                errorMsg=faultString
            result+="<tr><td colspan='2'>"+errorMsg+"</td></tr>";
        
        result+="</table>"
        return result
    
    @staticmethod
    def getMantisLink(message,parseMessage,url):
        pattern = parseMessage.replace("%ID%",'([0-9]*)')
        link = url
        gr = re.search(pattern,message)
        link = link.replace('%ID%',gr.group(1))
        return link
        
        