import sqlite3
import player
import datetime

alltournaments = []
allplayers = []
allsets = []
conn = None

def initializeconnection(filename) :
    global conn
    conn = sqlite3.connect(filename)
    conn.row_factory = sqlite3.Row
    findalltournaments()
    findallplayers()
    

def findalltournaments():
    global alltournaments
    tourlist = []
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Tournaments ORDER BY id ASC')
        for row in cur.fetchall() :
            touriter = player.Tournament(row["name"],row["id"],row["city"], datetime.datetime.strptime(row["startdate"],'%Y-%m-%d'), datetime.datetime.strptime(row["enddate"],'%Y-%m-%d'), row["evaluated"])
            tourlist.append(touriter)
    alltournaments = tourlist.copy()
    return tourlist

def findallplayers() :
    global allplayers
    playerlista=[]
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Players ORDER BY id ASC')
        for row in cur.fetchall() :
            altlist = findaltbyid(row["id"]).copy()
            playeriter = player.Player(row["name"],row["id"],row["skill"], row["var"], row["city"], datetime.datetime.strptime(row["lasttime"],'%Y-%m-%d'),row["hidden"],alts=altlist)
            playerlista.append(playeriter)
    allplayers = playerlista.copy()
    return playerlista

def findallsets() :
    global allsets
    setlist=[]
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets ORDER BY id ASC')
        for row in cur.fetchall() :
            p1 = binarysearch(allplayers, row["id_p1"])
            p2 = binarysearch(allplayers, row["id_p2"])
            tour = binarysearch(alltournaments, row["tournament_id"])
            setiter = player.Set(row["id"],p1,p2,tour, row["score1"], row["score2"], row["description"])
            setlist.append(setiter)
    allsets = setlist.copy()
    return setlist

def findplayerstournament(tournament):
    playerlist = []
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT id_p1 AS iidee FROM Sets WHERE tournament_id = ? UNION SELECT DISTINCT id_p2 AS iidee FROM Sets WHERE tournament_id = ?',(tournament.pkey,tournament.pkey,))
        for row in cur.fetchall():
            plyr = binarysearch(allplayers, row["iidee"])
            playerlist.append(plyr)
    return playerlist

def findplayername(name) :
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Players WHERE TRIM(UPPER(name)) = TRIM(UPPER(?))', (name,))
        results = cur.fetchall()
        if (len(results)==0) :
            return None
            # to be implemented: Alts
        elif (len(results)>1) :
            print("Warning, multiple players found!")
            return results
        pl = results[0]
        altlist = findaltbyid(pl["id"]).copy()
        return player.Player(pl["name"], pl["id"], pl["skill"], pl["var"], pl["city"], datetime.datetime.strptime(pl["lasttime"],'%Y-%m-%d'),alts=altlist)

def findtournamentbyname(name) :
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Tournaments WHERE TRIM(UPPER(name)) = TRIM(UPPER(?))', (name,))
        results = cur.fetchall()
        if (len(results)==0) :
            return None
        
        elif (len(results)>1) :
            print("Warning, multiple tournaments found!")
        tour = results[0]
        return player.Tournament(tour["name"], tour["id"], tour["city"], datetime.datetime.strptime(tour["startdate"],'%Y-%m-%d'),datetime.datetime.strptime(tour["enddate"],'%Y-%m-%d'), tour["evaluated"])

def findallsetsfortournament(tournament) :
    setlist = []
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets WHERE tournament_id = ?', (tournament.pkey,))
        for row in cur.fetchall():
            p1 = binarysearch(allplayers, row["id_p1"])
            p2 = binarysearch(allplayers, row["id_p2"])
            setlist.append(player.Set(row["id"], p1, p2, tournament, row["score1"], row["score2"], row["description"]))
    return setlist

def findsetstournamentplayer(tournament,plr) :
    setlist = []
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets WHERE tournament_id = ? AND (id_p1 = ? OR id_p2 = ?)', (tournament.pkey,plr.pkey,plr.pkey,))
        for row in cur.fetchall():
            p1 = binarysearch(allplayers, row["id_p1"])
            p2 = binarysearch(allplayers, row["id_p2"])
            setlist.append(player.Set(row["id"], p1, p2, tournament, row["score1"], row["score2"], row["description"]))
    return setlist

def findset(setti) :
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets WHERE ((id_p1=? AND id_p2=? AND score1=? AND score2=?) OR (id_p2=? AND id_p1=? AND score2=? AND score1 = ?)) AND tournament_id=? AND description = ?',(setti.player1.pkey,setti.player2.pkey,setti.score1,setti.score2,setti.player1.pkey,setti.player2.pkey,setti.score1,setti.score2,setti.tournament.pkey,setti.description,))
        row = cur.fetchone()
        if (row is None) :
            return None
        p1 = findplayerbyid(row["id_p1"])
        p2 = findplayerbyid(row["id_p2"])
        return player.Set(row["id"],p1,p2,setti.tournament,row["score1"],row["score2"],row["description"])
    return None

