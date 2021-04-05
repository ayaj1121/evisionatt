from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
from flask.globals import session 
from flask.helpers import flash
from flask_mysqldb import MySQL
from datetime import timedelta
from functools import wraps
import itertools
import imghdr
import os


app = Flask(__name__, static_url_path='/static')
app = Flask(__name__,template_folder='./templates',static_folder='./static')


app = Flask(__name__)
app.secret_key = "super secret key"
basedir = os.path.abspath(os.path.dirname(__file__))
stats_stud=()


# SQL configuration
mysql = MySQL(app)
app.config['MYSQL_HOST'] = 'SG-evision-4051-mysql-master.servers.mongodirector.com'
app.config['MYSQL_USER'] = 'sgroot'
app.config['MYSQL_PASSWORD'] = '#vlZnIKN9ooYfj5a'
app.config['MYSQL_DB'] = 'db1'

# File Upload configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg']
app.config['UPLOAD_PATH'] = 'uploads'

def validate_image(stream):
    header = stream.read(512)  # 512 bytes should be enough for a header check
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


# ---------------------------------------------------------Login
@app.route('/login', methods = ['POST','GET'])
def login():
    if request.method == "GET":
        return redirect(url_for('index'))
    if request.method == "POST":
        usr = request.form['username']
        psw = request.form['password']
        if(usr=="admin"):
            mycursor = mysql.connection.cursor()
            sql = "SELECT pswd FROM maintable where eno=0"
            mycursor.execute(sql)
            admin_pswd =mycursor.fetchone()[0]
            print(admin_pswd,psw)
            mycursor.close()
            if(psw==admin_pswd):    
                session['username']=usr
                session['Logged_In']=True
                session['admin']=True
                message="Successfully LoggedIn!"
                success=True
                # return render_template('home.html',message=message,success=success)
                return redirect("/Home", code=302)
            else:
                message="Invalid Password!"
                error=True
                return render_template('login.html',message=message,error=error)
        else:
            mycursor = mysql.connection.cursor()
            sql = "SELECT pswd FROM maintable where eno=%s"
            mycursor.execute(sql,(usr,))
            usr_pswd =mycursor.fetchone()[0]
            
            print(usr_pswd)
            mycursor.close()
            if(psw==usr_pswd):    
                session['username']=usr
                session['Logged_In']=True
                message="Successfully LoggedIn!"
                success=True
                return redirect(f"/Home", code=307)
                # return render_template('statistics2.html',eno=usr,message=message,success=success)   
            else:
                message="Invalid Password!"
                error=True
                return render_template('login.html',message=message,error=error)




# ---------------------------------------------------------Session
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'Logged_In' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised User')
            return redirect(url_for('index'))
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised User')
            return redirect(url_for('index'))
    return decorated_function

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.clear()
    return redirect(url_for('login'))


# ---------------------------------------------------------Index[For Security]
@app.route('/', methods =['GET', 'POST'])
def index():
    print(session)
    error=False
    if 'username' in session:
        if 'admin' in session:
            return render_template('home.html')
        else:
            return redirect(f"/Home", code=302)
    return render_template('login.html')

# ---------------------------------------------------------Home
@app.route('/Home', methods =['GET', 'POST'])
@login_required
def home():

    # If it is POST request the redirect
    if request.method =='POST':
        return redirect(url_for('home'))
  
    return render_template('home.html', title ='Home')

# ---------------------------------------------------------New Student
@app.route('/NewStudent', methods = ['POST','GET'])
@login_required
@admin_required
def NewStudentEntry():
    if request.method == 'GET':
        return render_template('NewStudent.html')
    if request.method == "POST":
        enr = request.form['enum']
        name = request.form['Name']
        pswd = request.form['Password']


        # File Upload & save on server
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(basedir, app.config['UPLOAD_PATH'], enr+".jpg"))

        with open(os.path.join(basedir, app.config['UPLOAD_PATH'])+"/"+enr+".jpg", 'rb') as file:
            s_img = file.read()

        # Insert into buff table
        mycursor = mysql.connection.cursor()
        sql = "INSERT INTO buff (eno,sname,img,pswd) VALUES (%s, %s, %s, %s)"
        val=(enr,name,s_img,pswd)
        mycursor.execute(sql, val)
        mysql.connection.commit()
        mycursor.close()

        # Remove file from web server
        os.remove(os.path.join(basedir, app.config['UPLOAD_PATH'])+"/"+enr+".jpg")

        flash(f"{enr} has been added")
        return redirect("/NewStudent", code=302)





