import functools 
import folium
from flask import Flask, render_template , redirect, request,url_for,flash,g,session,jsonify 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import text, and_,cast
from datetime import date
#conversao dos parametos de uma string para a query
from draw_graph import build_graph,build_graph3
#Usando geolocalizacao
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="flask_app")


# create and configure the app
app = Flask(__name__) 
app.config["DEBUG"] = True 
app.secret_key = 'dev' 
app.add_url_rule('/', endpoint='index') #Comando para instanciar a pagina '/' como index no url_for 
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    #username = "lenildojunior",
    #password="fone6058",
    username = "root",
    password = "*chicoADM*1",
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

class contagem(db.Model):
    __tablename__ = "contagem"
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer)
    numero_faixa = db.Column(db.Integer)
    data_hora = db.Column(db.DateTime)
    id_dispositivo = db.Column(db.String(4096))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'quantidade': self.quantidade,
            'numero_faixa': self.numero_faixa,
            'data_hora': self.data_hora,
            'id_dispositivo': self.id_dispositivo
        }


class usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(4096))
    cpf = db.Column(db.String(4096))
    email = db.Column(db.String(4096))
    telefone = db.Column(db.String(4096))
    username = db.Column(db.String(4096))
    password = db.Column(db.String(4096))
    id_perfil = db.Column(db.Integer)
    ativo = db.Column(db.Integer)

class perfil(db.Model):
    __tablename__ = "perfil"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(4096))

class dispositivos(db.Model):
    __tablename__ = "dispositivos"
    id = db.Column(db.String(4096), primary_key=True)
    marca_modelo = db.Column(db.String(4096))
    data_cadastro = db.Column(db.DateTime)
    criado_por = db.Column(db.String(4096))
    ativo = db.Column(db.Integer)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'marca_modelo': self.marca_modelo,
            'data_cadastro':self.data_cadastro,
            'criado_por':self.criado_por,
            'ativo':self.ativo
        }
    

class localizacao(db.Model):
    __tablename__ = "localizacao"
    id_dispositivo = db.Column(db.String(4096), primary_key=True)
    latitude = db.Column(db.String(4096))
    longitude = db.Column(db.String(4096))
    qtd_faixas = db.Column(db.Integer)
    data_realocacao = db.Column(db.DateTime)

    @property
    def serialize(self):
        return {
            'id_dispositivo': self.id_dispositivo,
            'latitude': self.latitude,
            'longitude':self.longitude,
            'qtd_faixas':self.qtd_faixas
        }

class historico_localizacao(db.Model):
    __tablename__ = "historico_localizacao"
    id = db.Column(db.Integer, primary_key=True)
    latitude_anterior = db.Column(db.String(4096))
    latitude_atual = db.Column(db.String(4096))
    longitude_anterior = db.Column(db.String(4096))
    longitude_atual = db.Column(db.String(4096))
    data_modificacao = db.Column(db.DateTime)
    id_dispositivo = db.Column(db.String(4096))


#Funcao para verificar se o usuario esta logado antes de ir para esta pagina
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect('login')
        return view(**kwargs)
    return wrapped_view 


#Definição da API para comunicação interação com o dispositivo

@app.route('/API/get_dispositivos',methods=["GET"])
def get_dispositivos():
    lista_dispositivos = dispositivos.query.filter_by(ativo=1)
    return jsonify([i.serialize for i in lista_dispositivos]),200


@app.route('/API/get_dispositivos/<id_disp>',methods=["GET"])
def get_dispositivos_by_id(id_disp):
    lista_dispositivos = dispositivos.query.filter_by(id=id_disp)
    return jsonify([i.serialize for i in lista_dispositivos]),200

@app.route('/API/get_localizacao/<id_disp>',methods=["GET"])
def get_localizacao_by_id(id_disp):
    valor_localizacao = localizacao.query.filter_by(id_dispositivo=id_disp)
    return jsonify([i.serialize for i in valor_localizacao]),200