#find 
def findsetsforplayer(pkey) :
    setlist = []
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets WHERE id_p1 = pkey OR id_p2 = pkey')
        for row in cur.fetchall() :
            p1 = binarysearch(allplayers, row["id_p1"])
            p2 = binarysearch(allplayers, row["id_p2"])
            tour = binarysearch(alltournaments, row["tournament_id"])
            setlist.append(player.Set(row["id"], p1, p2, tour, row["score1"], row["score2"],row["description"]))
    return setlist

def addalts(alt,plr) :
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO Alts (altname, player_id) VALUES (?,?)', (alt,plr.pkey,))

def findaltbyid(pkey) :
    altlist = []
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Alts WHERE player_id = ?', (pkey,))
        for row in cur.fetchall() :
            altlist.append(row['altname'])
    return altlist.copy()

def findalt(altname) :
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Alts WHERE TRIM(UPPER(altname)) = TRIM(UPPER(?))',(altname,))
        results = cur.fetchall()
        if (len(results)<1) :
            return None
        row = results[0]
        plr=findplayerbyid(row['player_id'])
        return plr
    return None

def addorupdateplayer(player) :
    with conn: 
        cur = conn.cursor()
        if (findplayerbyid(player.pkey) is None) :
            cur.execute('INSERT INTO Players (name, skill, var, city, lasttime, hidden) VALUES (?,?,?,?,?,?)',     (player.name,player.skill,player.var,player.city,player.lasttime.strftime('%Y-%m-%d'),player.hidden,))
            player.pkey=findplayername(player.name).pkey
            allplayers.append(player)
            allplayers.sort(key = lambda x : x.pkey)
        else :
            cur.execute('UPDATE Players SET name = ?, skill=?, var = ?, city=?, lasttime=? WHERE id=?', (player.name,player.skill,player.var,player.city,player.lasttime.strftime('%Y-%m-%d'),player.pkey))
    findallplayers()

def addsets(sets) :
    with conn: 
        cur = conn.cursor()
        array = []
        for row in sets :
            array.append((row.player1.pkey,row.player2.pkey,row.tournament.pkey,row.score1,row.score2,row.desription))
            cur.executemany('INSERT INTO Sets (id_p1, id_p2, tournament_id, score1, score2, description) VALUES (?,?,?,?,?,?)', array)
    allsets = findallsets()

def addset(setti) :
    with conn:
        foundset = findset(setti)
        if (foundset is None) :
            cur = conn.cursor()
            
            cur.execute('INSERT INTO Sets (id_p1, id_p2, tournament_id, score1, score2, description) VALUES (?,?,?,?,?,?)',(setti.player1.pkey, setti.player2.pkey, setti.tournament.pkey, setti.score1, setti.score2, setti.description,))
            foundset = findset(setti)
            setti.pkey = foundset.pkey
        else :
            setti.pkey = foundset.pkey
    allsets = findallsets()

def updateset(setti) :
    with conn:
        cur=conn.cursor()
        cur.execute('UPDATE Sets SET score1 = ?, score2=?, description = ? WHERE id = ?',(setti.score1,setti.score2,setti.description,setti.pkey,))
        return 1
    return 0

def addorupdatetournament(tournament) :
    with conn: 
        cur = conn.cursor()
        if (findtournamentbyid(tournament.pkey) is None) :
            cur.execute('INSERT INTO Tournaments (name, city, startdate, enddate, evaluated) VALUES (?,?,?,?,?)', (tournament.name, tournament.city, tournament.startdate.strftime('%Y-%m-%d'),tournament.enddate.strftime('%Y-%m-%d'), tournament.evaluated,))
            tournament.pkey = findtournamentbyname(tournament.name).pkey
            alltournaments.append(tournament)
        else :
            cur.execute('UPDATE Tournaments SET name=?, city=?, startdate=?, enddate=?, evaluated=?  WHERE id = ?', (tournament.name, tournament.city, tournament.startdate.strftime('%Y-%m-%d'),tournament.enddate.strftime('%Y-%m-%d'), tournament.evaluated,tournament.pkey,))
    findalltournaments()

