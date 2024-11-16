from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socket_io = SocketIO(app)

usuarios_conectados = {}
mensagens = []

@app.route("/")
def home():
    return render_template("chat.html")

@socket_io.on('enviarNome')
def receber_nome(data):
    nome = data['nome']
    ip_cliente = request.remote_addr
    porta_cliente = request.environ.get('REMOTE_PORT')
    usuarios_conectados[nome] = {
        'sid': request.sid,
        'ip': ip_cliente,
        'porta': porta_cliente
    }

    print(f"Cliente conectado: Nome {nome}, IP {ip_cliente}, Porta {porta_cliente}")
    
    emit("historicoMensagens", mensagens)

@socket_io.on('disconnect')
def desconectar():
    for nome, dados in list(usuarios_conectados.items()):
        if dados['sid'] == request.sid:
            mensagens.append({"nome": "Chat", "mensagem": f"{nome} saiu do chat!"})
            emit("receberMensagem", {"nome": "Chat", "mensagem": f"{nome} saiu do chat!"}, broadcast=True)
            print(f"Cliente desconectado: Nome: {nome}, IP: {dados['ip']}, Porta: {dados['porta']}")
            del usuarios_conectados[nome]
            break

@socket_io.on('enviarMensagem')
def receber_mensagem(msg):
    nome = msg['nome']
    mensagem = msg['mensagem']

    if mensagem.strip() == "/sair":
        if nome in usuarios_conectados:
            mensagens.append({"nome": "Chat", "mensagem": f"{nome} saiu do chat!"})
            emit("receberMensagem", {"nome": "Chat", "mensagem": f"{nome} saiu do chat!"}, broadcast=True)
            del usuarios_conectados[nome]
            
            ip_cliente = request.remote_addr
            porta_cliente = request.environ.get('REMOTE_PORT')
            
            print(f"Cliente desconectado: Nome: {nome}, IP: {ip_cliente}, Porta: {porta_cliente}.")
            
            emit("usuarioSaiu", {"nome": nome}, room=request.sid)
            return

    if mensagem.startswith('/'):
        destinatario, _, mensagem_privada = mensagem[1:].partition(" ")
        if destinatario in usuarios_conectados:
            emit("receberMensagem", {"nome": f"{nome} (privado)", "mensagem": mensagem_privada}, room=usuarios_conectados[destinatario]["sid"])
            emit("receberMensagem", {"nome": f"{nome} (privado)", "mensagem": mensagem_privada}, room=usuarios_conectados[nome]["sid"])
            return
        else:
            emit("receberMensagem", {"nome": "Chat", "mensagem": f"Usuário {destinatario} não está conectado."}, room=request.sid)
            return

    mensagens.append(msg)
    emit("receberMensagem", msg, broadcast=True)



if __name__ == "__main__":
    socket_io.run(app, host='0.0.0.0', port=5000, debug=True)
