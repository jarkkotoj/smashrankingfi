import glicko
import player
import database
import datetime
from dateutil.relativedelta import *
import challonge
import smashgg
from random import randint
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

tourwinopen = False
playerwinopen = False
setswinopen = False

def stringtodate(string) :
    return datetime.datetime.strptime(string,'%Y-%m-%d')

def closewindow(window) :
    global tourwinopen
    global playerwinopen
    global setswinopen
    if (window.title() == 'Tournaments') :
        tourwinopen = False
    elif (window.title() == 'Players') :
        playerwinopen = False
    elif (window.title() == 'Sets') :
        setswinopen = False
    window.destroy()

#
# Tournament branch starts here!
#

#Lists tournaments
def tourwin() :
    global tourwinopen
    if (tourwinopen == True) :
        return 0
    window = Toplevel(root)
    window.title('Tournaments')
    tourwinopen = True
    window.protocol("WM_DELETE_WINDOW", lambda *args : closewindow(window))
    frame = ttk.Frame(window, padding="3 3 3 3")
    frame.grid(row=0, column=0, sticky=(N,S,W,E))
    
    tree = ttk.Treeview(frame, columns = ('name','date','evaluated'))
    tree.grid(row=1, column=1,columnspan=4)
    tree['show']='headings'
    tree.heading('name',text='Name')
    tree.heading('date',text='Date')
    tree.heading('evaluated', text = 'Evaluated')
    tree.column('evaluated',width=80)
    tree.column('date',width=100)
    tree.column('name',width=320)
    
    alltours = database.findalltournaments()
    alltours.sort(key = lambda tour : tour.enddate)
    for ind in range(len(alltours)) :
        tree.insert('','end',str(ind))
        tree.set(str(ind),'name',alltours[ind].name)
        tree.set(str(ind),'date',datetime.datetime.strftime(alltours[ind].startdate,'%Y-%m-%d'))
        tree.set(str(ind),'evaluated',str(bool(alltours[ind].evaluated)))
    tree.bind('<Double-1>', lambda *args : opentournamentwindow(window,alltours[int(tree.selection()[0])]))
    
    addbutt = ttk.Button(frame, text='Add Tournament',command = lambda *args: addtournament(window,alltours,tree))
    addbutt.grid(row=2, column=1)
    ttk.Button(frame, text='Modify tournament',command = lambda *args: modtournament(window,alltours[int(tree.selection()[0])],alltours,tree)).grid(row=2,column=2)
    ttk.Button(frame, text='Delete tournament',command = lambda *args: deltournament(window,alltours[int(tree.selection()[0])],alltours,tree)).grid(row=2,column=3)
    ttk.Button(frame, text='Add tournament from internet', command = lambda *args : newtournamentauto(window,alltours,tree)).grid(row=2,column=4)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)
    
    return 1

#Modify tournament name, date
def modtournament(window0,tour,alltours,tree) :
    ind = tree.selection()[0]
    window = Toplevel(window0)
    window.title('Modify tournament ' + tour.name)
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    
    tourname = StringVar()
    tourname.set(tour.name)
    startdate = StringVar()
    startdate.set(tour.startdate.strftime('%Y-%m-%d'))
    enddate = StringVar()
    enddate.set(tour.enddate.strftime('%Y-%m-%d'))
    city = StringVar()
    city.set(tour.city)
    
    ttk.Label(frame,text='Tournament name:').grid(row=1,column=1)
    ttk.Label(frame,text='Start YYYY-MM-DD:').grid(row=2,column=1)
    ttk.Label(frame,text='End:').grid(row=3,column=1)
    ttk.Label(frame,text='City:').grid(row=4,column=1)
    Entry(frame,textvariable = tourname).grid(row=1,column=2)
    Entry(frame,textvariable = startdate).grid(row=2,column=2)
    Entry(frame,textvariable = enddate).grid(row=3,column=2)
    Entry(frame,textvariable = city).grid(row=4,column=2)

    button = ttk.Button(frame,text='Modify the data', command = lambda *args: modtournamentbutton(window, tree, alltours, tour,tourname.get(),startdate.get(),enddate.get(),city.get(),ind)).grid(row=5,column=1)
    
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)
    
    
def modtournamentbutton(window, tree, alltours, tour,tourname,startdates,enddates,city,ind) :
    try :
        startdate = datetime.datetime.strptime(startdates,'%Y-%m-%d')
        enddate = datetime.datetime.strptime(enddates,'%Y-%m-%d')
        if (startdate>enddate) :
            return 0
            print("Date formatting error!")
    except :
        print("Date formatting error!")
        return 0
    if (city=='') :
        return 0
    if (tourname != tour.name) :
        if (not (database.findtournamentbyname(tourname) is None)) :
            print("Name taken!")
            return 0
        tour.name = tourname
    tour.city = city
    tour.startdate=startdate
    tour.enddate=enddate
    tree.set(str(ind),'name',tour.name)
    tree.set(str(ind),'date',tour.startdate.strftime('%Y-%m-%d'))
    database.addorupdatetournament(tour)
    window.destroy()
    return 1
    
def deltournament(window0,tour,alltours,tree) :
    ind = int(tree.selection()[0])
    answer=messagebox.askyesno(message='Are you sure you wish to delete tournament '+ tour.name +'? All included results and sets will be lost!',icon='question',title='Delete '+tour.name+'?')
    if (answer == False) :
        return 0
    setlist = database.findallsetsfortournament(tour)
    for setti in setlist :
        database.deleteset(setti)
    reslist = database.findresults(tour)
    for res in reslist :
        database.deleteresult(res)
    del alltours[ind]
    for i in range(ind,len(alltours)) :
        tree.delete(str(ind))
        tree.insert('','end',str(ind))
        tree.set(str(ind),'name',alltours[i].name)
        tree.set(str(ind),'date',alltours[i].startdate.strftime('%Y-%m-%d'))
        tree.set(str(ind),'evaluated',str(bool(alltours[i].evaluated)))
    tree.delete(str(len(alltours)))
    database.deletetournament(tour)

