from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
from flask_mail import Mail
from datetime import datetime
import json
import os
import math


with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True



app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['upload_folder'] = params["upload_path"]
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['EMAIL_USER'],
    MAIL_PASSWORD = params['EMAIL_PASS']
)
mail= Mail(app)


if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contact(db.Model):
    SNo = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50),nullable=False)
    Email = db.Column(db.String(50),nullable=False)
    Phone_Number = db.Column(db.String(12),nullable=False)
    Date = db.Column(db.String(12),nullable=True)
    Message = db.Column(db.String(120),nullable=False)
    def __repr__(self):
        return '<User %r>' % self.Name

class Post(db.Model):
    SNo = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(50),nullable=False)
    Tag_line = db.Column(db.String(25),nullable=False)
    Slug = db.Column(db.String(50),nullable=False)
    Content = db.Column(db.String(500),nullable=False)
    Date = db.Column(db.String(12),nullable=True)
    img_file = db.Column(db.String(12),nullable=True)
    def __repr__(self):
        return '<User %r>' % self.Name

@app.route('/')
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    #[0:params['no_of_post']]
    page=request.args.get('page')

    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+int(params['no_of_post'])]
    if (page==1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif(page == last):
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)


    return render_template('index.html',params=params,posts = posts,prev=prev,next=next)

@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/contact',methods=['GET','POST'])
def contact():
    if (request.method == "POST"):
        #add entry for database
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        message  = request.form.get('message')

        entry = Contact(Name=name,Email=email,Phone_Number=phone_number,Date=datetime.now(),Message=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message(subject="new message from " +name,sender = email, recipients=[params['EMAIL_USER']],body = email+"\n"+message+"\n"+phone_number)
    return render_template('contact.html',params=params)

@app.route('/post/<string:post_slug>',methods = ['GET'])
def post_route(post_slug):
    post=Post.query.filter_by(Slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route('/dashboard',methods=["GET","POST"])
def dashboard():
    if 'user' in session and session['user'] == params["Admin_user"]:
        posts = Post.query.all()
        return render_template("dashboard.html",params=params,posts=posts)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass =  request.form.get('upass')
        if (username == params["Admin_user"] and userpass == params["Admin_pass"]):
            session['user'] = username
            posts = Post.query.all()
            return render_template("/dashboard.html",params=params,posts=posts)
    return render_template('login.html',params=params)

@app.route('/edit/<string:sno>',methods = ['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params["Admin_user"]:
        if request.method == 'POST':
            title = request.form.get("title")
            tagline = request.form.get("tag_line")
            slug = request.form.get("slug")
            content = request.form.get("content")
            image = request.form.get("img_file")

            if sno == '0':
                post = Post(Title=title,Tag_line=tagline,Slug=slug,Content=content,img_file=image,Date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(SNo=sno).first()
                post.Title = title
                post.Tag_line = tagline
                post.Slug = slug
                post.Content = content
                post.img_file = image
                post.Date = datetime.now()
                db.session.commit()
                return redirect("/edit/"+sno)
        post = Post.query.filter_by(SNo=sno).first()
        return render_template("edit.html",params=params,post=post,SNo=sno)

@app.route('/uploader',methods=["GET","POST"])
def uploader():
    if 'user' in session and session['user'] == params["Admin_user"]:
        if request.method=="POST":
            f = request.files["file1"]
            f.save(os.path.join(app.config['upload_folder'],secure_filename(f.filename)))
            return "upload complete"
        return redirect("/dashboard")

@app.route('/delete/<string:sno>',methods = ['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params["Admin_user"]:
        post = Post.query.filter_by(SNo=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect("/dashboard")



app.run(debug=True)