# ---------------------------------------------------------Statistics(student)
@app.route('/Statistics',methods=['GET','POST'])
@login_required
def Statistics(): 

    eno=session['username']
    print(eno)
    if eno=='admin':
        return render_template('Statistics.html')
    #--------------fetching sname for selected eno for display purpose-------------------
    mycursor =mysql.connection.cursor()
    sql = "SELECT sname from maintable where eno=%s"
    mycursor.execute(sql,(eno,))
    sname_tuple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    if sname_tuple == None:
        flash("No such user exists")
        return redirect("/Stats", code=302)
    sname_str=sname_tuple[0]
    #-----------------for counting att percentage----------------------------- 
    mycursor =mysql.connection.cursor()
    sql = "SELECT sum(np) from total"
    mycursor.execute(sql)
    totalp_tupple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    totalp_int=int(totalp_tupple[0])

    if totalp_int==0:
        return "No class have been taken"

    mycursor =mysql.connection.cursor()
    sql = "SELECT count(pno) from att where eno=%s"
    mycursor.execute(sql,eno)
    attp_tupple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    attp_int=int(attp_tupple[0])

    percentage=round((attp_int*100)/totalp_int,2)
    return render_template('Statistics2.html',eno=eno,sname=sname_str,per=percentage)



# ---------------------------------------------------------Statistics(admin)
@app.route('/Stats',methods=['GET','POST'])
@login_required
@admin_required
def Stats():
    eno = request.form['enum']
    mycursor =mysql.connection.cursor()
    sql = "SELECT sname from maintable where eno=%s"
    mycursor.execute(sql,(eno,))
    sname_tuple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    if sname_tuple == None:
        flash("No such user exists")
        return redirect("/Statistics", code=302)
    sname_str=sname_tuple[0]
    #-----------------for counting att percentage----------------------------- 
    mycursor =mysql.connection.cursor()
    sql = "SELECT sum(np) from total"
    mycursor.execute(sql)
    totalp_tupple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    totalp_int=int(totalp_tupple[0])

    if totalp_int==0:
        return "No class have been taken"

    mycursor =mysql.connection.cursor()
    sql = "SELECT count(pno) from att where eno=%s"
    mycursor.execute(sql,eno)
    attp_tupple = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    attp_int=int(attp_tupple[0])

    percentage=round((attp_int*100)/totalp_int,2)
    global stats_stud
    stats_stud=(eno,sname_str,percentage)
    # return render_template('Statistics2.html',eno=eno,sname=sname_str,per=percentage)
    return redirect('/stats')

@app.route('/stats',methods=['GET','POST'])
@login_required
@admin_required
def st(): 
    return render_template('Statistics2.html',eno=stats_stud[0],sname=stats_stud[1],per=stats_stud[2])
          

@app.route('/StatsDaily',methods=['GET','POST'])
@login_required
def Statistics3():
    # if session['username'] == 'admin':
    #     pass
    # else:
    eno=session['username']
    dt= request.form['date']
    if eno=='admin':
        eno=stats_stud[0]
        print(eno)
    # eno = request.form['eno']
    
    mycursor =mysql.connection.cursor()
    sql = "SELECT (pno) from att where eno=%s and dt=%s"
    mycursor.execute(sql,(eno,dt,))
    pr_tuple = mycursor.fetchall()
    out = list(itertools.chain(*pr_tuple))

    if(out==None):
        return "No class attended on {dt}"

    mysql.connection.commit()
    mycursor.close()

    mycursor =mysql.connection.cursor()
    sql = "SELECT (np) from total where dt=%s"
    mycursor.execute(sql,(dt,))
    t_np = mycursor.fetchone()
    mysql.connection.commit()
    mycursor.close()
    if(t_np == None):
        return render_template('statsdaily.html',dt=dt)
        # return f"There were no class on {dt}"
    print(type(out))
    t_np=t_np[0]
    return render_template('statsdaily.html',t_np=t_np,out=out,eno=eno)


