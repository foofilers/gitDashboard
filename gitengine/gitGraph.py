from django.utils.encoding import smart_unicode,DjangoUnicodeDecodeError
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

def canvasTooltipRect(x,y,width,height,color):
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

def canvasDateRect(x,y,width,color):
    rectJS='var dateRect = new Kinetic.Rect({'
    rectJS+='x:'+str(x)+','
    rectJS+='y:'+str(y)+','
    rectJS+='width:'+str(width)+','
    rectJS+='height:20,'
    rectJS+='fill:"'+color+'",'
    rectJS+='alpha: 0.75,'
    rectJS+='stroke: "white",'
    rectJS+='strokeWidth: 1'
    rectJS+='});\n'
    rectJS+='textGroup.add(dateRect);'
    return rectJS
    
def canvasTooltip(x,y,message):
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
   
def canvasCircle(x,y,radius,color,tooltip,cmtID,gitGraph):
    jsvar='circle_'+cmtID
    circleJS="var "+jsvar+" = new Kinetic.Circle({"
    circleJS+="x:"+str(x)+','
    circleJS+="y:"+str(y)+','
    circleJS+="radius:"+str(radius)+','
    circleJS+='fill:"'+color+'",'
    circleJS+='stroke: "black",'
    circleJS+='strokeWidth: 1'
    circleJS+='});\n'
    
    circleJS+=jsvar+'.on("mouseover", function(){\n'
    circleJS+='var mousePos = stage.getMousePosition();\n'
    circleJS+='tooltipLayer.removeChildren();\n'
    circleJS+='document.body.style.cursor = "pointer";\n'
    tooltipY=5
    maxLen=0
    tooltips=""
    numLines=0
    for msg in tooltip:
        if numLines<14:
            if numLines==13:
                message="[continua...]"
            else:
                message=str(msg).replace('"','')
                if len(message)>maxLen:
                    maxLen=len(message)
                try:
                    message=smart_unicode(message)
                except TypeError:
                    pass
                except DjangoUnicodeDecodeError:
                    message=message.decode('latin1')
            tooltips+=canvasTooltip('mousePos.x+20', 'mousePos.y+'+str(tooltipY+20), message);
            tooltipY+=20
            numLines+=1
        
    if (tooltipY-20)>gitGraph._maxTooltipHeight:
        gitGraph._maxTooltipHeight=tooltipY-20
        
    if maxLen*8>gitGraph._maxTooltipWidth:
        gitGraph._maxTooltipWidth=maxLen*8
        
    circleJS+=canvasTooltipRect('mousePos.x+20', 'mousePos.y+20', maxLen*8, str(tooltipY),color)
    circleJS+=tooltips
    circleJS+='tooltipLayer.show();\n'    
    circleJS+='tooltipLayer.draw();\n'
    circleJS+='});\n'
    
    #mouseOut
    circleJS+=jsvar+'.on("mouseout", function(){\n'
    circleJS+='tooltipLayer.removeChildren();\n'
    circleJS+='tooltipLayer.hide();\n'
    circleJS+='tooltipLayer.draw();\n'
    circleJS+='document.body.style.cursor = "default";\n'
    circleJS+='});\n'
    
    #click
    circleJS+=jsvar+'.on("mousedown", function(){\n'
    if gitGraph.commitUrl:
        cmtUrl=gitGraph.commitUrl.replace("$$",cmtID)
    else:
        cmtUrl=""
    circleJS+='window.location = "'+cmtUrl+'";'
    circleJS+='});\n'
    
    circleJS+='circleGroup.add('+jsvar+');\n'
    return circleJS

def canvasText(x,y,text,color,gitGraph,fontSize=None):
    textJS='var text= new Kinetic.Text({'
    textJS+='x:'+str(x)+','
    textJS+='y:'+str(y)+','
    textJS+='fontFamily: "Verdana",'
    if fontSize:
        textJS+='fontSize:'+str(fontSize)+','
    else:
        textJS+='fontSize:'+str(gitGraph._fontSize)+','
    textJS+='text:"'+text+'",'
    textJS+='textFill:"'+color+'"'
    textJS+='});\n'
    textJS+='textGroup.add(text);\n'
    return textJS;
    
