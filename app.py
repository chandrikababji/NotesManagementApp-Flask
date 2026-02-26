from flask import Flask, request, redirect, url_for, render_template, make_response,flash,session
from flask_session import Session
from datetime import datetime
from otp import generate_otp
from cmail import send_mail
from stoken import endata,dndata


from mysql.connector import (connection)
mydb=connection.MySQLConnection(user='root',host='localhost',password='root@0320',db='project2')

app = Flask(__name__)
app.secret_key='code123'
app.config['SESSION_TYPE']='filesystem'
Session(app) #inetegration

#welcome route  
@app.route('/')
def welcome():
    return render_template('welcome.html')

#register route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method=='POST':
        username=request.form['uname']
        useremail=request.form['email']
        userpassword=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from userdata where useremail=%s',[useremail])
            email_count=cursor.fetchone()  #if method is fetchone it will shw like (1,) or (0,)  #if method is fetchall it will show details as list of tuples
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not verify useremail')
            return redirect(url_for('register'))
        else:
            if email_count[0]==0:
                gotp=generate_otp()
                userdata={'username':username,'useremail':useremail,'userpassword':userpassword,'server_otp':gotp}
                subject='Application for developer role'
                body=f'by using otp apply for role{gotp}'
                send_mail(to=useremail,body=body,subject=subject)
                flash('OTP Has been sent to given mail')
                return redirect(url_for('otpverify',data_info=endata(userdata)))
            elif email_count[0]==1:
                flash('User Already Existed')
    return render_template('register.html')

#otpverification route
@app.route('/otpverify/<data_info>', methods=["GET", "POST"])
def otpverify(data_info):
    try:
        sdata=dndata(data_info)

    except Exception as e:
        print(e)
        flash('could not verify otp')
        return redirect(url_for('register'))
    
    else:
        if request.method=='POST':
            user_otp=request.form['otp']
            if sdata['server_otp']==user_otp:
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('insert into userdata(username,useremail,password) values (%s,%s,%s)',
                                   [sdata['username'],sdata['useremail'],sdata['userpassword']])
                    mydb.commit()  #to save changes in database permenantly
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('Could not store user details')
                    return redirect(url_for('otpverify',data_info=data_info))
                else:
                    flash('Registration Successfull')
                    return redirect(url_for('login'))
            else:
                flash('Invalid Otp')
    return render_template('otpverification.html')

#login route
@app.route('/userlogin', methods=["GET", "POST"])
def userlogin():
    if request.method=='POST':
        login_useremail=request.form['useremail']
        login_password=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from  userdata where useremail=%s',[login_useremail])
            email_count=cursor.fetchone()[0] #(1,) or (0,)
            print(email_count)
            if email_count==1:
                cursor.execute('select password from userdata where useremail=%s',[login_useremail])
                storedpassword=cursor.fetchone()[0]
                if storedpassword==login_password:
                    session['user']=login_useremail
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid Password')
                    return redirect(url_for('userlogin'))
            elif email_count==0:
                flash('No email found pls register now')
                return redirect(url_for('register'))
            else:
                flash('Invalid emailid')
                return redirect(url_for('userlogin'))
        except Exception as e:
            print(e)
            flash('Could not verify login details')
            return redirect(url_for('userlogin'))
    return render_template('login.html')


#dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

#addnotesroute
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if not session.get('user'):
        flash('pls login to add notes')
        return redirect(url_for('userlogin'))
    if request.method=='POST':
        notes_title=request.form['title']
        notes_content=request.form['content']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone()[0]  #(1,)
            cursor.execute('insert into notedata(notes_title,notes_content,user_id) values(%s,%s,%s)',[notes_title,notes_content,user_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not store notesdetails')
            return redirect(url_for('addnotes'))
        else:
            flash('notes added successfully')
            return redirect(url_for('addnotes'))
    return render_template('addnotes.html')

#viewallnotes route
@app.route('/viewallnotes')
def viewallnotes():
    if not session.get('user'):
       flash('pls login to view all notes')
       return redirect(url_for('userlogin'))
    try:    
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]  #(1,)
        cursor.execute('select notesid,notes_title,created_at from notedata where user_id=%s',
                       [user_id])
        notesdata=cursor.fetchall()
        print(notesdata)
        cursor.close()
    except Exception as e:     
        print(e)
        flash('could not fetch notesdetails')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallnotes.html',notesdata=notesdata)
    
#viewnotesroute
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if not session.get('user'):
       flash('pls login to view all notes')
       return redirect(url_for('userlogin'))
    try:    
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]  #(1,)
        cursor.execute('select notesid,notes_title,notes_content,created_at from notedata where user_id=%s and notesid=%s',
                       [user_id,nid])
        notesdata=cursor.fetchone()
        print(notesdata)
        cursor.close()
    except Exception as e:     
        print(e)
        flash('could not fetch notesdetails')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewnotes.html',notesdata=notesdata) 
    

#delete route
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('userlogin'))
    try:
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select userid FROM userdata WHERE useremail=%s',[session.get('user')])
        user_id = cursor.fetchone()[0]
        cursor.execute('delete FROM notedata WHERE user_id=%s AND notesid=%s',[user_id, nid])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not delete note')
        return redirect(url_for('dashboard'))
    else:
        flash('Note deleted successfully')
        return redirect(url_for('viewallnotes'))

#update route
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if not session.get('user'):
        flash('pls login to view all noteses')
        return redirect(url_for('userlogin'))
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0] #(1,)
        cursor.execute('select notesid,notes_title,notes_content,created_at from notedata where user_id=%s and notesid=%s',[user_id,nid]) #[(1,'anc','2026-02-23 2:56:2'),]
        notesdata=cursor.fetchone() #(1,'python','programming','2026-24')
        print(notesdata)
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch notesdetails')
        return redirect(url_for('dashboard'))
    else:
        if request.method=='POST':
            updated_title=request.form['title'] 
            updated_content=request.form['content']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone()[0] #(1,)
                cursor.execute('update notedata set notes_title=%s,notes_content=%s where notesid=%s and user_id=%s ',[updated_title,updated_content,nid,user_id])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('could not update notesdetails')
                return redirect(url_for('viewallnotes'))
            else:
                return redirect(url_for('updatenotes',nid=nid))
        return render_template('updatenotes.html',notesdata=notesdata) 
        

#upload file route
@app.route('/uploadfile')
def uploadfile():
    return render_template('uploadfile.html')

#viewallfiles route
@app.route('/viewallfiles')
def viewallfiles():
    return render_template('viewallfiles.html')


#excel sheet route
@app.route('/excelsheet')
def excelsheet():
    return render_template('excelsheet.html')


if __name__ == "__main__":
    app.run(debug=True)


