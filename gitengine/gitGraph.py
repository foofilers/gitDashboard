from django.utils.encoding import smart_unicode
import pygraphviz as pgv
from datetime import datetime

class GitGraphviz:
    def __init__(self,repo,since=None,size=None,until=None,branch=None,commitUrl=None):
        self.repo=repo
        self.G=None
        if since!=None and len(str(since))>0:
            self.since=int(since)
        else:
            self.since=None
        if until!=None and len(str(until))>0:
            self.until=int(until)
        else:
            self.until=None
        if size!=None and len(str(size))>0:
            self.size=int(size)
        else:
            self.size=None
        if branch is None or len(branch)==0:
            self.branch=repo.head()
        else:
            self.branch=branch
        self.commitUrl=commitUrl
            
    def prepare(self):
        allBranches = self.repo.getBranches();
        branches={}
        for ab in allBranches:
            if allBranches[ab] not in branches:
                branches[allBranches[ab]] = ab
            else:
                branches[allBranches[ab]]+=" "+ab
        self.G = pgv.AGraph(name="gitGraph",directed=True,rankdir='LR')
        self.G.node_attr['style']='filled'
        self.G.node_attr['shape']='circle'
        self.G.node_attr['width']='0.2'
        self.G.node_attr['height']='0.2'
        self.G.node_attr['fillcolor']='black'
        parents={}
        dates={}
        labeled=[]
        nbranch=0
        branchCmts={}
        for branch in branches:
            branchName=branches[branch]
            commits=self.repo.getCommits(num=self.size,branch=[branch],since=self.since,until=self.until)
            # cycle for all commits
            for cmt in commits:
                try:
                    branchCmts[branchName].append(cmt.id+"_"+branchName)
                except KeyError:
                    branchCmts[branchName]=[cmt.id+"_"+branchName]
                    
                for prt in cmt._get_parents():
                    if prt in parents:
                        parents[prt+"_"+branchName].append(cmt.id+"_"+branchName)
                    else:
                        parents[prt+"_"+branchName]=[cmt.id+"_"+branchName]
                dt = datetime.fromtimestamp(cmt.commit_time)
                if dt.strftime('%Y-%m') in dates:
                    dates[dt.strftime('%Y-%m')].append(cmt.id)
                else:
                    dates[dt.strftime('%Y-%m')]=[cmt.id]
                htmlTooltip="Author:"+cmt.author+"<br/>"
                htmlTooltip+="Date:"+dt.strftime('%Y-%m-%d %H:%M')+"<br/><hr/>"
                htmlTooltip+="Message:<br/>"+cmt.message.replace('\n',' ')
                
                if self.commitUrl:
                    cmtUrl=self.commitUrl.replace("$$",cmt.id)
                else:
                    cmtUrl=""
                self.G.add_node(cmt.id+"_"+branchName,label='',URL=cmtUrl,id=cmt.id+"_graph")
                
                n=self.G.get_node(cmt.id+"_"+branchName)
                try:
                    n.attr['tooltip']=smart_unicode(htmlTooltip)
                except TypeError:
                    n.attr['tooltip']=htmlTooltip
                labeled.append(cmt.id+"_"+branchName)
                
                for tag in cmt.getTags():
                    self.G.add_node(tag.id,tooltip=tag.name,label=tag.name,shape="rect",fontsize="10",labeldistance=10,fillcolor="lightblue")
                    self.G.add_edge(tag.id,cmt.id+"_"+branchName)    
                for branch in cmt.getBranches():
                    self.G.add_node(str(branch),tooltip=str(branch),label=str(branch),shape="rect",fontsize="10",fillcolor="green")
                    self.G.add_edge(str(branch),cmt.id+"_"+branchName)    
            #cycle for arrow division
            for par in parents:
                for son in parents[par]:
                    if par in labeled and son in labeled:
                        self.G.add_edge(par,son)
            self.G.add_subgraph(nbunch=branchCmts[branchName],name="cluster_"+str(nbranch),label=str(branchName),style='filled')
            nbranch+=1
                        
        # cycle for subgraph 
        #  for m in dates.keys():
        #     self.G.add_subgraph(nbunch=dates[m],name="cluster_"+str(m),label="Data:"+str(m),style='filled')
    def draw(self,path,dotFormat=None):
        self.G.draw(path,prog='dot',format=dotFormat)
    def tostr(self):
        return self.G.to_string()
    