#Create a new tournament from Challonge or smash.gg
def newtournamentauto(window0,alltours,tree) :
    window = Toplevel(window0)
    window.title('Smash.gg or Challonge?')
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    ttk.Label(frame, text='Choose site').grid(row=1,column=1,columnspan=2)
    ttk.Button(frame,text='Smash.gg',command=lambda *args:newtournamentgg(window,window0,alltours,tree)).grid(row=2,column=2)
    ttk.Button(frame,text='Challonge',command = lambda *args:newtournamentchallonge(window,window0,alltours,tree)).grid(row=2,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


#Add a tournament using smash.gg    
def newtournamentgg(window00,window0,alltours,tree):
    if (smashgg.apikey.strip()=='') :
        smashgg.getapikey()
        if (smashgg.apikey.strip()==''):
            messagebox.showinfo(message='No API key found. Insert one into smashggkey.dat and try again!', title='No API key')
            return 0
        
    window00.destroy()
    window=Toplevel(window0)
    window.title('Retrieve data from smash.gg')
    frame=ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0)
    
    tourkey=StringVar()
    helpwords = StringVar()
    helpwords.set('')
    ttk.Label(frame,text='Tournament slug:').grid(row=1,column=1)
    Entry(frame,textvariable=tourkey).grid(row=1,column=2)
    ttk.Label(frame,text='Help words (optional):').grid(row=2,column=1)
    Entry(frame,textvariable=helpwords).grid(row=2,column=2)
    
    ttk.Button(frame,text='Retrieve', command= lambda *args :ggtournament0(window,window0,alltours,tree,tourkey.get(),helpwords.get())).grid(row=3,column=1,columnspan=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Add a tournament using smash.gg API
def ggtournament0(window00,window0,alltours,tree,tourkey,helpwords) :
    window00.destroy()
    
    if(helpwords.strip()==''):
        hit=smashgg.retrievetournament(tourkey)
        if (hit is None) :
            messagebox.showinfo(message="No tournament found!",title="No tournament found!")
            return 0
    else :
        helpwords = helpwords.strip().lower().split(' ')
        hit=smashgg.retrievetournament(tourkey,helpwords)
        if (hit is None) :
            messagebox.showinfo(message="No tournament found!",title="No tournament found!")
            return 0
    (tournames,startdate,enddate,citys,reslist,setlist)=hit
    
    window=Toplevel(window0)
    window.title('Retrieve data from smash.gg')
    frame=ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0)
    
    tourname = StringVar()
    startdates = StringVar()
    enddates = StringVar()
    city = StringVar()
    tourname.set(tournames)
    startdates.set(startdate.strftime('%Y-%m-%d'))
    enddates.set(enddate.strftime('%Y-%m-%d'))
    city.set(citys)
    
    ttk.Label(frame, text='Tournament name: ').grid(row=1,column=1)
    ttk.Label(frame, text='Started (YYYY-MM-DD): ').grid(row=2,column=1)
    ttk.Label(frame, text='Ended: ').grid(row=3,column=1)
    ttk.Label(frame, text='City: ').grid(row=4,column=1)
    Entry(frame, textvariable=tourname).grid(row=1,column=2)
    Entry(frame, textvariable=startdates).grid(row=2,column=2)
    Entry(frame, textvariable=enddates).grid(row=3,column=2)
    Entry(frame, textvariable=city).grid(row=4,column=2)
    Button(frame, text='Proceed', command=lambda *args : ggtournament1(window,window0,alltours,tree,reslist,setlist,tourname.get(),startdates.get(),enddates.get(),city.get())).grid(row=5,column=1,columnspan=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)    

def ggtournament1(window00,window0,alltours,tree,reslist,setlist,tourname,startdates,enddates,city):
    if (not (database.findtournamentbyname(tourname) is None)) :
        messagebox.showinfo(message='Tournament name taken!', title='Name taken')
        return 0
    try :
        if (stringtodate(startdates)>stringtodate(enddates)) :
            messagebox.showinfo(message='Tournament cannot start after its end', title='Check the dates')
            return 0
    except :
        print("Date formats wrong!")
        return 0
    if (city ==''):
        messagebox.showinfo(message='Please input city!', title='Write city')
        return 0
    
    tour = player.Tournament(tourname,-1,city,stringtodate(startdates),stringtodate(enddates),False)
    database.addorupdatetournament(tour)
    alltours.append(tour)
    tree.insert('','end',str(len(alltours)-1))
    tree.set(str(len(alltours)-1),'name',tour.name)
    tree.set(str(len(alltours)-1),'date',tour.startdate.strftime('%Y-%m-%d'))
    tree.set(str(len(alltours)-1),'evaluated',str(bool(tour.evaluated)))
    window00.destroy()
    
    ggtournament2(window0, reslist,setlist,tour)

def hasplayername(plr,name) :
    if (plr.name.strip().lower() == name.strip().lower()):
        return True
    for alt in plr.alts :
        if (alt.strip().lower() == name.strip().lower()):
            return True
    return False

def ggtournament2(window0,reslist,setlist,tour) :
    resobjlist = []
    namelist = []
    for row in reslist :
        name = row[0]
        namelist.append(name.strip().lower())
        plr = database.findplayername(name)
        if (plr is None) :
            plr = database.findalt(name)
        while (plr is None or plr.pkey<0) :
            plr = player.Player(name,-1,1500,350,'city')
            window = Toplevel(window0)
            addplayerchallonge(plr,window,window0)
        result = player.Result(plr,tour,-1,row[1])
        database.addorupdateresult(result)
        resobjlist.append(result)
    for row in setlist :
        name1 = row[0].strip().lower()
        name2 = row[1].strip().lower()
        p1 = resobjlist[namelist.index(name1)].player
        p2 = resobjlist[namelist.index(name2)].player
        setti = player.Set(-1,p1,p2,tour,row[2],row[3],row[4])
        database.addset(setti)
    return 1

