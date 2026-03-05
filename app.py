from flask import Flask, request, redirect, url_for, render_template, make_response,flash,session,send_file,jsonify
from flask_session import Session
from datetime import datetime
from otp import generate_otp
from cmail import send_mail
from stoken import endata,dndata
from io import BytesIO
import flask_excel as excel
import re
import os
import psycopg2


DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    mydb = psycopg2.connect(DATABASE_URL)
else:
    print("DATABASE_URL not found")



app = Flask(__name__)
excel.init_excel(app)
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
            cursor=mydb.cursor()
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
                    cursor=mydb.cursor()
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
            cursor=mydb.cursor()
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
            cursor=mydb.cursor()
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
        cursor=mydb.cursor()
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
        cursor=mydb.cursor()
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
        cursor = mydb.cursor()
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
        cursor=mydb.cursor()
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
                cursor=mydb.cursor()
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
@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            f_data=filedata.read()
            try:
                cursor=mydb.cursor()
                cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone()[0]
                cursor.execute('insert into filedata(filename,filedata,user_id) values(%s,%s,%s)',[fname,f_data,user_id])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('Could not store filed data')
                return redirect(url_for('uploadfile'))
            else:
                flash('file uploaded successfully')
                return redirect(url_for('uploadfile'))

        return render_template('uploadfile.html')
    else:
        flash('pls login to upload file')
        return redirect(url_for('userlogin'))
    



#viewallfiles route
@app.route('/viewallfiles',methods=['GET','POST'])
def viewallfiles():
    if not session.get('user'):
        flash('pls login to view all noteses')
        return redirect(url_for('userlogin'))
    try:
        cursor=mydb.cursor()
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0] #(1,)
        cursor.execute('select fid,filename,created_at from filedata where user_id=%s',[user_id]) #[(1,'anc','2026-02-23 2:56:2'),]
        allfilesdata=cursor.fetchall()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not fetch filesdetails')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallfiles.html',filesdata=allfilesdata)

#viewfile route
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if not session.get('user'):
       flash('pls login to view all notes')
       return redirect(url_for('userlogin'))
    try:    
        cursor=mydb.cursor()
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]  #(1,)
        cursor.execute('select fid,filename,filedata,created_at from filedata where user_id=%s and fid=%s',
                       [user_id,fid])
        file_data=cursor.fetchone()
        cursor.close()
    except Exception as e:     
        print(e)
        flash('could not fetch filedetails')
        return redirect(url_for('viewallfiles'))
    else:
        bytesdata=BytesIO(file_data[2])
        return send_file(bytesdata,as_attachment=False,download_name=file_data[1])

#download file route
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if not session.get('user'):
       flash('pls login to view all notes')
       return redirect(url_for('userlogin'))
    try:    
        cursor=mydb.cursor()
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]  #(1,)
        cursor.execute('select fid,filename,filedata,created_at from filedata where user_id=%s and fid=%s',
                       [user_id,fid])
        file_data=cursor.fetchone()
        cursor.close()
    except Exception as e:     
        print(e)
        flash('could not fetch filedetails')
        return redirect(url_for('viewallfiles'))
    else:
        bytesdata=BytesIO(file_data[2])
        return send_file(bytesdata,as_attachment=True,download_name=file_data[1])
     
   
#deletefile route
@app.route('/deletefile/<fid>')
def deletefile(fid):
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('userlogin'))
    try:
        cursor = mydb.cursor()
        cursor.execute('select userid FROM userdata WHERE useremail=%s',[session.get('user')])
        user_id = cursor.fetchone()[0]
        cursor.execute('delete FROM filedata WHERE fid=%s AND user_id=%s',[ fid,user_id])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('Could not delete file')
        return redirect(url_for('dashboard'))
    else:
        flash('file deleted successfully')
        return redirect(url_for('viewallfiles'))  

#excel sheet route
@app.route('/getexceldata')
def getexceldata():
    if not session.get('user'):
       flash('pls login to view all notes')
       return redirect(url_for('userlogin'))
    try:    
        cursor=mydb.cursor()
        cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
        user_id=cursor.fetchone()[0]  #(1,)
        cursor.execute('select notesid,notes_title,notes_content,created_at from notedata where user_id=%s',
                       [user_id])
        notesdata=cursor.fetchall()
        cursor.close()
    except Exception as e:     
        print(e)
        flash('could not fetch notesdetails')
        return redirect(url_for('dashboard'))
    else:
        array_data=[list(i) for i in notesdata]
        columns=['Notesid','Notes Title','Notes_Content','Created_at']
        array_data.insert(0,columns)
        print(array_data)
        return excel.make_response_from_array(array_data,'xlsx',file_name='excel_data')
    
#search route
@app.route('/search',methods=['POST'])
def search():
    if session.get('user'):
        search_data=request.form['sdata']
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(search_data):
            try:    
                cursor=mydb.cursor()
                cursor.execute('select userid from userdata where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone()[0]  #(1,)
                cursor.execute('select notesid,notes_title,notes_content,created_at from notedata where user_id=%s and (notes_title like %s or notes_content like %s or created_at like %s)',[user_id,search_data+'%',search_data+'%',search_data+'%'])
                notesdata=cursor.fetchall()
                cursor.close()
            except Exception as e:     
                print(e)
                flash('could not fetch notesdetails')
                return redirect(url_for('dashboard'))  
            else:
                return render_template('viewallnotes.html',notesdata=notesdata)  
        else:
            flash('invalid search data')
            return redirect(url_for('dashboard'))
        
           
#logout route
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('userlogin'))
    else:
        flash('to logout you must login')
        return redirect(url_for('userlogin'))

#forgot password route
@app.route('/forgotpwd',methods=['GET','POST'])
def forgotpwd():
    if request.method=='POST':
        useremail=request.form['email']
        try:
            cursor=mydb.cursor()
            cursor.execute('select count(*) from userdata where useremail=%s',[useremail])
            email_count=cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not verify useremail')
            return redirect(url_for('register'))
        else:
            if email_count[0]==1:
                subject='Reset link for snm application'
                body=f"use the given link for snm app {url_for('newpassword',data=endata(useremail),_external=True)}"
                send_mail(to=useremail,body=body,subject=subject)
                flash('Reset link has been sent to given mail')
                return redirect(url_for('forgotpwd'))
            elif email_count[0]==0:
                flash('User Email not found')
                return redirect(url_for('forgotpwd'))
    return render_template('forgotpwd.html')

#new password route
@app.route('/newpassword/<data>',methods=['GET','PUT'])
def newpassword(data):
    if request.method=='PUT':
        print(request.get_json())
        npassword=request.get_json()['password']
        try:
            sdata=dndata(data)
        except Exception as e:
            print(e)
            flash('could not verify email')
            return redirect(url_for('newpassword',data=data))
        else:
            try:
                cursor=mydb.cursor()
                cursor.execute('update userdata set password=%s where useremail=%s',[npassword,sdata])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('Could not update password ')
                return redirect(url_for('newpassword',data=data))
            else:
                flash('password successfull')
                return jsonify({"message":"ok"})
    return render_template('newpassword.html',data=data)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