# ---------------------------------------------------------About
@app.route('/About',methods=['GET'])
@login_required
def About():
    return render_template('About.html')


# ---------------------------------------------------------Schedule
@app.route('/schedule' ,methods=['GET', 'POST']) 
@login_required
@admin_required
def schedulef():
    if request.method == 'GET':
        return render_template('scheduling.html')
    if request.method == 'POST':
        np = request.form['noper']
        np_int=int(np)
        mycursor = mysql.connection.cursor()
        sql = "UPDATE noper SET np=%s"
        val=(np)
        mycursor.execute(sql, val)
        mysql.connection.commit()
        mycursor.close()
        for i in range(1,np_int+1):
            sh = request.form[f'shr[{i}]']
            sm = request.form[f'smin[{i}]']
            eh = request.form[f'ehr[{i}]']
            em = request.form[f'emin[{i}]']
            mycursor = mysql.connection.cursor()
            sql = "UPDATE timetable SET sh=%s,sm=%s,eh=%s,em=%s WHERE pno=%s"
            val=(sh,sm,eh,em,i)
            mycursor.execute(sql, val)
            mysql.connection.commit()
            mycursor.close()
            success=True
            flash(f"Schedule has been updated")
            return redirect("/Home", code=302)

# ---------------------------------------------------------Settings

@app.route('/Settings',methods=['GET'])
@login_required
@admin_required
def settings():
    return render_template('settings.html')


@app.route('/clearAtt' ,methods=['POST'])
@login_required
@admin_required
def clearAtt():
    if request.method == "POST":
        # clear att table
        mycursor = mysql.connection.cursor()
        sql = "truncate att"
        mycursor.execute(sql)
        mysql.connection.commit()
        mycursor.close()
        # clear total table
        mycursor = mysql.connection.cursor()
        sql = "truncate total"
        mycursor.execute(sql)
        mysql.connection.commit()
        mycursor.close()
        success=True
        flash(f"Total table and att table has been cleared")
        return redirect("/Settings", code=302)


@app.route('/updatePswd' ,methods=['POST'])
@login_required
@admin_required
def updatePswd():

    enr = request.form['enroll']
    pswd = request.form['password']
    
    # Checking main table for enrollment
    mycursor = mysql.connection.cursor()
    sql = "SELECT (eno) FROM maintable where eno=%s"
    mycursor.execute(sql,(enr,))
    result =mycursor.fetchone()
    mycursor.close()
    if(result==None):
        flash(f"{enr} does not exists")
        return redirect("/Settings", code=302)
    else:
        # Updating password
        mycursor = mysql.connection.cursor()
        sql = "UPDATE maintable SET pswd=%s WHERE eno=%s"
        val=(pswd,enr,)
        mycursor.execute(sql, val)
        mysql.connection.commit()
        mycursor.close()
        success=True
        flash(f"password of {enr} has been updated")
        return redirect("/Settings", code=302)

@app.route('/removeStud' ,methods=['POST'])
@login_required
@admin_required
def removeStud():
    if request.method == "POST":
        enr = request.form["enum"]
        # Insert into rbuff table
        mycursor = mysql.connection.cursor()
        sql = "INSERT INTO rbuff (eno) VALUES (%s)"
        mycursor.execute(sql, (enr,))
        mysql.connection.commit()
        mycursor.close()
        success=True
        flash(f"{enr} has been put up on removed list")
        return redirect("/Settings", code=302)

if __name__ == '__main__':
    app.debug = True
    app.run()