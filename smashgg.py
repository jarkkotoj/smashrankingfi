import requests
import datetime
import time

url = 'https://api.smash.gg/gql/alpha'
file  = open("smashggkey.dat","r+")
apikey = file.readline()
file.close()

def postresults(apikey, url, eventId) :
    query = 'query EventStandings($eventId: Int!,$pageNum:Int!) {\n  event(id:$eventId) {\n    name,\n    id,\n    standings(query:{perPage:70,page:$pageNum}) {\n      nodes {\n        placement\n        entrant {\n          name\n        }\n      }\n    }\n  }\n}'
    headers = {"Authorization": "Bearer " + apikey}
    i=1
    data=[]
    while (i>0) :
        json = {'query':query,'variables':{"eventId":eventId,"pageNum":i}}
        r = requests.post(url,json=json,headers=headers)
        i = i+1
        dataaux = r.json()['data']['event']['standings']['nodes']
        if (dataaux is None or i>100):
            break
        try :
            r.raise_for_status()
        except :
            print("Aw shit with smash<dot>gg in postresults (resslist)")
            return None
        data=data+dataaux
        time.sleep(1.2)
    resslist=[]
    for row in data :
        resslist.append((row['entrant']['name'],row['placement']))
    
    query2='query FindPhases($eventId: Int!) {\n  event(id:$eventId) {\n    phases {\n      id,\n      name\n    }\n    phaseGroups {\n      id,\n      phaseId,\n      displayIdentifier,\n      state\n    }\n  }\n}'
    json = {'query':query2, 'variables':{"eventId":eventId}}
    r = requests.post(url,json=json,headers=headers)
    
    try:
        r.raise_for_status()
    except :
        print("Aw shit with smash<dot>gg in postresults (phasegrouplist)")
        return None
    phaselist = []
    for row in r.json()['data']['event']['phases']:
        phaselist.append((row['name'],row['id']))
    phasegrouplist = []
    for row in r.json()['data']['event']['phaseGroups']:
        if (row['state']==3) :
            phasegrouplist.append((row['id'],phasename(phaselist,row['phaseId'])+' '+str(row['displayIdentifier'])))
    return(resslist,phasegrouplist)
    
def phasename(phaselist,phaseid) :
    return next((phase[0] for phase in phaselist if phase[1]==phaseid),None)

def getsetsforphasegroup(phasegroupid, apikey, url, roundstring) :
    query = 'query SetsInPhaseGroup($groupId: Int!) {\n  phaseGroup(id:$groupId) {\n    id,\n    sets {\n      displayScore,\n      round,\n      slots {\n        entrant {\n          name\n        }\n      }\n    }\n  }\n}'
    
    headers = {"Authorization": "Bearer " + apikey}
    json = {'query':query,'variables':{'groupId':phasegroupid}}
    r = requests.post(url,json=json,headers=headers)
    data = r.json()["data"]['phaseGroup']['sets']
    
    try :
        r.raise_for_status()
    except :
        print("Aw shit! with smash<dot>gg in fun getsetsforphasegroup")
        return None
    
    setlist = []
    for setti in data :
        aux = parsedisplayscore(setti['displayScore'],setti['slots'])
        if (not(aux is None)):
            (s1,s2,p1name,p2name)=aux
            setlist.append((p1name,p2name,s1,s2,wrorlrornot(roundstring,setti['round'])))
    return setlist

def wrorlrornot(roundstring,intti) :
    if ('racket' in roundstring.lower() or 'top' in roundstring.lower()) :
        if (intti>0):
            return roundstring+': '+'WR'+ str(intti)
        else :
            return roundstring+': '+'LR'+ str(-intti)
    return roundstring+': '+str(intti)

def parsedisplayscore(dispscore,helpvar) :
    if (dispscore is None) :
        return None
    if (dispscore.strip().lower() == 'bye' or dispscore.strip().lower() == 'dq') :
        return None
    p1name=helpvar[0]['entrant']['name']
    p2name=helpvar[1]['entrant']['name']
    s1 = dispscore[len(p1name)+1] #assuming one digit scores or W or L
    s2 = dispscore[-1]
    try :
        s1=int(dispscore[len(p1name)+1]) #if numerical value
        s2=int(dispscore[-1])
    except :
        if (s1.lower() == 'w') :
            s1 = 1
            s2 = 0
        else :
            s2 = 1
            s1 = 0
    return(s1,s2,p1name,p2name)

def countdigits(dispscore) :
    count = 0
    for i in range(len(dispscore)) :
        if (dispscore[i].isnumeric()) :
            count += 1
    return count
    
def getevents(tournamentslug, apikey, url, helpwords=('melee','singles')) :
    query = 'query Events($tourneySlug: String!) {'
    query = query+"\n  tournament(slug:$tourneySlug) {"
    query = query+'\n    name,'
    query = query+'\n    id,'
    query = query+'\n    startAt,'
    query = query+'\n    endAt,'
    query = query+'\n    city,'
    query = query+'\n    events{'
    query = query+'\n      id,'
    query = query+'\n      name'
    query = query+'\n    }'
    query = query+'\n  }'
    query = query+'\n}'
    json = {'query':query,'variables':{"tourneySlug":tournamentslug}}
    headers = {"Authorization": "Bearer " + apikey}
    
    r=requests.post(url=url,json=json,headers=headers)
    try :
        r.raise_for_status()
    except :
        print("Aw shit! with smash<dot>gg in getevents")
        return None
    
    data = r.json()['data']['tournament']
    tourname = data['name']
    startdate = datetime.date.fromtimestamp(data['startAt'])
    enddate = datetime.date.fromtimestamp(data['endAt'])
    city = data['city']
    events = data['events']
    for event in events :
        juuh = 1
        for word in helpwords :
            if ( not (word.strip().lower() in event['name'].strip().lower())) :
                juuh = -1
                break
        if (juuh == 1) :
            eventid = event['id']
    return(tourname,startdate,enddate,city,eventid)
    
def retrievetournament(tournamentslug,helpwords=('melee','singles')) :
    hit =getevents(tournamentslug,apikey,url,helpwords)
    if (hit is None) :
        return None
    (tourname,startdate,enddate,city,eventid)=hit
    hit=postresults(apikey,url,eventid)
    if (hit is None) :
        return None
    (reslist,phasegrouplist)=hit
    setlist = []
    for phasegroup in phasegrouplist :
        time.sleep(1)
        listaux = getsetsforphasegroup(phasegroup[0],apikey,url,phasegroup[1])
        if (not(listaux is None)) :
            setlist = setlist+listaux
    if (len(setlist)==0) :
        return None
    return (tourname,startdate,enddate,city,reslist,setlist)
    
if __name__ == '__main__' :
    (tourname,startdate,enddate,city,eventid)=getevents('poravaunu-5',apikey,url)
    (reslist,phasegrouplist)=postresults(apikey,url,eventid)
    setlist = []
    for phasegroup in phasegrouplist :
        time.sleep(0.8)
        listaux = getsetsforphasegroup(phasegroup[0],apikey,url,phasegroup[1])
        if (not(listaux is None)) :
            setlist = setlist+listaux
    print(setlist)