#Add a tournament using challonge.com API
def newtournamentchallonge(window00,window0,alltours,tree):
    if (challonge.apikey.strip()==""):
        challonge.getapikey()
        if (challonge.apikey.strip()=="") :
            messagebox.showinfo(message='No challonge API-key found. Please insert one into challongekey.dat and try again.',title='No API key')
            return 0
    window00.destroy()
    window=Toplevel(window0)
    window.title('Retrieve data from challonge.com')
    frame=ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0)
    
    tourkey=StringVar()
    urlstart='https://api.challonge.com/v1/tournaments/'
    ttk.Label(frame,text='Tournament key:').grid(row=1,column=1)
    Entry(frame,textvariable=tourkey).grid(row=1,column=2)
    ttk.Button(frame,text='Retrieve', command= lambda *args :challongetournament0(window,window0,alltours,tree,urlstart,tourkey.get())).grid(row=2,column=1,columnspan=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    
#Modify data of Challonge tournament
def challongetournament0(window00,window0,alltours,tree,urlstart,tourkeys) :
    window00.destroy()

    tourname = StringVar()
    startdates = StringVar()
    enddates = StringVar()
    city = StringVar()
    city.set('City')
    hits =challonge.getrequest(tourkeys,'json',urlstart)
    if (hits is None) :
        messagebox.showinfo(message='No tournament found or tournament is not complete?',title='Tournament error!')
        return 0
    (tournames,startdate,enddate,reslist,setlist)=hits
    tourname.set(tournames)
    startdates.set(startdate.strftime('%Y-%m-%d'))
    enddates.set(enddate.strftime('%Y-%m-%d'))

    window=Toplevel(window0)
    window.title('Retrieve data from challonge.com')
    frame=ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0)
    
    ttk.Label(frame, text='Tournament name: ').grid(row=1,column=1)
    ttk.Label(frame, text='Started (YYYY-MM-DD): ').grid(row=2,column=1)
    ttk.Label(frame, text='Ended: ').grid(row=3,column=1)
    ttk.Label(frame, text='City: ').grid(row=4,column=1)
    Entry(frame, textvariable=tourname).grid(row=1,column=2)
    Entry(frame, textvariable=startdates).grid(row=2,column=2)
    Entry(frame, textvariable=enddates).grid(row=3,column=2)
    Entry(frame, textvariable=city).grid(row=4,column=2)
    Button(frame, text='Proceed', command=lambda *args : challongetournament1(window,window0,alltours,tree,reslist,setlist,tourname.get(),startdates.get(),enddates.get(),city.get())).grid(row=5,column=1,columnspan=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


def challongetournament1(window00,window0,alltours,tree,reslist,setlist,tourname,startdates,enddates,city) :
    if (not (database.findtournamentbyname(tourname) is None)) :
        messagebox.showinfo(message='Tournament name taken!', title='Name taken')
        return 0
    try :
        if (stringtodate(startdates)>stringtodate(enddates)) :
            messagebox.showinfo(message='Tournament cannot start after its end', title='Check the dates')
            return 0
    except :
        print("Date formats wrong!")
        return 0
    if (city ==''):
        messagebox.showinfo(message='Please input city!', title='Write city')
        return 0
    
    tour = player.Tournament(tourname,-1,city,stringtodate(startdates),stringtodate(enddates),False)
    database.addorupdatetournament(tour)
    alltours.append(tour)
    tree.insert('','end',str(len(alltours)-1))
    tree.set(str(len(alltours)-1),'name',tour.name)
    tree.set(str(len(alltours)-1),'date',tour.startdate.strftime('%Y-%m-%d'))
    tree.set(str(len(alltours)-1),'evaluated',str(bool(tour.evaluated)))
    window00.destroy()
    
    challongetournament2(window0, reslist,setlist,tour)
    
#add players to challonge tournament
def challongetournament2(window0,reslist,setlist,tour) :
    indlist = []
    resobjlist = []
    for row in reslist :
        name = row[1]
        plr = database.findplayername(name)
        if (plr is None) :
            plr = database.findalt(name)
        while (plr is None or plr.pkey<0) :
            plr = player.Player(name,-1,1500,350,'city')
            window = Toplevel(window0)
            addplayerchallonge(plr,window,window0)
        indlist.append(row[0])
        result = player.Result(plr,tour,-1,row[2])
        database.addorupdateresult(result)
        resobjlist.append(result)
    for row in setlist :
        id1 = row[0]
        id2 = row[1]
        p1 = resobjlist[indlist.index(id1)].player
        p2 = resobjlist[indlist.index(id2)].player
        setti = player.Set(-1,p1,p2,tour,row[2],row[3],parseround(row[4]))
        database.addset(setti)
    return 1
    
    
def parseround(intti) :
    if (isinstance(intti,int)) :
        if (intti>0) :
            return('WR'+str(intti))
        elif(intti<0) :
            return('LR'+str(-intti))
    return ('?Round?'+str(randint(1,900)))


#Add player in challonge
def addplayerchallonge(plr,window,window0) :
    window.title('Player not found')
    frame = ttk.Frame(window,padding= "3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    
    name = StringVar()
    name.set(plr.name)
    city = StringVar()
    city.set(plr.city)
    skill = StringVar()
    skill.set(str(plr.skill))
    var = StringVar()
    var.set(str(plr.var))
    ttk.Label(frame,text='Name: ').grid(row=1,column=1)
    ttk.Label(frame,text='City: ').grid(row=2,column=1)
    ttk.Label(frame,text='Skill: ').grid(row=3,column=1)
    ttk.Label(frame,text='Variance: ').grid(row=4,column=1)
    Entry(frame,textvariable=name).grid(row=1,column=2)
    Entry(frame,textvariable=city).grid(row=2,column=2)
    Entry(frame,textvariable=skill).grid(row=3,column=2)
    Entry(frame,textvariable=var).grid(row=4,column=2)
    
    ttk.Button(frame,text='OK', command = lambda *args: addtheplayer2(name.get(),city.get(),skill.get(),var.get(),plr,window)).grid(row=5,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    window0.wait_window(window)

def addtheplayer2(names,citys,skills,varstr,plr,window) :
    try :
        skill = float(skills)
        var = float(varstr)
    except :
        print("Format error!")
        return 0
    plraux = database.findplayername(names)
    if (not (plraux is None)) :
        plr.set(plraux)
        window.destroy()
        return 1
    plr.city=citys
    plr.skill=skill
    plr.var=var
    plr.name=names
    database.addorupdateplayer(plr)
    window.destroy()
    return 1
    
    
#Create a new tournament entry
def addtournament(window0,alltournaments, tree) :
    window = Toplevel(window0)
    window.title('Add tournament')
    frame = ttk.Frame(window, padding = "3 3 3 3")
    frame.grid(row=0,column=0, sticky=(N,S,W,E))
    
    name = StringVar()
    name.set('Name')
    city = StringVar()
    city.set('Helsinki, FI')
    startdate = StringVar()
    startdate.set('2019-01-01')
    enddate = StringVar()
    enddate.set('2019-01-01')
    
    namel=ttk.Label(frame,text='Tournament name')
    namel.grid(row=1, column=1)
    cityl=ttk.Label(frame,text='Location')
    cityl.grid(row=2,column=1)
    startl= ttk.Label(frame, text='Start date YYYY-MM-DD')
    startl.grid(row=3, column=1)
    endl = ttk.Label(frame, text='End date YYYY-MM-DD')
    endl.grid(row=4, column=1)
    
    nameentry = ttk.Entry(frame,text = 'Name', textvariable = name)
    nameentry.grid(row=1, column=2)
    cityentry = ttk.Entry(frame,text = 'City', textvariable = city)
    cityentry.grid(row=2,column=2)
    startentry = ttk.Entry(frame,text='2019-01-01', textvariable=startdate)
    startentry.grid(row=3, column=2)
    endentry = ttk.Entry(frame,text ='2019-01-01', textvariable=enddate)
    endentry.grid(row=4, column=2)
    
    tourbutt = ttk.Button(frame, text='Add!', command = lambda *args: createtournament(window,name,city,startdate,enddate,alltournaments,tree))
    tourbutt.grid(row=5, column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


#Adds the tournament entry
def createtournament(window,name, city, startdates, enddates,alltournaments, tree) :
    try :
        startdate = datetime.datetime.strptime(startdates.get(),'%Y-%m-%d')
        enddate = datetime.datetime.strptime(enddates.get(),'%Y-%m-%d')
    except :
        print("error! Date format not correct")
        return 0
    if ((enddate-startdate).total_seconds()<0) :
        print("Error! Start cannot be after end!")
        return 0
    if (not (database.findtournamentbyname(name.get()) is None)) :
        print("Error! Name already taken!")
        return 0
    
    tour = player.Tournament(name.get(),-1,city.get(),startdate,enddate, False)
    database.addorupdatetournament(tour)
    window.destroy()
    alltournaments.append(tour)
    ind = str(len(alltournaments)-1)
    tree.insert('','end',ind)
    tree.set(ind,'name',tour.name)
    tree.set(ind,'date',datetime.datetime.strftime(tour.startdate,'%Y-%m-%d'))
    tree.set(ind,'evaluated',str(tour.evaluated))
    return 1

#Open sets and results for a tournaments
def opentournamentwindow(window0, tour) :
    window = Toplevel(window0)
    window.title(tour.name)
    setlist = database.findallsetsfortournament(tour)
    playerlist = database.findresults(tour)
    frame = ttk.Frame(window, padding = "3 3 3 3")
    frame.grid(row=0,column=0,sticky= (N,S, W, E))
    
    treeset = ttk.Treeview(frame, columns = ('p1','p2','score','desc'))
    treeset['show']='headings'
    treeset.heading('score',text='Score')
    treeset.heading('desc', text='Phase')
    treeset.grid(row=1, column=1, columnspan=2)
    treeset.column('score',width=50)
    treeset.column('p1',width=90)
    treeset.column('p2',width=90)
    treeset.column('desc',width=60)
    
    for ind in range(len(setlist)) :
        treeset.insert('','end',str(ind))
        treeset.set(str(ind),'p1',setlist[ind].player1.name)
        treeset.set(str(ind),'p2',setlist[ind].player2.name)
        treeset.set(str(ind),'score',str(setlist[ind].score1)+"-"+str(setlist[ind].score2))
        treeset.set(str(ind),'desc',setlist[ind].description)
    treeset.bind('<Double-1>', lambda *args : opensetwin(setlist[int(treeset.selection()[0])],setlist,treeset,window))
    
    treepl = ttk.Treeview(frame, columns = ('name','pl'))
    treepl['show']='headings'
    treepl.heading('name',text='Name')
    treepl.heading('pl',text='Placement')
    treepl.grid(row=1, column=3,columnspan=2)
    treepl.column('pl',width=80)
    treepl.column('name',width=120)
    
    for ind in range(len(playerlist)) :
        treepl.insert('','end',str(ind))
        treepl.set(str(ind),'name',playerlist[ind].player.name)
        treepl.set(str(ind),'pl',playerlist[ind].placement)
    treepl.bind('<Double-1>', lambda *args : openresultwin(window, playerlist[int(treepl.selection()[0])],treepl,playerlist))
    
    addsetbutt = ttk.Button(frame,text='Add a set!', command = lambda *args : addsetwindow(window,setlist,playerlist,treeset,tour))
    delsetbutt = ttk.Button(frame,text='Delete this set!', command = lambda *args : deleteset(setlist[int(treeset.selection()[0])],setlist,treeset))
    addresbutt = ttk.Button(frame,text='Add a player!', command = lambda *args : addreswindow(window,playerlist,tour,treepl))
    delresbutt = ttk.Button(frame,text='Delete this result!', command = lambda *args : delreswindow(window,playerlist[int(treepl.selection()[0])],playerlist,treepl))
    addsetbutt.grid(row=2, column=1)
    addresbutt.grid(row=2, column=3)
    delsetbutt.grid(row=2, column=2)
    delresbutt.grid(row=2, column=4)
    
    evaluatetourbutton = ttk.Button(frame, text='Evaluate this tournament', command= lambda *args: updateprocedure(tour))
    evaluatetourbutton.grid(row=3, column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


#Evaluate tournament and compute glicko changes    
def updateprocedure(tournament) :
    #Check if tournament sets should be evaluated!
    if (tournament.evaluated==True) :
        messagebox.showinfo(message='Tournament already evaluated!')
        return 0
    playerlist = database.findplayerstournament(tournament)
    for row in playerlist :
        if (row.lasttime > tournament.enddate) :
            answer = messagebox.askyesno(message='Tournament seems to be old! Do you want to proceed?',icon='question',title='Warning! Old tournament?')
            if (answer == False) :
                return 0
            else :
                break
    #All ok! Let's go!
    try :
        updatelist = []
        for plyr in playerlist :
            setlist = database.findsetstournamentplayer(tournament,plyr)
            (rate,rd) = glicko.newratings(plyr, setlist)
            updatelist.append((plyr,rate,rd,))
        for entry in updatelist:
            entry[0].updateskill(entry[1],entry[2],tournament.enddate)
        tournament.evaluated=True
        #Insert (hidden or not?) procedure
        database.addorupdatetournament(tournament)
        for plyr in playerlist :
            database.addorupdateplayer(plyr)
        return 1
    except Exception as e :
        print(str(e))
        print("Error in glicko evaluation!")
        return 0
    
#Look and edit set score
def opensetwin(setti,setlist,tree,window0) :
    window = Toplevel(window0)
    window.title(setti.player1.name + " vs. " + setti.player2.name +" at " +setti.tournament.name)
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0, sticky=(N,S,W,E))
    
    s1=StringVar()
    s1.set(str(setti.score1))
    s2=StringVar()
    s2.set(str(setti.score2))
    phase = StringVar()
    phase.set(setti.description)
    ttk.Label(frame,text=setti.player1.name).grid(row=1,column=2)
    ttk.Label(frame,text=setti.player2.name).grid(row=1,column=3)
    s1entry = Entry(frame, textvariable=s1)
    s1entry.grid(row=2,column=2)
    s2entry=Entry(frame, textvariable=s2)
    s2entry.grid(row=2,column=3)
    ttk.Label(frame, text='P1 score').grid(row=2,column=1)
    ttk.Label(frame, text='P2 score').grid(row=2, column=4)
    ttk.Label(frame, text='Phase: ').grid(row=3, column=2)
    Entry(frame, textvariable=phase).grid(row=3,column=3)
    ttk.Button(frame,text='Modify set', command = lambda *args: changeset(setti,setlist,tree,window,s1.get(),s2.get(),phase.get())).grid(row=4,column=1)
    ttk.Button(frame,text='Delete set', command = lambda *args:deleteset(setti,setlist,tree,window)).grid(row=4,column=3)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Makes the changes in set
def changeset(setti,setlist,tree,window,s1s,s2s,phase) :
    try :
        s1 = int(s1s)
        s2 = int(s2s)
        ind=setlist.index(setti)
        setti.score1=s1
        setti.score2=s2
        setti.description=phase
        tree.set(str(ind),'desc',phase)
        tree.set(str(ind),'score',str(s1) + "-" + str(s2))
        database.updateset(setti)
        window.destroy()
    except:
        print("Error in changeset!")
        return 0

#Command for deleting set
def deleteset(setti, setlist,tree,window=None) :
    answer=messagebox.askyesno(message='Are you sure you wish to delete this set?',icon='question',title='Delete set?')
    if (answer == True):
        ind = setlist.index(setti)
        database.deleteset(setti)
        setlist.remove(setti)
        tree.delete(str(ind))
        if (window is None) :
            return 1
        else :
            window.destroy()
            return 1
    return 0

#Look and edit result of a player
def openresultwin(window0, result, tree,playerlist) :
    window = Toplevel(window0)
    window.title(result.player.name + " at " + result.tournament.name)
    frame = ttk.Frame(window, padding = "3 3 3 3")
    frame.grid(row=0, column=0,sticky=(N,S,W,E))
    ttk.Label(frame,text='Name :').grid(row=1,column=1)
    ttk.Label(frame,text=result.player.name).grid(row=1,column=2)
    pl = StringVar()
    pl.set(str(result.placement))
    plentry = ttk.Entry(frame,textvariable=pl)
    plentry.grid(row=2,column=2)
    ttk.Label(frame,text='Placement: ').grid(row=2,column=1)
    
    okbutt = ttk.Button(frame, text='OK', command = lambda *args: changeresult(result,pl.get(),window,tree,playerlist))
    okbutt.grid(row=3,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    
#command to change result
def changeresult(result,placement,window,tree,playerlist) :
    try :
        pl = int(placement)
        ind = playerlist.index(result)
        result.placement=pl
        database.addorupdateresult(result)
        tree.set(str(ind),'pl',placement)
        window.destroy()
        return 1
    except :
        print("Error")
        return 0

#Procedure to add a set to a tournament
def addsetwindow(window0,setlist, playerlist, tree, tournament) :
    if (tournament.evaluated == True):
        answer = messagebox.askyesno(message='Tournament has already been evaluated. Are you sure you want to add new sets?',icon='question',title='Warning!')
        if (answer == False):
            return 0
    window = Toplevel(window0)
    window.title('Add a set')
    frame = ttk.Frame(window, padding = "3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    p1 = StringVar()
    p2 = StringVar()
    s1 = StringVar()
    s2 = StringVar()
    phase = StringVar()
    
    p1entry = ttk.Entry(frame, textvariable = p1)
    p1entry.grid(row=1, column=2)
    p2entry= ttk.Entry(frame, textvariable = p2)
    p2entry.grid(row=1,column=3)
    ttk.Label(frame, text='P1 name').grid(row=1,column=1)
    ttk.Label(frame, text='P2 name').grid(row=1,column=4)
    s1entry= ttk.Entry(frame, textvariable = s1)
    s1entry.grid(row=2,column=2)
    ttk.Label(frame, text='P1 score').grid(row=2,column=1)
    s2entry= ttk.Entry(frame, textvariable = s2)
    s2entry.grid(row=2,column=3)
    ttk.Label(frame, text='P2 score').grid(row=2,column=4)
    phaseentry= ttk.Entry(frame, textvariable = phase)
    phaseentry.grid(row=3, column = 2)
    
    ttk.Label(frame, text='Phase: ').grid(row=3,column=1)
    p1entry.focus()
    window.bind('<Return>',lambda *args : addsetbutton(window, setlist,playerlist,tree, tournament,p1.get(),p2.get(),s1.get(),s2.get(),phase.get()))
    ttk.Button(frame, text='Add set', command= lambda *args : addsetbutton(window, setlist,playerlist,tree, tournament,p1.get(),p2.get(),s1.get(),s2.get(),phase.get())).grid(row=4,column=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


#Command to add the set to a tournament
def addsetbutton(window, setlist, playerlist, tree, tournament,*setaux) :
    p1o=next((x for x in playerlist if x.player.name.strip().lower()==setaux[0].strip().lower()),None).player
    p2o=next((x for x in playerlist if x.player.name.strip().lower()==setaux[1].strip().lower()),None).player
    if (p1o is None or p2o is None) :
        messagebox.showinfo(message='One or more player not found in player list!')
        return 0
    if (p1o==p2o) :
        messagebox.showinfo(message='Players cannot be the same')
        return 0
    try :
        s1 = int(setaux[2])
        s2 = int(setaux[3])
        if (s1 == s2):
            messagebox.showinfo(message='Scores have to be different')
            return 0
    except :
        return 0
    setti = player.Set(-1, p1o,p2o,tournament,s1,s2,setaux[4])
    if (not (database.findset(setti) is None)) :
        messagebox.showinfo(message='Set is already in database')
        return 0
    database.addset(setti)
    setlist.append(setti)
    tree.insert('','end',str(len(setlist)-1))
    tree.set(str(len(setlist)-1),'p1',setti.player1.name)
    tree.set(str(len(setlist)-1),'p2',setti.player2.name)
    tree.set(str(len(setlist)-1),'score',str(setti.score1) + "-" + str(setti.score2))
    tree.set(str(len(setlist)-1),'desc',setti.description)
    window.destroy()

#Procedure to add a result/player to tournament
def addreswindow(window0,reslist, tournament,tree) :
    window = Toplevel(window0)
    window.title('Add result')
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0, sticky = (N,S,W,E))
    
    name = StringVar()
    placement = StringVar()
    name.set('Name')
    nameentry = ttk.Entry(frame,textvariable=name)
    placemententry = ttk.Entry(frame, textvariable = placement)
    nameentry.grid(row=1, column=2)
    placemententry.grid(row=2, column=2)
    namel = ttk.Label(frame, text = 'Name:')
    placementl = ttk.Label(frame, text = 'Placement')
    namel.grid(row=1, column=1)
    placementl.grid(row=2, column=1)
    
    addbutt = ttk.Button(frame,text='Add result', command = lambda *args : addresult(name.get(), placement.get(), reslist,tournament, window,tree))
    addbutt.grid(row=3, column=1)
    cancelbutt = ttk.Button(frame, text='Cancel', command = lambda *args : closewindow(window))
    nameentry.focus()
    window.bind('<Return>',lambda *args : addresult(name.get(),placement.get(),reslist,tournament,window,tree))
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


#Command to add player/result to tournament
def addresult(name, placement, reslist,tournament, window,tree) :
    if (tournament.evaluated == True) :
        answer = messagebox.askyesno(message='Tournament has already been evaluated. Are you sure you want to add new results?',icon='question',title='Warning!')
        if (answer == False) :
            return 0
    plr=database.findplayername(name)
    auxvar = IntVar()
    auxvar.set(0)
    if (plr is None) :
        plr = database.findalt(name)
    while (plr is None or plr.name=='') :
        print("Player not found!")
        answer = messagebox.askyesno(message='Player name not found? Add this player?',icon='question',title='Add player?')
        if(answer == True) :
            plr = addplayerres(window, name)
        else :
            return 0
    try :
        placementi = int(placement)
    except :
        placementi = 0
    result = player.Result(plr,tournament,-1,placementi)
    if (not (database.findresult(plr,tournament) is None)) :
        messagebox.showinfo(message='Player already has a result!')
        return 0
    database.addorupdateresult(result)
    reslist.append(result)
    tree.insert('','end',str(len(reslist)-1))
    tree.set(str(len(reslist)-1),'name',result.player.name)
    tree.set(str(len(reslist)-1),'pl',result.placement)
    window.destroy()
    return 1

#Adds a player to database
def addplayerres(window0,name='Name') :
    window = Toplevel(window0)
    
    window.title('Add player')
    frame = ttk.Frame(window, padding = "3 3 3 3")
    frame.grid(row=0,column=0, sticky= (N,S,W,E))
    
    namev = StringVar()
    namev.set(name)
    skill = StringVar()
    skill.set('1500')
    var = StringVar()
    var.set('350')
    city = StringVar()
    city.set('City')
    lasttime = StringVar()
    lasttime.set(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'))
    
    nameentry = ttk.Entry(frame,textvariable = namev)
    namel = Label(frame, text = 'Name')
    nameentry.grid(row=1,column=2)
    namel.grid(row=1,column=1)
    skillentry = ttk.Entry(frame, textvariable = skill)
    skilll = Label(frame, text = 'Skill')
    skillentry.grid(row=2,column=2)
    skilll.grid(row=2,column=1)
    varentry = ttk.Entry(frame, textvariable = var)
    varl = Label(frame,text = 'Skill variance')
    varentry.grid(row=3, column=2)
    varl.grid(row=3, column=1)
    cityentry = ttk.Entry(frame, textvariable = city)
    cityl = Label(frame, text = 'City')
    cityentry.grid(row=4, column=2)
    cityl.grid(row=4, column=1)
    lasttimeentry = ttk.Entry(frame, textvariable = lasttime)
    lasttimel = Label(frame, text='Last time seen YYYY-MM-DD')
    lasttimeentry.grid(row=5,column=2)
    lasttimel.grid(row=5,column=1)
    
    plr = player.Player('',-1,1500,350,'')
    addbutt = ttk.Button(frame, text = 'Add', command = lambda *args : addtheplayer(namev.get(),skill.get(),var.get(),city.get(),lasttime.get(),window, plr))
    addbutt.grid(row=6,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    window0.wait_window(window)
    return plr

#Adds the result/player to database
def addtheplayer(name,skill,var,city,lasttime, window,plr) :
    lasttimed = datetime.datetime.strptime(lasttime,'%Y-%m-%d')
    try :
        if (name != '' and (database.findplayername(name) is None) and (database.findalt(name) is None)) :
            skilli = int(skill)
            vari = int(var)
            lasttimed = datetime.datetime.strptime(lasttime,'%Y-%m-%d')
            player1 = player.Player(name, -1, skilli, vari, city, lasttimed)
            database.addorupdateplayer(player1)
            window.destroy()
            plr.set(player1)
    except ValueError:
        print("ValueError")
    except NameError:
        print("NameError")
    except TypeError:
        print("TypeError")
    except UnicodeError:
        print("UnicodeError")
    except :
        print('Wrong format or player name already taken or sth. idc')

#Deleting a result
def delreswindow(window0, result, reslist,tree) :
    try :
        answer = messagebox.askyesno(message='Are you sure you wish to delete this result?',icon='question',title='Delete result?')
        if (len(database.findsetstournamentplayer(result.tournament,result.player))>0 and answer == True) :
            messagebox.showinfo(message='Delete corresponding sets first!')
            return 0
        if (answer == True) :
            ind = reslist.index(result)
            reslist.remove(result)
            database.deleteresult(result)
            for i in range(ind,len(reslist)) :
                tree.delete(str(i))
                tree.insert('','end',str(i))
                tree.set(str(i),'name',reslist[i].player.name)
                tree.set(str(i),'pl',reslist[i].placement)
            tree.delete(str(len(reslist)))
            return 1
    except :
        print("No set selected!")
    return 0

#
# Tournament branch ends
#
# H2H sets branch begins!!
#

def setswin() :
    global setswinopen
    if (setswinopen == True) :
        return 0
    window = Toplevel(root)
    window.title('H2H sets')
    setswinopen = True
    window.protocol("WM_DELETE_WINDOW", lambda *args : closewindow(window))
    frame = ttk.Frame(window,padding = "3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    
    n=6
    datestring=(datetime.datetime.now()-datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    name1=StringVar()
    name2=StringVar()
    lastsets = StringVar()
    lastsets.set(str(n))
    pasttimemonths = StringVar()
    ttk.Label(frame,text='P1 name').grid(row=1,column=1)
    Entry(frame,textvariable=name1).grid(row=1,column=2)
    Entry(frame,textvariable=name2).grid(row=1,column=3)
    ttk.Label(frame,text='P2 name').grid(row=1,column=4)
    ttk.Label(frame,text='Compare past x sets: ' ).grid(row=2,column=2)
    Entry(frame,textvariable=lastsets).grid(row=2,column=3)
    ttk.Label(frame,text='Compare past x months or since (YYYY-MM-DD) ').grid(row=3,column=1,columnspan=2)
    Entry(frame,textvariable=pasttimemonths).grid(row=3,column=3)
    Button(frame,text='Generate',command = lambda *args: generatesetdata(name1.get(),name2.get(),lastsets.get(),pasttimemonths.get(),alltimelabel,pastxsetslabel,sincelabel),height=4).grid(row=2,column=4,rowspan=2)
    alltimelabel=ttk.Label(frame,text = 'All time set results: ')
    alltimelabel.grid(row=4,column=2)
    pastxsetslabel =ttk.Label(frame,text = 'Past ' + lastsets.get() + ' sets: ')
    pastxsetslabel.grid(row=5,column=2)
    sincelabel =ttk.Label(frame, text = 'Sets since '+datestring +': ')
    sincelabel.grid(row=6,column=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)


def generatesetdata(name1,name2,lastsets,pasttimemonths,alltimelabel,pastxsetslabel,sincelabel) :
    alltimelabel['text'] = 'All time set results: '
    pastxsetslabel['text'] = 'Past ' +'X' + ' sets: '
    sincelabel['text'] = 'Sets since ' +'X' + ' months: '
    plr1=database.findplayername(name1)
    if (plr1 is None):
        plr1 = database.findalt(name1)
        if (plr1 is None) :
            return 0
    plr2=database.findplayername(name2)
    if (plr2 is None):
        plr2 = database.findalt(name2)
        if (plr2 is None) :
            return 0
    setlist = database.findsetsbetween(plr1,plr2).copy()
    setlist.sort(key = lambda x : x.tournament.startdate,reverse=True)
    for setti in setlist :
        if (setti.player2==plr1) :
            setti.player1 == plr1
            setti.player2 == plr2
            aux = setti.score1
            setti.score1 == setti.score2
            setti.score2 == aux
    allscore1 = 0
    allscore2 = 0
    pastscore=''
    sincescore=''
    try : 
        n = int(lastsets)
    except :
        n = None
    try :
        monthsi = int(pasttimemonths)
        datelimit = datetime.datetime.now()-relativedelta(months=monthsi)
    except :
        monthsi = None
        try :
            datelimit = stringtodate(pasttimemonths)
        except :
            datelimit = None

    auxind = 0
    length=len(setlist)
    for setti in setlist :
        auxind = auxind+1

        if ((not (n is None))) :
            if (auxind > n) :
                pastscore = str(allscore1) + '-' + str(allscore2)
                pastxsetslabel['text'] = 'Past ' + str(n) + ' sets: ' + pastscore
                n = None
        if (not (datelimit is None)) :
            if (setti.tournament.enddate < datelimit) :
                sincescore = str(allscore1) + '-' + str(allscore2)
                if (monthsi is None) :
                    sincelabel['text']='Sets since ' +datelimit + ': ' + sincescore
                else :
                    sincelabel['text']='Sets during past ' + str(monthsi) +' months: '+ sincescore
                datelimit = None
        if (setti.winner() == plr1) :
            allscore1 = allscore1+1
        elif (setti.winner() == plr2) :
            allscore2 = allscore2+1
    if (auxind == length) :
        if ((not (n is None))) :
                pastscore = str(allscore1) + '-' + str(allscore2)
                pastxsetslabel['text'] = 'Past ' + str(n) + ' sets: ' + pastscore
        if (not (datelimit is None)) :
            sincescore = str(allscore1) + '-' + str(allscore2)
            if (monthsi is None) :
                sincelabel['text']='Sets since ' +datelimit + ': ' + sincescore
            else :
                sincelabel['text']='Sets during past ' + str(monthsi) +' months: '+ sincescore

    alltimelabel['text'] = 'All time set results: ' + str(allscore1)+'-'+str(allscore2)
    
#
# Set branch ends
#
# Player branch begins!!
#

#List players in database alphabetically. Proceed to rankings,
#look at player stats, results etc.
def playerwin() :
    global playerwinopen
    if (playerwinopen == True) :
        return 0
    window = Toplevel(root)
    window.title('Players')
    playerwinopen = True
    window.protocol("WM_DELETE_WINDOW", lambda *args : closewindow(window))
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0, column=0,sticky=(N,S,W,E))
    
    treepl = ttk.Treeview(frame,columns=('name','skill','var','city','lastseen','ranked'),height=25)
    treepl.grid(row=1,column=1,columnspan=2)
    treepl['show']='headings'
    treepl.heading('name',text='Name')
    treepl.heading('skill',text='Avg. skill')
    treepl.heading('var',text='Deviation')
    treepl.heading('city',text='City')
    treepl.heading('lastseen',text='Last appearance')
    treepl.heading('ranked',text='Ranked')
    treepl.column('name',width=120)
    treepl.column('ranked',width=60)
    treepl.column('city',width=90)
    treepl.column('skill',width=80)
    treepl.column('var',width=80)
    treepl.column('lastseen',width=100)
    
    playerlist=database.findallplayers()
    playerlist.sort(key = lambda x:x.name.lower())
    for ind in range(len(playerlist)):
        treepl.insert('','end',str(ind))
        treepl.set(str(ind),'name',playerlist[ind].name)
        treepl.set(str(ind),'skill',str("%.1f"%playerlist[ind].skill))
        treepl.set(str(ind),'var',str("%.1f"%playerlist[ind].var))
        treepl.set(str(ind),'city',playerlist[ind].city)
        treepl.set(str(ind),'lastseen',datetime.datetime.strftime(playerlist[ind].lasttime,'%Y-%m-%d'))
        treepl.set(str(ind),'ranked',str(not playerlist[ind].hidden))
    treepl.bind('<Double-1>',lambda *args: openplayerplayerwin(window,playerlist[int(treepl.selection()[0])],playerlist,treepl))
    
    Button(frame,text='Add player!', command=lambda *args: addplayer(window,playerlist,treepl)).grid(row=2,column=1)
    Button(frame,text='See rankings!', command = lambda *args:rankings(window,playerlist)).grid(row=2,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    return 1

#Look at the current rankings
def rankings(window0,playerlist) :
    window=Toplevel(window0)
    window.title('Rankings')
    newlist = [plr for plr in playerlist if plr.hidden == False]
    newlist.sort(key = lambda x: x.skill-2*x.var, reverse=True )
    
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    tree = ttk.Treeview(frame,columns=('rank','name','realskill','skill','var','city'),height=25)
    tree['show']='headings'
    tree.grid(row=1,column=1,sticky=(N,S,W,E))
    tree.heading('name',text='Name')
    tree.heading('realskill',text='Real skill')
    tree.heading('skill',text='Avg. skill')
    tree.heading('var',text='Skill dev.')
    tree.heading('city',text='City')
    tree.heading('rank',text='Rank')
    tree.column('name',width=100)
    tree.column('rank',width=50)
    tree.column('realskill',width=100)
    tree.column('skill',width=60)
    tree.column('var',width=70)
    tree.column('city',width=100)
    
    for ind in range(len(newlist)) :
        tree.insert('','end',str(ind))
        tree.set(str(ind),'rank',str(ind+1))
        tree.set(str(ind),'name',newlist[ind].name)
        tree.set(str(ind),'realskill',str("%.1f"%(newlist[ind].skill-2*newlist[ind].var)))
        tree.set(str(ind),'skill',str("%.1f"%newlist[ind].skill))
        tree.set(str(ind),'var',str("%.1f"%glicko.RD(newlist[ind],datetime.datetime.now())))
        tree.set(str(ind),'city',newlist[ind].city)
    tree.bind('<Double-1>', lambda *args:openplayerrankwin(window, newlist[int(tree.selection()[0])],int(tree.selection()[0])))
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Look at the ranked player's stats
def openplayerrankwin(window0, plr,rank):
    window = Toplevel(window0)
    window.title('Stats for ' + plr.name)
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    
    ttk.Label(frame, text = 'Name: ').grid(row=1,column=1)
    ttk.Label(frame, text=plr.name).grid(row=1,column=2)
    ttk.Label(frame, text = '(Skill, variance):').grid(row=2,column=1)
    ttk.Label(frame, text = '('+str("%.1f"%plr.skill)+','+str("%.1f"%glicko.RD(plr,datetime.datetime.now()))+')').grid(row=2,column=2)
    ttk.Label(frame, text = 'Rank: '+ str(rank)).grid(row=3,column=1)
    ttk.Label(frame, text = 'Real skill: '+str("%.1f"%(plr.skill-2*glicko.RD(plr,datetime.datetime.now())))).grid(row=3,column=2)
    ttk.Label(frame, text = 'City: ').grid(row=4,column=1)
    ttk.Label(frame, text=plr.city).grid(row=4,column=2) 
    ttk.Label(frame, text = 'Last seen: ').grid(row=5,column=1)
    ttk.Label(frame, text = datetime.datetime.strftime(plr.lasttime,'%Y-%m-%d')).grid(row=5,column=2)

    Button(frame,text='See tournament results', command = lambda *args: playertournaments(window, plr)).grid(row=6,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Look and modify player stats
def openplayerplayerwin(window0, plr,playerlist,tree):
    window = Toplevel(window0)
    window.title('Stats for ' + plr.name)
    frame = ttk.Frame(window,padding="3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    
    name = StringVar()
    name.set(plr.name)
    city = StringVar()
    city.set(plr.city)
    hidden=IntVar()
    hidden.set(int(plr.hidden))
    
    ttk.Label(frame, text = 'Name: ').grid(row=1,column=1)
    Entry(frame, textvariable=name).grid(row=1,column=2)
    ttk.Label(frame, text = '(Skill, variance):').grid(row=2,column=1)
    ttk.Label(frame, text = '('+str("%.1f"%plr.skill)+','+str("%.1f"%glicko.RD(plr,datetime.datetime.now()))+')').grid(row=2,column=2)
    ttk.Label(frame, text = 'City: ').grid(row=3,column=1)
    Entry(frame, textvariable=city).grid(row=3,column=2) 
    ttk.Label(frame, text = 'Last seen: ').grid(row=4,column=1)
    ttk.Label(frame, text = datetime.datetime.strftime(plr.lasttime,'%Y-%m-%d')).grid(row=4,column=2)
    ttk.Label(frame, text = 'Hidden: ').grid(row=5,column=1)
    Checkbutton(frame, variable=hidden).grid(row=5,column=2)
    if (len(plr.alts)>0) :
        altlist = '; '.join(plr.alts)
        ttk.Label(frame, text='Alt names: ' + altlist).grid(row=6,column=1,columnspan=2)
        
    Button(frame,text='See tournament results', command = lambda *args: playertournaments(window, plr)).grid(row=8,column=1)
    Button(frame,text='Add alt names', command = lambda *args :addaltwin(window,plr)).grid(row=8,column=2)
    Button(frame,text='Delete player', command = lambda *args :deleteplayer(plr,tree,playerlist,window)).grid(row=7,column=1)
    Button(frame,text='Modify info',command= lambda *args: modifyplayerinfo(name.get(),city.get(),hidden.get(),plr,playerlist,tree,window)).grid(row=7,column=2)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Window for adding alt names
def addaltwin(window0,plr) :
    window=Toplevel(window0)
    window.title('Add alt name for ' + plr.name)
    frame = ttk.Frame(window,padding = "3 3 3 3")
    frame.grid(row=0,column=0,sticky=(N,S,W,E))
    altname=StringVar()
    ttk.Label(frame,text='Alt name: ').grid(row=1,column=1)
    Entry(frame,textvariable=altname).grid(row=1,column=2)
    Button(frame,text='Add!', command = lambda *args :addthealt(window,plr,altname.get())).grid(row=2,column=1)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Does the adding of alt name
def addthealt(window,plr,altname) :
    if (plr.addalt(altname) == 0) :
        return 0
    window.destroy()
    

#Look at tournament results of a player
def playertournaments(window0,plr) :
    window = Toplevel(window0)
    window.title('Tournament results of ' + plr.name)
    frame = ttk.Frame(window,padding = "3 3 3 3")
    frame.grid(row=0,column=0, sticky= (N,S,W,E))
    
    resultslist = database.findresultplayer(plr)
    if (len(resultslist)>0):
        resultslist.sort(key = lambda res : res.tournament.enddate)
    tree = ttk.Treeview(frame,columns=('tour','date','placement'))
    tree.grid(row=1,column=1)
    tree['show']='headings'
    tree.heading('tour',text='Tournament')
    tree.heading('date',text='Date')
    tree.heading('placement',text='Placement')
    tree.column('tour', width=240)
    tree.column('date',width=100)
    tree.column('placement',width=110)
    
    for ind in range(len(resultslist)) :
        tree.insert('','end',str(ind))
        tree.set(str(ind),'tour',resultslist[ind].tournament.name)
        tree.set(str(ind),'date',datetime.datetime.strftime(resultslist[ind].tournament.startdate,'%Y-%m-%d'))
        tree.set(str(ind),'placement',str(resultslist[ind].placement))
    tree.bind('<Double-1>', lambda *args : playerattournamentwin(plr,resultslist[int(tree.selection()[0])].tournament,window))
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Look at the sets at a tournament (of a player)
def playerattournamentwin(plr,tournament,window0) :
    window = Toplevel(window0)
    window.title('Sets of ' +plr.name+' at '+tournament.name)
    setlist = database.findsetstournamentplayer(tournament,plr)
    setlist.sort(key = lambda x: x.description)
    frame = ttk.Frame(window,padding = "3 3 3 3")
    frame.grid(row=0,column=0)
    tree = ttk.Treeview(frame, columns=('p1','p2','score','desc'))
    tree.grid(row=1,column=1)
    tree['show']='headings'
    tree.heading('p1',text='P1')
    tree.heading('p2',text='P2')
    tree.heading('score',text='Score')
    tree.heading('desc',text='Phase')
    tree.column('p1',width=100)
    tree.column('p2',width=100)
    tree.column('score',width=70)
    tree.column('desc',width=80)
    
    for ind in range(len(setlist)) :
        tree.insert('','end',str(ind))
        tree.set(str(ind),'p1',setlist[ind].player1.name)
        tree.set(str(ind),'p2',setlist[ind].player2.name)
        tree.set(str(ind),'score',str(setlist[ind].score1)+"-"+str(setlist[ind].score2))
        tree.set(str(ind),'desc',setlist[ind].description)
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)

#Modify the player info
def modifyplayerinfo(name,city,hiddeni,plr,playerlist,tree,window0) :
    if (name == '') :
        print("Name cannot be blank")
        return 0
    if (name.strip().lower() != plr.name.strip().lower()) :
        paux = database.findalt(name) 
        if (not (database.findplayername(name) is None )) :
            print("Name is reserved!")
            messagebox.showinfo(message='Name already taken!')
            return 0
        if (not (paux is None) ):
            if (paux.name != name) :
                print("Name is reserved!")
                messagebox.showinfo(message='Name already taken!')
                return 0
    ind=playerlist.index(plr)
    plr.name = name
    plr.city = city
    plr.hidden = bool(hiddeni)
    database.addorupdateplayer(plr)
    tree.set(str(ind),'name',name)
    tree.set(str(ind),'city',city)
    tree.set(str(ind),'ranked',str(not plr.hidden))
    window0.destroy()
    return 1

#Procedure to delete player from database (must not have results)
def deleteplayer(plr,tree,playerlist, window0) :
    answer = messagebox.askyesno(message='Are you sure you want to delete player: ' + plr.name + '?',title='Delete ' + plr.name +'?',icon='question' )
    if (answer == False) :
        return 0
    if (len(database.findresultplayer(plr))>0) :
        messagebox.showinfo(message='Cannot delete player. Delete corresponding results first!')
        return 0
    ind = playerlist.index(plr)
    del(playerlist[ind])
    for i in range(ind,len(playerlist)) :
        tree.delete(str(i))
        tree.insert('','end',str(i))
        tree.set(str(i),'name',playerlist[i].name)
        tree.set(str(i),'city',playerlist[i].city)
        tree.set(str(i),'ranked',str(bool(playerlist[i].ranked)))
        tree.set(str(i),'skill',str(playerlist[i].skill))
        tree.set(str(i),'var',str(playerlist[i].var))
        tree.set(str(i),'lastseen',playerlist[i].lasttime.strftime())
    tree.delete(str(len(playerlist)))
    database.deleteplayer(plr)
    window0.destroy()
    return 1

#Procedure to add new player to database
def addplayer(window0,lista,tree) :
    window = Toplevel(window0)
    window.title('Add a player')
    frame = ttk.Frame(window, padding="3 3 3 3")
    frame.grid(row=0,column=0, sticky=(N,S,W,E))
    
    namev = StringVar()
    namev.set('Name')
    skill = StringVar()
    skill.set('1500')
    var = StringVar()
    var.set('350')
    city = StringVar()
    city.set('City')
    lasttime = StringVar()
    lasttime.set(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d'))
    
    nameentry = ttk.Entry(frame,textvariable = namev)
    namel = Label(frame, text = 'Name')
    nameentry.grid(row=1,column=2)
    namel.grid(row=1,column=1)
    skillentry = ttk.Entry(frame, textvariable = skill)
    skilll = Label(frame, text = 'Skill')
    skillentry.grid(row=2,column=2)
    skilll.grid(row=2,column=1)
    varentry = ttk.Entry(frame, textvariable = var)
    varl = Label(frame,text = 'Skill variance')
    varentry.grid(row=3, column=2)
    varl.grid(row=3, column=1)
    cityentry = ttk.Entry(frame, textvariable = city)
    cityl = Label(frame, text = 'City')
    cityentry.grid(row=4, column=2)
    cityl.grid(row=4, column=1)
    lasttimeentry = ttk.Entry(frame, textvariable = lasttime)
    lasttimel = Label(frame, text='Last time seen YYYY-MM-DD')
    lasttimeentry.grid(row=5,column=2)
    lasttimel.grid(row=5,column=1)
    
    plr = player.Player('',-1,1500,350,'')
    addbutt = ttk.Button(frame, text = 'Add', command = lambda *args : addplayerbutton(namev.get(),skill.get(),var.get(),city.get(),lasttime.get(),window, plr,tree,lista))
    window.bind('<Return>',lambda *args : addplayerbutton(namev.get(),skill.get(),var.get(),city.get(),lasttime.get(),window, plr,tree,lista))
    addbutt.grid(row=6,column=1)
    nameentry.focus()
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)
    
#Adds the player to database
def addplayerbutton(name,skills,varstr,city,lasttimes,window0,plr,tree, playerlist) :
    plr1 = database.findplayername(name)
    if (not(plr1 is None)) :
        messagebox.showinfo(message='Player name already taken!')
        return 0
    if (not(database.findalt(name) is None)):
        messagebox.showinfo(message='Player name already taken!')
        return 0
    while (plr1 is None and name != '') :
        try:
            skill = int(skills)
            var = int(varstr)
            lasttime = datetime.datetime.strptime(lasttimes,'%Y-%m-%d')
            plr1 = player.Player(name,-1,skill,var,city,lasttime,False)
            database.addorupdateplayer(plr1)
            plr.set(plr1)
        except :
            print("Error in values!")
            return 0
    playerlist.append(plr)
    iden = str(len(playerlist)-1)
    tree.insert('','end',str(len(playerlist)-1))
    tree.set(iden,'name',plr.name)
    tree.set(iden,'skill',str(int(plr.skill)))
    tree.set(iden,'var',str(int(plr.var)))
    tree.set(iden,'city',plr.city)
    tree.set(iden,'lastseen',datetime.datetime.strftime(plr.lasttime,'%Y-%m-%d'))
    tree.set(iden,'ranked',str(not plr.hidden))
    for child in frame.winfo_children(): child.grid_configure(padx=5, pady=5)
    window0.destroy()

#
# End player branch
#
# Start main cycle
#


database.initializeconnection("smashranking.db")

root = Tk()
root.title("Smashranking.fi BETA")
mainframe = ttk.Frame(root, padding="3 3 3 3")
mainframe.grid(row=0,column=0, sticky = (N,S,W,E))
root.columnconfigure(0,weight=1)
root.rowconfigure(0,weight=1)

tourbut=ttk.Button(mainframe, command = lambda *args :tourwin(), text = "Tournaments")
tourbut.grid(row=1,column=1)
playerbut = ttk.Button(mainframe, command = lambda *args :playerwin(), text = "Players")
playerbut.grid(row=1, column = 2)
setbut = ttk.Button(mainframe, command = lambda *args :setswin(), text = "H2H stats")
setbut.grid(row=1, column = 3)
for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

root.mainloop()