def findsetsbetween(plyr1,plyr2) :
    setlist = []
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Sets WHERE (id_p1 = ? AND id_p2 = ?) OR (id_p2 = ? AND id_p1 = ?)',(plyr1.pkey,plyr2.pkey,plyr1.pkey,plyr2.pkey,))
        for row in cur.fetchall() :
            tour= binarysearch(alltournaments,row["tournament_id"])
            if (row["id_p1"]==plyr1.pkey) :
                setlist.append(player.Set(row["id"],plyr1,plyr2, tour, row["score1"], row["score2"],row["description"]))
            else :
                setlist.append(player.Set(row["id"],plyr2,plyr1,tour, row["score1"], row["score2"],row["description"]))
    return setlist

def deletetournament(tournament) :
    with conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM Tournaments WHERE id = ?', (tournament.pkey,))
    findalltournaments()

def deleteplayer(player) :
    with conn: 
        cur = conn.cursor()
        cur.execute('DELETE FROM Players WHERE id = ?', (player.pkey,))
    findallplayers()
    
def deleteset(setti) :
    with conn: 
        cur = conn.cursor()
        cur.execute('DELETE FROM Sets WHERE id =?', (setti.pkey,))
    findallsets()

def findresultplayer(plr) :
    resultlist = []
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Results WHERE id_player = ?', (plr.pkey,))
        for row in cur.fetchall() :
            tour = binarysearch(alltournaments,row["tournament_id"])
            resultlist.append(player.Result(plr,tour,row["id"],row["placement"]))
    return resultlist

def findresult(plr,tournament) :
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Results WHERE id_player = ? AND tournament_id = ?',(plr.pkey,tournament.pkey,))
        res=cur.fetchone()
        if (res is None) :
            return None
        return player.Result(plr,tournament,res["id"],res["placement"])
    return None

def findresults(tournament) :
    resultlist = []
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Results WHERE tournament_id = ? ORDER BY placement', (tournament.pkey,))
        for row in cur.fetchall() :
            pl=binarysearch(allplayers, row["id_player"])
            resultlist.append(player.Result(pl,tournament,row["id"],row["placement"]))
    return resultlist

def findresultid(resultid) :
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Results WHERE id = ?',(resultid,))
        res=cur.fetchone()
        if (res is None) :
            return None
        p = binarysearch(allplayers,res["id_player"])
        tour = binarysearch(alltournaments, res["tournament_id"])
        return player.Result(p,tour,resultid,res["placement"])
    return None

def addorupdateresult(result) :
    with conn: 
        cur = conn.cursor()
        if (findresult(result.player,result.tournament) is None) :
            cur.execute('INSERT INTO Results (id_player,tournament_id,placement) VALUES (?,?,?)', (result.player.pkey,result.tournament.pkey,result.placement) )
            res=findresult(result.player,result.tournament)
            result.pkey=res.pkey
        else :
            cur.execute('UPDATE Results SET placement=? WHERE id = ?',(result.placement,result.pkey,)) 
        
def deleteresult(result) :
    with conn: 
        cur = conn.cursor()
        cur.execute('DELETE FROM Results WHERE id = ?', (result.pkey,))
        
#Use binary search on an ordered list
#pkeys: tournaments, players: 1/2
#       sets: 0/1
def binarysearch(lista, target) :
    starti = 0;
    endi = len(lista)-1
    while (starti <= endi) :
        middle  = (starti+endi)//2
        if (lista[middle].pkey>target) :
            endi = middle-1
        elif (lista[middle].pkey<target) :
            starti = middle+1
        elif (lista[middle].pkey==target) :
            return lista[middle]

#Find the instances of pkey in given lista
def searchlistbyidbin(lista,pkey) :
    items = [item for item in lista if item.pkey==pkey ]
    return items
    
#find the player in db by their primary key
def findplayerbyid(pkey) :
    with conn: 
        cur = conn.cursor()
        cur.execute('SELECT * FROM Players WHERE id = ?', (pkey,))
        row = cur.fetchone()
        if (row is None) :
            return None
        cur = conn.cursor()
        cur.execute('SELECT * FROM Alts WHERE player_id=?', (pkey,))
        altlist = []
        for row1 in cur.fetchall():
            altlist.append(row1['altname'])
        return player.Player(row["name"], row["id"], row["skill"], row["var"], row["city"],alts=altlist.copy())
    return None

#return player.Player(row["name"], row["id"], row["skill"], row["var"], row["city"], datetime.datetime.strptime(row["lasttime"],'%Y-%m-%d'))

def findtournamentbyid(pkey) :
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM Tournaments WHERE id = ?', (pkey,))
        row = cur.fetchone()
        if (row is None) :
            return None
        return player.Tournament(row["name"], pkey, row["city"], datetime.datetime.strptime(row["startdate"],'%Y-%m-%d'), datetime.datetime.strptime(row["enddate"],'%Y-%m-%d'), row["evaluated"])
    return None