@app.route('/API/registrar_contagem',methods=["POST"])
def registrar_contagem():
    data = request.get_json()
    if(data):
        dispositivo = dispositivos.query.filter_by(id=data[0].get('id_dispositivo'),ativo=1).first()
        if(dispositivo is not None):
            dados_localizacao = localizacao.query.filter_by(id_dispositivo=data[0].get('id_dispositivo')).first()
            if(dados_localizacao is not None):
                for informacao in data:
                    insert_query = text("INSERT INTO contagem (numero_faixa,quantidade,data_hora,id_dispositivo) VALUES (:numero_da_faixa,:quantidade,NOW(),:id_disp)")
                    db.engine.execute(insert_query,numero_da_faixa = informacao.get('numero_faixa'),quantidade=informacao.get('quantidade'), id_disp = informacao.get('id_dispositivo'))
                return jsonify(data),201
            return jsonify({'error':'Localizacao nao cadastrada'})
        return jsonify({'error':'dispositivo nao cadastrado'})
    return jsonify({'error':'Enviado um JSON vazio'})

@app.route('/API/cadastrar_localizacao',methods=["POST"])
def cadastrar_localizacao():
    data = request.get_json()
    if(data):
        dispositivo = dispositivos.query.filter_by(id=data.get('id_dispositivo'),ativo=1).first()
        if(dispositivo is not None):
            dados_localizacao = localizacao.query.filter_by(id_dispositivo=data.get('id_dispositivo')).first()
            if(dados_localizacao is None):
                insert_query = text("INSERT INTO localizacao (id_dispositivo,latitude,longitude,qtd_faixas) VALUES (:id_disp, :lat, :long, :num_faixas)")
                db.engine.execute(insert_query, id_disp = data.get('id_dispositivo'), lat = data.get('latitude') , long = data.get('longitude'), num_faixas = data.get('qtd_faixas'))
                return jsonify(data),201
            return jsonify({'mensagem':'Localizacao ja cadastrada'})
        return jsonify({'error':'dispositivo nao cadastrado'})
    return jsonify({'error':'Enviado um JSON vazio'})

@app.route('/API/atualizar_localizacao/<id_disp>',methods=['PUT'])
def atualizar_localizacao(id_disp):
    data = request.get_json()
    if(data):
        localizacao_update = localizacao.query.filter_by(id_dispositivo = id_disp).first()
        if(localizacao_update is not None):
            localizacao_update.latitude = data.get('latitude')
            localizacao_update.longitude = data.get('longitude')
            localizacao_update.data_realocacao = data.get('data_realocacao')
            db.session.commit()
            return jsonify(data),200
        return jsonify({'error':'dispositivo não localizado'})
    else:
        return jsonify({'error':'JSON vazio'})

#Fim definição da API

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

@app.route('/usuarios',methods=('GET','POST'))
@login_required
def usuarios():
    if request.method == "GET":
        lista_usuarios = usuario.query.filter_by(ativo=1)
        return render_template('usuarios.html',usuarios=lista_usuarios)
    if request.method == "POST":
        id_inativar = request.form.get('inativar')
        id_update = request.form.get('atualizar')
        if id_inativar is not None:
            inativa_usuario = usuario.query.filter_by(id=id_inativar).first()
            inativa_usuario.ativo = 0
            db.session.commit()
            return redirect('usuarios')
        if id_update is not None:
           usuario_to_update = usuario.query.filter_by(id = id_update).first()
           session['u_id'] = usuario_to_update.id
           session['u_nome'] = usuario_to_update.nome
           session['u_cpf'] = usuario_to_update.cpf
           session['u_telefone'] = usuario_to_update.telefone
           session['u_email'] = usuario_to_update.email
           session['u_perfil'] = usuario_to_update.id_perfil
           return redirect('atualizar_cadastro_usuario')
    return redirect('login')
