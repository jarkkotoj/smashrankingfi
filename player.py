import datetime
import database

class Player :
    def __init__(self, name, pkey=-1, skill = 1500, var = 350, city = "", moment = datetime.datetime.strptime('2002-05-04', '%Y-%m-%d'), main = [], team="", alts=[]) :
        try :
            self.name = name.strip()
            self.pkey = pkey
            self.skill = skill
            self.var = var
            self.city = city
            self.main = main
            self.lasttime = moment
            self.hidden = False
            self.team=team
            self.alts=alts
        except :
            print("Oh no!")
    
    def addalt(self,altname) :
        altname = altname.strip()
        if (altname == ''):
            return 0
        if (not (database.findplayername(altname) is None)) :
            return 0
        if (not (database.findalt(altname) is None)) :
            return 0
        self.alts.append(str(altname))
        database.addalts(altname,self)
    
    def set(self, plr) :
        self.name = plr.name
        self.pkey = plr.pkey
        self.skill = plr.skill
        self.var = plr.var
        self.city = plr.city
        self.main = plr.main
        self.lasttime = plr.lasttime
        self.hidden = plr.hidden
        self.team = plr.team
        self.alts = plr.alts
        
    def updateskill(self, skill, var, lasttime) :
        self.skill = skill
        self.var = var
        self.lasttime=lasttime

class Tournament :
    def __init__(self, name, pkey, city, datea, dateb, evaluated=False) :
        self.name=name #name
        self.pkey=pkey #id
        self.city=city #city
        self.startdate=datea #startdate
        self.enddate=dateb #enddate
        self.evaluated=evaluated #evaluated

class Set : #depends on Tournament, Player classes
    def __init__(self, pkey, player1, player2, tournament, score1, score2, description="") :
        self.pkey = pkey
        self.player1=player1
        self.player2=player2
        self.tournament=tournament
        self.score1 = score1
        self.score2 = score2
        self.description=description
    
    def dq(self) :
        if (score1 <0 or score2<0):
            return true
        return false
    
    def box(self) : #best of x?
        return 2*max(score1,score2)+1
    
    def winner(self) :
        if (self.score1>self.score2 and self.score2 >= 0) :
            return self.player1
        elif (self.score2>self.score1 and self.score1 >= 0) :
            return self.player2
        else :
            return None        

class Result :
    def __init__(self, player, tournament, pkey, placement) :
        self.player=player
        self.tournament = tournament
        self.pkey = pkey
        self.placement = placement