class GitGraphCanvas:
    def __init__(self,repo,commitUrl=None):
        self.repo=repo
        self.commitUrl=commitUrl
        self._width=0
        self._height=0
        self._fontSize=10
        self._maxTooltipWidth=0
        self._maxTooltipHeight=0
        
    def __tooltipRect(self,x,y,width,height,color):
        rectJS='var rect = new Kinetic.Rect({'
        rectJS+='x:'+str(x)+','
        rectJS+='y:'+str(y)+','
        rectJS+='width:'+str(width)+','
        rectJS+='height:'+str(height)+','
        rectJS+='fill:"'+color+'",'
        rectJS+='alpha: 0.75,'
        rectJS+='stroke: "black",'
        rectJS+='strokeWidth: 1'
        rectJS+='});\n'
        rectJS+='tooltipLayer.add(rect);'
        return rectJS
        
    def __tooltip(self,x,y,message):
        tooltipJS='var tooltip = new Kinetic.Text({'
        tooltipJS+='text: "'+message+'",'
        tooltipJS+="x:"+str(x)+','
        tooltipJS+="y:"+str(y)+','
        tooltipJS+='fontFamily: "Verdana",'
        tooltipJS+='fontSize: 10,'
        tooltipJS+='padding: 5,'
        tooltipJS+='textFill: "black"'
        tooltipJS+='})\n;'
        tooltipJS+='tooltipLayer.add(tooltip);'
        return tooltipJS
       
    def __circle(self,x,y,radius,color,tooltip,cmtID):
        circleJS="var circle = new Kinetic.Circle({"
        circleJS+="x:"+str(x)+','
        circleJS+="y:"+str(y)+','
        circleJS+="radius:"+str(radius)+','
        circleJS+='fill:"'+color+'",'
        circleJS+='stroke: "black",'
        circleJS+='strokeWidth: 1'
        circleJS+='});\n'
        
        circleJS+='circle.on("mousemove", function(){\n'
        circleJS+='var mousePos = stage.getMousePosition();\n'
        circleJS+='tooltipLayer.removeChildren();\n'
        circleJS+='document.body.style.cursor = "pointer";\n'
        y=5
        maxLen=0
        tooltips=""
        for msg in tooltip:
            message=msg.replace('"','')
            if len(message)>maxLen:
                maxLen=len(message)
            try:
                message=smart_unicode(message)
            except TypeError:
                message=message
            tooltips+=self.__tooltip('mousePos.x + 5', 'mousePos.y + '+str(y), message);
            y+=20
        if y>self._maxTooltipHeight:
            self._maxTooltipHeight=y
        if maxLen*8>self._maxTooltipWidth:
            self._maxTooltipWidth=maxLen*8
        circleJS+=self.__tooltipRect('mousePos.x + 5', 'mousePos.y', maxLen*8, str(y),color)
        circleJS+=tooltips
        circleJS+='tooltipLayer.show();\n'
        circleJS+='tooltipLayer.draw();\n'
        circleJS+='});\n'
        
        #mouseOut
        circleJS+='circle.on("mouseout", function(){\n'
        circleJS+='tooltipLayer.removeChildren();\n'
        circleJS+='tooltipLayer.hide();\n'
        circleJS+='tooltipLayer.draw();\n'
        circleJS+='document.body.style.cursor = "default";\n'
        circleJS+='});\n'
        
        #click
        circleJS+='circle.on("mousedown", function(){\n'
        if self.commitUrl:
            cmtUrl=self.commitUrl.replace("$$",cmtID)
        else:
            cmtUrl=""
        circleJS+='window.location = "'+cmtUrl+'";'
        circleJS+='});\n'
        circleJS+='circlesLayer.add(circle);\n'
        return circleJS
    
    def __text(self,x,y,text,color):
        textJS='var text= new Kinetic.Text({'
        textJS+='x:'+str(x)+','
        textJS+='y:'+str(y)+','
        textJS+='fontFamily: "Verdana",'
        textJS+='fontSize:'+str(self._fontSize)+','
        textJS+='text:"'+text+'",'
        textJS+='textFill:"'+color+'"'
        textJS+='});\n'
        textJS+='textsLayer.add(text);\n'
        return textJS;
    
    def render(self):
        #recupero i branch
        allBranches = self.repo.getBranches();
        branches={}
        for ab in allBranches:
            if allBranches[ab] not in branches:
                branches[allBranches[ab]] = ab
            else:
                branches[allBranches[ab]]+=" "+ab
        branchesCmtsDates = {}
        #tutte le date presenti
        canvas=""
        commitsPos={}
        cmtAdded=[]
        parents={}
        sons={}
        maxBranchNameLength=0
        cmts={}
        
        dates=[]
        datesX={}
        sortedBranches=[self.repo.head()]
        tmp=[]
        tmp.extend(branches.keys())
        tmp.remove(self.repo.head())
        sortedBranches.extend(tmp)
        for branchSha in sortedBranches:
            if len(branches[branchSha])>maxBranchNameLength:
                maxBranchNameLength=len(branches[branchSha])
            parents[branchSha]=[]        
            branchCmts=self.repo.getCommits(branch=[branchSha])            
            branchDates={}
            for cmt in branchCmts:
                cmts[cmt.id]=cmt
                dt = datetime.fromtimestamp(cmt.commit_time)
                dates.append(dt.strftime('%Y-%m-%d-%H-%M-%s'))
                cmtID=cmt.id+"_"+branchSha
                if cmtID in parents[branchSha] or cmt.id==branchCmts[0].id:
                    if len(cmt._get_parents())>0:
                        firstPrt=cmt._get_parents()[0]
                        firstprtID=firstPrt+"_"+branchSha
                        parents[branchSha].append(firstprtID)
                        for prt in cmt._get_parents():
                            if prt in sons:
                                sons[prt].append(cmtID)
                            else:
                                sons[prt]=[cmtID]
                    if dt.strftime('%Y-%m-%d-%H-%M-%s') in branchDates:
                        branchDates[dt.strftime('%Y-%m-%d-%H-%M-%s')].append(cmtID)
                    else:
                        branchDates[dt.strftime('%Y-%m-%d-%H-%M-%s')]=[cmtID]
            branchesCmtsDates[branchSha] = branchDates;
        dates=sorted(set(dates))
        radius=6
        x=maxBranchNameLength*(self._fontSize-2)
        xDelay=((radius*2)+10)
        for dt in dates:
            xMax=1
            #find maximum number of commit for each date
            for branchSha in sortedBranches:
                try:
                    if len(branchesCmtsDates[branchSha][dt])>max:
                        xMax=len(branchesCmtsDates[branchSha][dt])
                except KeyError:
                    pass
            datesX[dt]=x
            x+=xDelay*xMax
        y=15
        for branchSha in sortedBranches:
            #draw branch names
            if branchSha == self.repo.head():
                canvas+=self.__text(15, y, branches[branchSha], "red")
                color="red"
            else:
                canvas+=self.__text(15, y, branches[branchSha], "black")
                color="#8ED6FF"
            #draw commits
            for dt in dates:
                cmtNum=0
                try:
                    for cmt in branchesCmtsDates[branchSha][dt]:
                        cmtX=datesX[dt]+(xDelay*cmtNum)
                        #set global width
                        if cmtX>self._width:
                            self._width=cmtX
                        cmtID=cmt.split('_')[0]
                        if cmtID not in cmtAdded:
                            tooltip=[]
                            tooltip.append("Branch: "+branches[branchSha])
                            tooltip.append("Author: "+cmts[cmtID].author)
                            dt = datetime.fromtimestamp(cmts[cmtID].commit_time)
                            tooltip.append("Date: "+dt.strftime('%Y-%m-%d %H:%M:%S'))
                            tooltip.append("--------------");
                            rows=cmts[cmtID].message.split('\n')
                            for row in rows:
                                if len(row)>0:
                                    tooltip.append(row)
                            #draw circle
                            canvas+=self.__circle(cmtX, y, radius, color,tooltip,cmtID)
                            #add circle positions on commitsPos dictionary
                            commitsPos[cmt]=(cmtX,y)
                            cmtAdded.append(cmtID)
                            cmtNum+=1
                except KeyError:
                    pass
            #next branch y position
            y+=radius+20
        #set the global height
        self._height=y
        #Lines
        for par in sons.keys():
            for branchSha in sortedBranches:
                parID=par+"_"+branchSha
                if parID in commitsPos:
                    xPar=commitsPos[parID][0]
                    yPar=commitsPos[parID][1]
                    for son in sons[par]:
                        if son in commitsPos:
                            x=commitsPos[son][0]
                            y=commitsPos[son][1]
                            canvas+='line('+str(xPar)+','+str(yPar)+','+str(x)+','+str(y)+',"#000000",linesLayer);\n'
        return canvas
    def getWidth(self):
        return self._width+self._maxTooltipWidth
    def getHeight(self):
        return self._height+self._maxTooltipHeight
    