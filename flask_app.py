import functools
from flask import Flask, render_template , redirect, request,url_for,flash,g,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from draw_graph import build_graph



# create and configure the app
app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'dev'
app.add_url_rule('/', endpoint='index') #Comando para instanciar a pagina '/' como index no url_for

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username = "lenildojunior",
    password="sua senha",
    hostname="host do banco",
    databasename="nome do banco",
)

#Set the app config values for Database connection
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class frutas(db.Model):
    __tablename__ = "frutas"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(4096))

class usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(4096))
    password = db.Column(db.String(4096))



#Funcao para verificar se o usuario esta logado antes de ir para esta pagina
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect('login')

        return view(**kwargs)

    return wrapped_view

@app.route('/',methods=["GET","POST"])
@login_required #Indica que para acessar esta pagina, precisa estar logado
def index():
    if request.method =="GET":
        fruits = frutas.query.all()
        return render_template("dashboard.html", fruits=fruits)
    return redirect('login')


@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        select_text = text("SELECT id from usuario where username= :usuario")
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.engine.execute(select_text, usuario = username
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            insert_query = text("INSERT INTO usuario (username, password) VALUES (:usuario, :senha)")
            db.engine.execute(insert_query, usuario = username, senha = password)
            return redirect('login')
        flash(error)
    return render_template('register.html')

@app.route('/login',methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        login_query = text("SELECT * FROM usuario where username = :usuario")
        user = db.engine.execute(login_query, usuario = username).fetchone()
        if user is None:
            error = "Usuário não encontrado"
        elif (user['password'])!=password:
            error = "Senha incorreta"

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect('/')
        flash(error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#Funcao para indicar a sessao de usuario
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = db.engine.execute(text(
            "SELECT * FROM usuario WHERE id = :id_usuario"), id_usuario = user_id
        ).fetchone()

@app.route('/graphs')
@login_required
def graphs():
    eixo_x = frutas.query.all()
    eixo_x_list = []
    eixo_y_list = []
    for fruta in eixo_x:
        eixo_x_list.append(fruta.nome)
        eixo_y_list.append(fruta.id)

    graph_url = build_graph(eixo_x_list,eixo_y_list)
    return render_template('graphs.html',graph1 = graph_url,graph2 = graph_url,graph3 = graph_url)