@app.route('/atualizar_cadastro_usuario',methods=('GET','POST'))
@login_required
def atualizar_cadastro_usuario():
    if request.method == 'GET':
        if session.get('u_nome') is not None:
            nome_up = session.get('u_nome')
            cpf_up = session.get('u_cpf')
            telefone_up = session.get('u_telefone')
            email_up = session.get('u_email')
            perfil_up = session.get('u_perfil')
            lista_perfis = perfil.query.all()
            return render_template('atualizar_cadastro_usuario.html',nome = nome_up, cpf = cpf_up, telefone = telefone_up, email = email_up, perfis = lista_perfis)
    if request.method == 'POST':
        nome = request.form['marca_modelo']
        cpf = request.form['cpf']
        telefone = request.form['telefone']
        email = request.form['email']
        perfil_id = request.form['perfil']
        usuario_update = usuario.query.filter_by(id = session.get('u_id')).first()
        usuario_update.nome = nome
        usuario_update.cpf = cpf
        usuario_update.telefone = telefone
        usuario_update.email = email
        usuario_update.id_perfil = perfil_id
        db.session.commit()
        session.pop('u_id',None)
        session.pop('u_nome',None)
        session.pop('u_cpf',None)
        session.pop('u_telefone',None)
        session.pop('u_perfil',None)
        return redirect('usuarios')



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
        session.pop('marca_modelo',None)
        return redirect('/')
#    return render_template('atualizar_cadastro_dispositivo.html',id = id_up, marca = marca_up)

@app.route('/register', methods=('GET', 'POST')) 
def register():
    if request.method == 'POST':
        nome_f = request.form['nome']
        cpf_f = request.form['cpf']
        email_f = request.form['email']
        telefone_f = request.form['telefone']
        username = request.form['username']
        password = request.form['password']
        id_perfil_f = request.form['perfil']
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
            insert_query = text("INSERT INTO usuario (nome, cpf,telefone, email, username, password, ativo, id_perfil) VALUES (:nome, :cpf, :telefone, :email,:usuario, :senha, 1, :id_perfil)")
            db.engine.execute(insert_query, nome=nome_f, cpf=cpf_f, telefone=telefone_f, email=email_f, id_perfil = id_perfil_f, usuario = username, senha = password)
            return redirect('/')
        flash(error)
    lista_perfis = perfil.query.all()
    return render_template('register.html',perfis=lista_perfis) 
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
            session['perfil_id'] = user['id_perfil']
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

