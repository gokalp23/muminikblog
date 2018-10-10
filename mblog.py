from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# Kullanıcı Giriş Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız...","danger")
            return redirect(url_for("login"))  
    return decorated_function

# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim:", validators=[validators.Length(max=25,min=4),validators.InputRequired(message="İsim ve Soyisim girilmelidir.")])
    username = StringField("Kullanıcı Adı:", validators=[validators.Length(max=35,min=5),validators.InputRequired(message="Kullanıcı adı boş bırakılamaz.")])
    email = StringField("Email:", validators=[validators.InputRequired(message="Lütfen bir email adresi giriniz"),validators.Email(message="Doğru formatta bir email adresi giriniz!")])
    password = PasswordField("Parola:",validators=[validators.DataRequired(message="Lütfen bir parola belirleyiniz"),validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor!"),validators.Length(min=6)])
    confirm = PasswordField("Parola Doğrula:")

# Login Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Parola:")

# Makale Formu
class ArticleForm(Form):
    title = StringField("Başlık:",validators=[validators.Length(min=5,max=100,message="Başlık 5-100 karakter aralığında olmalıdır!")])
    content = TextAreaField("Yazı:",validators=[validators.Length(min=10,message="Makale içeriği en az 10 karakter olmalıdır!")])

app = Flask(__name__)
app.secret_key = "muminikblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "muminikblogdb"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# ANASAYFA
@app.route("/")
def index():
    return render_template("index.html") 

# Hakkımızda Sayfası
@app.route("/about")
def about():
    return render_template("about.html")    

# Makaleler Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")   
    
# Makale Detay Sayfası
@app.route("/article/<string:id>")
def article_detail(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE Id=%s"
    result = cursor.execute(query,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

# Makale Arama
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM articles WHERE Title LIKE '%" + keyword + "%'"
        result = cursor.execute(query)
        if result == 0:
            flash("Aradığınız kelimeye uygun makale bulunamadı...","danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)


# Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE Author = %s"
    result = cursor.execute(query,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")


# Register sayfası
@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        query = "INSERT INTO users (FullName,Email,UserName,Password) VALUES (%s,%s,%s,%s)"
        cursor.execute(query,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarı ile kayıt oldunuz...","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)

    
    
# Login işlemleri
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data
        cursor = mysql.connection.cursor()
        
        query_username = "Select * From users where UserName=%s"
        result_username = cursor.execute(query_username,(username,))
        if result_username > 0:
            data = cursor.fetchone()
            real_password = data["Password"]
            if sha256_crypt.verify(password,real_password):
                flash("Başarıyla giriş yaptınız...","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz!","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı yok!","danger")
            return redirect(url_for("login"))    

    return render_template("login.html",form = form)  

# Logout İşlemleri
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))  

################ MAKALE EKLEME,GÜNCELLEME,SİLME #################

# Makale Ekleme
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        query = "INSERT INTO articles (Title,Author,Content) VALUES (%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi.","success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html",form=form)

# Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE Id=%s and Author=%s"
    result = cursor.execute(query,(id,session["username"]))
    if result > 0:
        query_delete = "DELETE FROM articles WHERE Id=%s"
        cursor.execute(query_delete,(id,))
        mysql.connection.commit()
        flash("Makale başarıyla silinmiştir...","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Bu makaleyi silme yetkiniz yoktur!","danger")
        return redirect(url_for("index"))

# Makale Güncelle
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "Select * from articles where Id=%s and Author=%s"
        result = cursor.execute(query,(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok!","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["Title"]
            form.content.data = article["Content"]
            return render_template("edit.html",form=form)
    else:
        #POST
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        query_edit = "UPDATE articles SET Title=%s, Content=%s WHERE Id=%s"
        cursor = mysql.connection.cursor()
        cursor.execute(query_edit,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellenmiştir.","success")
        return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)







