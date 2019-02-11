import requests
import datetime

urlstart = 'https://api.challonge.com/v1/tournaments/'
filetype = 'json'
tournamentidexample = '7k1gtjz8'
file = open("challongekey.dat","r+")
apikey=file.readline()
file.close()

def getrequest(tournamentid,filetype,urlstart) :
    if (filetype != 'json') :
        return None
    URL = urlstart+tournamentid+"."+filetype
    PARAMS = {'api_key':apikey,'include_participants':1,'include_matches':1}
    r = requests.get(url=URL,params=PARAMS)
    try :
        r.raise_for_status()
    except :
        print("Aw shit!")
        return None
    
    #tournament name and date:
    datatour = r.json()['tournament']
    if(datatour['name'] is None):
        return None
    tourname = datatour['name']
    try :
        startdate=datetime.datetime.strptime(datatour['started_at'][0:10],'%Y-%m-%d')
        enddate=datetime.datetime.strptime(datatour['completed_at'][0:10],'%Y-%m-%d')
    except :
        print("Tournament not complete?")
        return None
    
    #players/results:
    reslist = []
    for row in datatour['participants'] :
        reslist.append((row['participant']['id'],row['participant']['name'],row['participant']['final_rank']))

    #sets:
    setlist = []
    for row in datatour['matches'] :
        (s1,s2)=parsescore(row['match']['scores_csv'])
        setlist.append((row['match']['player1_id'],row['match']['player2_id'],s1,s2,row['match']['round']))
    return(tourname,startdate,enddate,reslist,setlist)

def getapikey() :
    global apikey
    file = open("challongekey.txt","r")
    apikey = file.readline()
    file.close()

def parsescore(csv_score) :
    count = csv_score.count('-')
    if (count < 1) :
        print("Invalid score!")
        return None
    if (csv_score[0]=='-') :
        ind = csv_score[1:].find('-')
        score1 = -int(csv_score[1:ind+1])
        score2 = int(csv_score[(ind+2):])
        return(score1,score2)
    else :
        ind = csv_score.find('-')
        score1 = int(csv_score[:ind])
        score2 = int(csv_score[(ind+1):])
        return(score1,score2)

if __name__ == '__main__' :
    print(getrequest(tournamentidexample,'json',urlstart))
    
