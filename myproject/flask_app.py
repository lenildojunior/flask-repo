import functools 
import folium
from flask import Flask, render_template , redirect, request,url_for,flash,g,session 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import text
#conversao dos parametos de uma string para a query
from draw_graph import build_graph


# create and configure the app
app = Flask(__name__) 
app.config["DEBUG"] = True 
app.secret_key = 'dev' 
app.add_url_rule('/', endpoint='index') #Comando para instanciar a pagina '/' como index no url_for 
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username = "lenildojunior",
    password="fone6058",
    hostname="localhost",
    databasename="frutas", )
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

class dispositivos(db.Model):
    __tablename__ = "dispositivos"
    id = db.Column(db.String(4096), primary_key=True)
    marca_modelo = db.Column(db.String(4096))
    data_cadastro = db.Column(db.DateTime)
    criado_por = db.Column(db.String(4096))
    ativo = db.Column(db.Integer)

class localizacao(db.Model):
    __tablename__ = "localizacao"
    id_dispositivo = db.Column(db.String(4096), primary_key=True)
    latitude = db.Column(db.String(4096))
    longitude = db.Column(db.String(4096))


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
        lista_dispositivos = dispositivos.query.filter_by(ativo=1)
        return render_template("dashboard.html", dispositivos=lista_dispositivos)
    if request.method == "POST":
        form_id_dispositivo = request.form.get('inativar')
        id_dispositivo_update = request.form.get('atualizar')
        if form_id_dispositivo is not None:
            inativa_dispositivo = dispositivos.query.filter_by(id=form_id_dispositivo).first()
            inativa_dispositivo.ativo = 0
            db.session.commit()
            return redirect('/')
        if id_dispositivo_update is not None:
           dispositivo_to_update = dispositivos.query.filter_by(id = id_dispositivo_update).first()
           session['dispositivo_id'] = dispositivo_to_update.id
           session['marca_modelo'] = dispositivo_to_update.marca_modelo
           return redirect('atualizar_cadastro_dispositivo')
    return redirect('login')

@app.route('/cadastro_de_dispositivos',methods=('GET', 'POST'))
@login_required
def cadastro_de_dispositivos():
    if request.method == 'POST':
        id_form = request.form['IMEI']
        marca_modelo = request.form['marca_modelo']
        error = None
        select_text = text("SELECT id from dispositivos where id= :id_form")
        if not id_form:
            error = 'IMEI is required.'
        elif not marca_modelo:
            error = 'Marca/modelo is required.'
        elif db.engine.execute(select_text, id_form = id_form
        ).fetchone() is not None:
            error = 'Device {} is already registered.'.format(id_form)

        if error is None:
            insert_query = text("INSERT INTO dispositivos (id, marca_modelo, data_cadastro, criado_por, ativo) VALUES (:id_form, :marca_modelo, NOW(), :username, 1)")
            db.engine.execute(insert_query, id_form = id_form, marca_modelo = marca_modelo , username = g.user['username'])
            return redirect('/')
        flash(error)
    return render_template('cadastro_de_dispositivos.html')

@app.route('/atualizar_cadastro_dispositivo',methods=('GET','POST'))
@login_required
def atualizar_cadastro_dispositivo():
    if request.method == 'GET':
        if session.get('dispositivo_id') is not None:
            id_up = session.get('dispositivo_id')
            marca_up = session.get('marca_modelo')
            return render_template('atualizar_cadastro_dispositivo.html',id = id_up, marca = marca_up)
    if request.method == 'POST':
        marca_modelo = request.form['marca_modelo']
        dispositivo_update = dispositivos.query.filter_by(id = session.get('dispositivo_id')).first()
        dispositivo_update.marca_modelo = marca_modelo
        db.session.commit()
        session.pop('dispositivo_id',None)
        return redirect('/')
#    return render_template('atualizar_cadastro_dispositivo.html',id = id_up, marca = marca_up)

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
            error = "Usuario nao encontrado"
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

@app.route('/mapa') 
@login_required 
def mapa():
    lista_coordenadas = localizacao.query.all()
    start_coords = (-5.834575, -35.2207787) #Coordenadas de Natal
    folium_map = folium.Map(location=start_coords, zoom_start=13)
    site = url_for('graphs')
    html = "<a href= '" + site + "' target='_blank'>Ver gráficos</h1></a>"
    for coordenadas in lista_coordenadas:
        folium.Marker(location = (float((coordenadas.latitude).replace(',','.')),float((coordenadas.longitude).replace(',','.'))),popup=folium.Popup(html), icon=folium.Icon(color='green')).add_to(folium_map) #Adicionando uma marcação no mapa
    #folium.Marker(location = (-5.8112895,-35.2084236),popup=folium.Popup(html), icon=folium.Icon(color='green')).add_to(folium_map)#Adicionando uma marcação no mapa
    folium_map.save('templates/folium.html')
    return render_template('mapa.html')
    #return folium_map._repr_html_()
