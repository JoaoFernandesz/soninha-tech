from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
import json

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os

app = Flask(__name__)

print(os.urandom(16))

app.secret_key = os.urandom(16)

def obter_telefone_usuario(nome_usuario):
    with open('usuarios.csv', mode='r') as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            if linha['nome'] == nome_usuario:
                return linha['telefone']
    return None 


def verificar_usuario(nome, telefone):
    with open('usuarios.csv', mode='r') as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            if linha['nome'] == nome or linha['telefone'] == telefone:
                return linha['nome']  # Retorna o identificador do usuário
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        usuario = verificar_usuario(nome, telefone)
        if usuario:
            session['usuario_id'] = usuario  # Armazena o identificador na sessão
            return redirect(url_for('lista_produtos'))
        else:
            mensagem = "Telefone ou nome não encontrado."
            return render_template('index.html', mensagem=mensagem)
    return render_template('index.html', mensagem='')

@app.route('/produtos')
def lista_produtos():
    path = os.path.join(os.getcwd(), 'produtos.json')
    print(f'Tentando abrir o arquivo em: {path}')
    with open('produtos.json', 'r') as f:
        produtos = json.load(f)
    return render_template('produtos.html', produtos=produtos)

@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    if 'usuario_id' not in session:
        return redirect(url_for('home')) 

    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade'))
    usuario_id = session['usuario_id']

    if 'carrinho' not in session:
        session['carrinho'] = {}
    
    if usuario_id not in session['carrinho']:
        session['carrinho'][usuario_id] = []

    session['carrinho'][usuario_id].append({'produto_id': produto_id, 'quantidade': quantidade})
    
    session.modified = True
    
    return redirect(url_for('lista_produtos'))


@app.route('/finalizar_compra')
def finalizar_compra():
    if 'usuario_id' not in session or 'carrinho' not in session or session['usuario_id'] not in session['carrinho']:
        return redirect(url_for('home'))

    usuario_id = session['usuario_id']
    carrinho = session['carrinho'][usuario_id]
    
    
    total = 0
    for item in carrinho:
        # tem que fazer o calculo aq
        
        produto_preco = 10  # simulação
        total += item['quantidade'] * produto_preco
    
    return render_template('finalizar_compra.html', carrinho=carrinho, total=total)


def obter_preco_produto(produto_id):
    return 10  # simulação

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'usuario_id' not in session or 'carrinho' not in session or session['usuario_id'] not in session['carrinho']:
        return redirect(url_for('home'))  
    
    usuario_id = session['usuario_id']
    carrinho = session['carrinho'][usuario_id]
    total = sum(item['quantidade'] * obter_preco_produto(item['produto_id']) for item in carrinho)
    

    telefone = obter_telefone_usuario(usuario_id)
    
    data = {
        'nome': usuario_id,
        'telefone': telefone,
        'valor': total,
        'produtos': carrinho 
    }
    
    web_app_url = 'https://script.google.com/macros/s/AKfycbzF-v1kMobc8ZHM5oCVvxi2stszEuDpaoTOidgEweVUdpLXEVyESbZ_r8n-nbPPrxbDXg/exec'
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(web_app_url, json=data, headers=headers)
    
    if response.status_code == 200:
        # Limpa o carrinho após a finalização da compra
        del session['carrinho'][usuario_id]
        session.modified = True
        
        return jsonify({'result': 'success', 'data': response.text}), 200
    else:
        return jsonify({'result': 'error', 'data': 'Failed to send data to Google Sheets'}), 500



if __name__ == '__main__':
    app.run(debug=True)