@app.route('/graphs/<id_d>/<tipo_graf>',methods=('GET', 'POST'))
#@app.route('/graphs/<id_d>/<tipo_graf>/<datas>') 
@login_required 
def graphs(id_d,tipo_graf):
    datas = None

    #Se o botão de filtro de datas for utilizado
    if request.method == 'POST':
        if 'dataEspecifica' in request.form:
            datas = request.form['dataEspecifica']
            contagem_por_data = text("SELECT * from contagem where numero_faixa= :num_faixa and id_dispositivo = :id_disp and cast(data_hora as date) = :data ORDER BY data_hora")
        elif 'intervaloDatas' in request.form:
            dataInicial = request.form['dataInicial']
            dataFinal = request.form['dataFinal']
            datas = dataInicial + ' - ' + dataFinal
            contagem_por_data = text("SELECT * from contagem where numero_faixa= :num_faixa and id_dispositivo = :id_disp and cast(data_hora as date) BETWEEN :dtInicial and :dtFinal ORDER BY data_hora")

    #Acessand oas informações de localização do dispositivo atual
    localizacao_disp = localizacao.query.filter_by(id_dispositivo = id_d).first()
    
    #pegando o dicionario do endereco
    local_dict = (geolocator.reverse(localizacao_disp.latitude + "," + localizacao_disp.longitude)).raw['address']
    local = local_dict['road'] + ", " + local_dict['suburb'] + " - " + local_dict['city'] + "/" + local_dict['state']
        
    #pegando todos os dispositivos que possuem contagem
    dispositivos_com_contagem = contagem.query.with_entities(contagem.id_dispositivo).distinct()
    locais = []
    for disp in dispositivos_com_contagem:
        locais_disp = localizacao.query.filter_by(id_dispositivo = disp.id_dispositivo).first()
        locais_dict = (geolocator.reverse(locais_disp.latitude + "," + locais_disp.longitude)).raw['address']
        locais.append((disp.id_dispositivo,locais_dict['road'] + ", " + locais_dict['suburb'] + " - " + locais_dict['city']))

    #cada via possui no mínimo duas faixas
    if datas is None:
        lista1 = contagem.query.filter_by(numero_faixa = 1,id_dispositivo = id_d).order_by('data_hora')
        lista2 = contagem.query.filter_by(numero_faixa = 2,id_dispositivo = id_d)
    else:
        if 'dataEspecifica' in request.form:
            lista1 = db.engine.execute(contagem_por_data, num_faixa = 1, id_disp = id_d,data = datas)
            lista2 = db.engine.execute(contagem_por_data, num_faixa = 2, id_disp = id_d,data = datas)
        else :
            lista1 = db.engine.execute(contagem_por_data, num_faixa = 1, id_disp = id_d,dtInicial = dataInicial,dtFinal = dataFinal )
            lista2 = db.engine.execute(contagem_por_data, num_faixa = 2, id_disp = id_d,dtInicial = dataInicial,dtFinal = dataFinal )

    #Preparação dos dados para gerar o gráfico
    eixo_x_list = []
    eixo_y_list1 = []
    eixo_y_list2 = []
    for registro in lista1:
        horario = registro.data_hora.strftime("%H") + ":" + registro.data_hora.strftime("%M")
        data = registro.data_hora.strftime("%d") + "/" + registro.data_hora.strftime("%m") + "/" + registro.data_hora.strftime("%Y") 
        eixo_x_list.append(horario + '\n' + data)
        eixo_y_list1.append(registro.quantidade)
    for registro in lista2:
        eixo_y_list2.append(registro.quantidade)

    #Se houver uma terceira faixa
    if(localizacao_disp.qtd_faixas == 3):
        if datas is None:
            lista3 = contagem.query.filter_by(numero_faixa = 3,id_dispositivo = id_d)
        else:
            if 'dataEspecifica' in request.form:
                lista3 = db.engine.execute(contagem_por_data, num_faixa = 3, id_disp = id_d,data = datas)
            else :
                lista3 = db.engine.execute(contagem_por_data, num_faixa = 3, id_disp = id_d,dtInicial = dataInicial,dtFinal = dataFinal )
           
        eixo_y_list3 = []
        for registro in lista3:
            eixo_y_list3.append(registro.quantidade)
        graph_url = build_graph3(eixo_x_list,eixo_y_list1,eixo_y_list2,eixo_y_list3,data,tipo_graf)
    else:
        graph_url = build_graph(eixo_x_list,eixo_y_list1,eixo_y_list2,data,tipo_graf)
        
    session['id_dispositivo'] = str(request.path).split('/')[2]
    session['tipo_graf_escolhido'] = str(request.path).split('/')[3]
    return render_template('graphs.html',graph1 = graph_url, localizacao = local,lista_locais = locais ) 

@app.route('/mapa') 
@login_required 
def mapa():
    lista_coordenadas = localizacao.query.all()
    start_coords = (-5.834575, -35.2207787) #Coordenadas de Natal
    folium_map = folium.Map(location=start_coords, zoom_start=13)
    for coordenadas in lista_coordenadas:
        #site = url_for('graphs') + '/' + coordenadas.id_dispositivo + '/bar'
        site = url_for('graphs',id_d = coordenadas.id_dispositivo, tipo_graf = 'bar')
        html = " <a href= '" + site + "' target='_blank'>Ver gráficos</a>"
        folium.Marker(location = (float((coordenadas.latitude).replace(',','.')),float((coordenadas.longitude).replace(',','.'))),popup=folium.Popup(html), icon=folium.Icon(color='green')).add_to(folium_map) #Adicionando uma marcação no mapa
    #folium.Marker(location = (-5.8112895,-35.2084236),popup=folium.Popup(html), icon=folium.Icon(color='green')).add_to(folium_map)#Adicionando uma marcação no mapa
    folium_map.save('templates/folium.html')
    return render_template('mapa.html')
    #return folium_map._repr_html_()
