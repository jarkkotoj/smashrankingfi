#glicko methods
import math
import datetime
import player
import numpy as np

maxvar = 350
csq = math.sqrt(61250.0/39.0) #c-squared, assuming 1.5 years = 78 weeks = unknown
qconst = math.log(10)/400

def timeinweeks(player,date) :
    return max((date-player.lasttime).total_seconds()/(7*86400),0)

def RD(player,date) :
    return min(maxvar, math.sqrt(csq*timeinweeks(player,date)+math.pow(player.var,2)))

def gfunc(player,date):
    return 1.0/math.sqrt(1.0+ 3*math.pow(qconst*RD(player,date)/math.pi,2))

def efunc(player, setlist) :
    elist = []
    slist = []
    glist = []
    for setti in setlist :
        date = setti.tournament.startdate
        if (not (setti.winner() is None)) :
            if (setti.winner().pkey == player.pkey) :
                slist.append(1)
            else :
                slist.append(0)
            if (player.pkey == setti.player1.pkey) :
                glist.append(gfunc(setti.player2,date))
                elist.append(1.0/(1.0+math.pow(10,-glist[-1]*(player.skill-setti.player2.skill)/400.0)))
            else :
                glist.append(gfunc(setti.player1,date))
                elist.append(1.0/(1.0+math.pow(10,-glist[-1]*(player.skill-setti.player1.skill)/400.0)))
    return (elist,glist,slist)

def newratings(player, setlist) :
    (elist,glist,slist)=efunc(player,setlist)
    elist = np.array(elist)
    glist = np.array(glist)
    slist = np.array(slist)
    invds = math.pow(qconst,2)*np.sum((np.power(glist,2)*elist*(1-elist)))
    for row in setlist :
        date = row.tournament.startdate
    newskill = player.skill+qconst/(math.pow(RD(player,date),-2)+invds)*np.dot(glist,(slist-elist))
    newvar = math.pow(invds+math.pow(RD(player,date),-2),-1/2)
    return (newskill,newvar)