class CommitGraph:
    def __init__(self,cmt,x,y,color,gitGraph,branchName):
        self.x=x;
        self.y=y;
        self.cmt=cmt;
        self.color=color
        self.gitGraph=gitGraph
        self.branchName=branchName
    def draw(self):
        radius=6
        tooltip=[]
        tooltip.append("id: "+self.cmt.id)
        cmprts=self.cmt._get_parents()
        for cmpr in cmprts:
            tooltip.append("parent: "+cmpr)
        tooltip.append("Branch: "+self.branchName)
        tooltip.append("Author: "+self.cmt.author)
        dt = datetime.fromtimestamp(self.cmt.commit_time)
        tooltip.append("Date: "+dt.strftime('%Y-%m-%d %H:%M:%S'))
        tooltip.append("--------------");
        rows=self.cmt.message.split('\n')
        for row in rows:
            if len(row)>0:
                tooltip.append(row)
        return canvasCircle(self.x, self.y, radius, self.color,tooltip,self.cmt.id,self.gitGraph)

class GitGraphCanvas:
    def __init__(self,repo,since=None,until=None,commitUrl=None):
        self.repo=repo
        self.commitUrl=commitUrl
        self._width=0
        self._height=0
        self._fontSize=10
        self._maxTooltipWidth=0
        self._maxTooltipHeight=0
        self.since=since
        self.until=until
    def render(self):
        #the return string
        canvas=""
        #Dict key:cmtID value: (x,y)
        commitsPos={}
        #Commit already added
        cmtAdded=[]
        #Dict key:cmtID value:instance of GraphCommit
        graphCommits={}
        #Dict key:sonId value=[parentID,...]
        parents={}
        #Dict key:parentId value=[sonID,...]
        sons={}
        #Max lenght(calculated based numchar*8) of name of branch
        maxBranchNameLength=0
        #Dict Key:cmtID value:instance of GitCommit
        cmts={}
        #all dates
        dates=[]
        #Date associated to x coordinate
        datesX={}
        #List of years
        years=[]
        #Dict key:year value=(xMin,xMax)
        yearX={}
        #List of months
        months=[]
        #Dict key:month value=(xMin,xMax)
        monthX={}
        #List of months
        days=[]
        #Dict key:day value=(xMin,xMax)
        daysX={}
        #Dict key:date value:[cmtID,...]
        branchesCmtsDates = {}
        
        #fetch branches
        allBranches = self.repo.getBranches();
        branches={}
        for ab in allBranches:
            if allBranches[ab] not in branches:
                branches[allBranches[ab]] = ab
            else:
                branches[allBranches[ab]]+=" "+ab
        sortedBranches=[self.repo.head()]
        tmp=[]
        tmp.extend(branches.keys())
        tmp.remove(self.repo.head())
        sortedBranches.extend(tmp)
        
        #associate commits to its date
        for branchSha in sortedBranches:
            if len(branches[branchSha])>maxBranchNameLength:
                maxBranchNameLength=len(branches[branchSha])
            parents[branchSha]=[]        
            branchCmts=self.repo.getCommits(branch=[branchSha],since=self.since,until=self.until)            
            branchDates={}
            for cmt in branchCmts:
                cmts[cmt.id]=cmt
                dt = cmt.commit_time
                dates.append(dt)
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
                    if dt in branchDates:
                        branchDates[dt].append(cmtID)
                    else:
                        branchDates[dt]=[cmtID]
            branchesCmtsDates[branchSha] = branchDates;
        dates=sorted(set(dates))
        radius=10
        x=maxBranchNameLength*(self._fontSize-2)
        xDelay=((radius*2)+10)
        
        #find the first x coordinate for each date
        currMonth=""
        currDay=""
        currYear=""
        lastDt = dates[len(dates)-1]
        for dt in dates:
            xMax=1
            #YEARS
            year = datetime.fromtimestamp(dt).strftime('%Y')
            if currYear!=year:
                #the first year
                if currYear!="":
                    yearX[currYear]=(yearX[currYear][0],x)
                years.append(year)
                if dt==lastDt:
                    yearX[year]=(x,xDelay*xMax)
                else:
                    yearX[year]=(x,x)
                currYear=year
            else:
                if dt==lastDt:
                    yearX[currYear]=(yearX[currYear][0],x+xDelay*xMax)
            #MONTHS
            month = datetime.fromtimestamp(dt).strftime('%Y-%m')
            if currMonth!=month:
                #the first month
                if currMonth!="":
                    monthX[currMonth]=(monthX[currMonth][0],x)
                months.append(month)
                if dt==lastDt:
                    monthX[month]=(x,xDelay*xMax)
                else:
                    monthX[month]=(x,x)
                currMonth=month
            else:
                if dt==lastDt:
                    monthX[currMonth]=(monthX[currMonth][0],x+xDelay*xMax)
            #DAYS 
            day = datetime.fromtimestamp(dt).strftime('%Y-%m-%d')
            if currDay!=day:
                #the first day
                if currDay!="":
                    daysX[currDay]=(daysX[currDay][0],x)
                days.append(day)
                if dt==lastDt:
                    daysX[day]=(x,x+xDelay*xMax)
                else:
                    daysX[day]=(x,x)
                currDay=day
            else:
                if dt==lastDt:
                    daysX[currDay]=(daysX[currDay][0],x+xDelay*xMax)
            #find maximum number of commit for each date
            for branchSha in sortedBranches:
                try:
                    if len(branchesCmtsDates[branchSha][dt])>max:
                        xMax=len(branchesCmtsDates[branchSha][dt])
                except KeyError:
                    pass
            datesX[dt]=x
            x+=xDelay*xMax
        #creation of commits graphs structures
        for branchSha in sortedBranches:
            graphCommits[branchSha]=[]
            if branchSha == self.repo.head():
                color="red"
            else:                
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
                            #do not set y because it will be recalculate later
                            graphCmt = CommitGraph(cmts[cmtID],cmtX,0,color,self,branches[branchSha])
                            graphCommits[branchSha].append(graphCmt)
                            #add circle positions on commitsPos dictionary
                            commitsPos[cmt]=graphCmt
                            cmtAdded.append(cmtID)
                            cmtNum+=1
                except KeyError:
                    pass
        #DRAW!
        #draw date row
        
        years = sorted(years)
        for y in years:
            canvas+=canvasDateRect(yearX[y][0]-radius-5, 7, yearX[y][1]-yearX[y][0],"black");
            yX=yearX[y][0]+((yearX[y][1]-yearX[y][0])/2)-radius-10
            canvas+=canvasText(yX,12,y,'white',self,fontSize=8)
        
        months = sorted(months)
        for mn in months:
            canvas+=canvasDateRect(monthX[mn][0]-radius-5, 27, monthX[mn][1]-monthX[mn][0],"#202020");
            mnX=monthX[mn][0]+((monthX[mn][1]-monthX[mn][0])/2)-radius-10
            canvas+=canvasText(mnX,32,mn.split('-')[1],'white',self,fontSize=8)
        days = sorted(days)
        for d in days:
            canvas+=canvasDateRect(daysX[d][0]-radius-5, 47, daysX[d][1]-daysX[d][0],"#404040");
            dX=daysX[d][0]+((daysX[d][1]-daysX[d][0])/2)-radius-10
            canvas+=canvasText(dX,52,d.split('-')[2],'white',self,fontSize=8)
        #y delay
        y=80
        branchToDrop=[] #list of branch to drop because is empty
        for branchSha in sortedBranches:
            if len(graphCommits[branchSha])>0:
                if branchSha == self.repo.head():
                    canvas+=canvasText(15, y, branches[branchSha], "red",self)
                    color="red"
                else:
                    canvas+=canvasText(15, y, branches[branchSha], "black",self)
                    color="#8ED6FF"
                #draw circle
                for grpCmt in graphCommits[branchSha]:
                    grpCmt.y=y
                    canvas+=grpCmt.draw()
                y+=radius+20
            else:
                branchToDrop.append(branchSha)
        for delSha in branchToDrop:
            sortedBranches.remove(delSha)
            
        #set the global height
        self._height=y
        #Lines
        for par in sons.keys():
            for branchSha in sortedBranches:
                parID=par+"_"+branchSha
                if parID in commitsPos:
                    xPar=commitsPos[parID].x
                    yPar=commitsPos[parID].y
                    for son in sons[par]:
                        if son in commitsPos:
                            x=commitsPos[son].x
                            y=commitsPos[son].y
                            canvas+='line('+str(xPar)+','+str(yPar)+','+str(x)+','+str(y)+',"#000000",lineGroup);\n'
        return canvas
    def getWidth(self):
        return self._width
    def getHeight(self):
        return self._height+self._maxTooltipHeight
    