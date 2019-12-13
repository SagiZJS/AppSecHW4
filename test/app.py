#from flask import Flask, escape, request, url_for
import flask as fl 
import sqlite3
import dbm
import os
import random
import datetime
conn = dbm.get_conn()
c = conn.cursor()
c.execute("select name from sqlite_master where type = 'table' and name = 'users'")
table = c.fetchall()
if (len(table) == 0):
    dbm.init_db(c)
    conn.commit()
seed = random.randint(0,100000)
app = fl.Flask(__name__)
app.config.update(
    #
    SESSION_COOKIE_HTTPONLY=True,
    #SESSION_COOKIE_SECURE=True,
    #SESSION_COOKIE_SMAESITE=True,
)


db = [['admin','123','123']]
tokens={}
   
def valid_userinfo(s):
    for i in range(len(s)):
        if (not ((s[i] == '@') or(s[i]>='A' and s[i] <= 'Z') or (s[i] >= 'a' and s[i] <= 'z') or (s[i]>='0' and s[i] <='9') or (s[i] == '_') or (s[i] == '!'))):
            return False
    return True

def auth_cookie():
    
    cookie = None
    users = dbm.fetch_users(c)
    print("after db")
    print(users)
    try:
        print("getting cookie")
        cookie = fl.request.cookies.get('username')
        print("cookie",cookie)
        print("before db")

        print(users)
        for a in users:
            print(a[0])
            if (str(hash(a[0])) == cookie):
                print("cookie get")
                return a[0]
    except:
        pass
    return False
@app.route('/history/<queryid>')
def queryid(queryid):
    resp = auth_cookie()
    if (not resp):
        return fl.render_template('login_failure.html')
    username = resp
    qid = int(queryid[5:])
    res =  c.execute("select * from records where id=?",(qid,)).fetchall()
    ret = ""
    if (len(res) == 0):
        return ret
    if (username == "admin" or res[0][1]== username ):
        ret += '<p id="queryid">' + str(qid)+'</p><br>'
        ret += '<p id = "username">' + res[0][1]+'</p><br>'
        ret += '<p id = "querytext">' + res[0][2]+'</p><br>'
        ret += '<p id = "queryresults">' + res[0][3]+'</p><br>'
    return ret
@app.route('/history')
def history():
    username = auth_cookie()
    if (not username):
        return fl.render_template('login_failure.html')
    records = c.execute("select * from records where username=?",(username,)).fetchall()
    numquery = '<p id = "numqueries">'+str(len(records))+'</p><br>'
    querys = ''
    for i in range(len(records)):
        querys += '<a id="query'+str(records[i][0])+'" href = "http://localhost:5000/history/query'+str(records[i][0])+'">'+str(records[i])+'</a><br>'
    return numquery + querys

@app.route('/query')
def query():
    users = c.execute("select * from users;").fetchall()
    records = c.execute("select * from records;").fetchall()
    log = c.execute("select * from logs;").fetchall()
    print(users,records,log)
    return "users"+str(users) +"\nrecords:"+ str(records) + "\nlogs:"+str(log)
@app.route('/register',methods=['POST', 'GET'])
def register():
    print ("register")
    resp = auth_cookie()
    if (resp):
        return fl.render_template('login_success.html')
    if (fl.request.method == 'POST'):
        username = fl.request.form['username']
        password = fl.request.form['password']

        twofa = fl.request.form['twofa']
        if (not (valid_userinfo(username) and valid_userinfo(password) and valid_userinfo(twofa) ) ):
            return fl.render_template('register_failure.html')
        if ((not username) or (not password) or (not twofa)):
            return fl.render_template('register_failure.html')
        users = dbm.fetch_users(c)
        for a in users:
            if username == a[0]:
                return fl.render_template('register_failure.html')
        dbm.insert_user(c,username,password,twofa)
        conn.commit()
        db.append([username,password,twofa])
        return fl.render_template('register_success.html')
    else:
        
        return fl.render_template('register.html')

@app.route('/login',methods=['POST','GET'])
def login():
    print ("login")
    if (auth_cookie()):
        return fl.render_template('login_success.html')

    if fl.request.method == 'POST':
        username = fl.request.form['username']
        password = fl.request.form['password']
        twofa = fl.request.form['twofa'] 
         
        if (not(valid_userinfo(username) and valid_userinfo(password) and valid_userinfo(twofa))):
            return fl.render_template('login_failure.html')
        users = c.execute("select username, password, twofa from users where username=?",(username,)).fetchall()
        print("login:",users)
        if (not users):
            return fl.render_template('login_failure.html')
        for a in users:
            if (username == a[0] and password == a[1]):
                if (twofa != a[2]):
                    failinfo = "Two-factor failure"
                    break
                resp = fl.make_response(fl.render_template('login_success.html'))
                resp.set_cookie('username', str(hash(username)))
                dbm.insert_log(c, username, str(datetime.datetime.now()), 1)
                conn.commit()
                return resp
        
        return fl.render_template('login_failure.html')
    else:    
        return fl.render_template('login.html')

@app.route('/spell_check',methods=['GET','POST'])
def spell_check():
    resp = auth_cookie()
    if (not resp):
        return fl.render_template('login_failure.html')
    if fl.request.method == 'POST':
        token = fl.request.form['CSRFToken']
        print("POST",token)
        print("POST tokens",tokens[resp])
        print(type(token),len(token))
        print(type(tokens[resp]),len(tokens[resp]))
        if (tokens[resp] != token): 
            return fl.render_template('login_failure.html')
        text = fl.request.form['input']
        fw = open("to_check.txt","w")
        fw.write(text)
        fw.close()
        import os
        os.system("./a.out to_check.txt wordlist.txt > res.txt")
        fr = open("res.txt","r")
        content = fr.read()
        fr.close()
        dbm.insert_record(c,resp,text,content)
        conn.commit()
        print(content)
        if (content):
            content = content.replace("\n",",")[:-1]
        print(fl.escape(content))
        return fl.render_template("spell_check_result.html",text=text,result=content)
    else:
        token = random.randint(0, 10000000)
        print(token)
        tokens[resp] = str(token)
        print(tokens[resp])
        
        return fl.render_template('spell_check.html', csrftoken=token)
