

import socket
import mysql.connector
#from geopy.geocoders import Nominatim

HOST = '0.0.0.0' #socket.gethostbyname(socket.gethostname())  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

#geolocator = Nominatim(user_agent="OpenCVTest")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	s.bind((HOST, PORT))
	s.listen()
	while True:
		print("Aguardando conexão no endereço:", HOST," na porta: ",PORT)
		conn, addr = s.accept()
		with conn:
			print('Connected by', addr)
			data = conn.recv(4096) #recebe os dados em formato de bytes
			data = data.decode("utf-8") #converte os dados para o fomrato de texto
			data_tuple = tuple(map(str,data.split(",")))
			print(len(data_tuple))
			connection = mysql.connector.connect(user='socket.server', password='s0ck3ts3rv3r',host='localhost',port=3306,database='frutas',)
			cur = connection.cursor(buffered=True)

			if len(data_tuple) == 4:
				IMEI = data_tuple[0]
				latitude = data_tuple[1]
				longitude = data_tuple[2]
				flag_realocacao = data_tuple[3]
				#print(IMEI, " ", latitude, " ", longitude, " ", flag_realocacao)
				print("IMEI=",IMEI)
				print("latitude=",latitude)
				cur_insert_localizacao = connection.cursor(buffered=True)
				cur_update_localizacao = connection.cursor(buffered=True)
				cur_search_localizacao = connection.cursor(buffered=True)
			
				query_busca_dispositivo = "SELECT * FROM dispositivos where id=" + IMEI
				query_busca_disp_localizacao = "SELECT * FROM localizacao where id_dispositivo=" + IMEI
				query_insert_localizacao = "INSERT INTO localizacao VALUES ( %s, %s, %s)"
				query_update_localizacao = "UPDATE localizacao SET latitude = %s, longitude = %s WHERE id_dispositivo = %s"

				cur.execute(query_busca_dispositivo)
				cur_search_localizacao.execute(query_busca_disp_localizacao)

				if cur is not None: #indica que o dispositivo esta cadastrado
					if cur_search_localizacao is not None:  #indica que ja existe uma localizacao para o dispositivo
						if flag_realocacao == '1': #indica realocacao
							cur_update_localizacao.execute(query_update_localizacao,(latitude,longitude,IMEI))
							connection.commit()
						else:
							print("Dispositivo ja possui localizacao. Realocação não informada")
					else:
						cur_insert.execute(query_insert_localizacao,(IMEI,latitude,longitude))
						connection.commit()
				else:
					print("Dispositivo não cadastrado")
			connection.close()
			#connection.commit()
			#cur.execute("SELECT * from frutas")
			#latitude = data_tuple[0]
			#longitude=data_tuple[1]
			#localizacao = str(geolocator.reverse(latitude + "," + longitude))
			#print(localizacao.split(", Natal")[0])

