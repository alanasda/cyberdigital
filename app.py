from flask import Flask, request, jsonify
from supabase import create_client, Client
from flask_cors import CORS
import yagmail

app = Flask(__name__)
CORS(app)

# Supabase config
SUPABASE_URL = "https://szbptsuvjmaqkcgsgagx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN6YnB0c3V2am1hcWtjZ3NnYWd4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNjA3MjEsImV4cCI6MjA1OTczNjcyMX0.wqjSCJ8evNog5AnP2dzk1t2nkn31EfvqDuaAkXDiqNo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# E-mail config
EMAIL_REMETENTE = "cyberdigitalsuporte@gmail.com"
EMAIL_SENHA_APP = "ufvz jkdc ihpu ksak"

# PING
@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

# REGISTRO
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")

    if not nome or not email or not senha:
        return jsonify({"success": False, "message": "Todos os campos são obrigatórios."}), 400

    # Verifica se email já existe
    exists = supabase.table("usuarios").select("email").eq("email", email).execute()
    if exists.data:
        return jsonify({"success": False, "message": "Email já cadastrado."}), 409

    supabase.table("usuarios").insert({
        "nome": nome,
        "email": email,
        "senha": senha,
        "modulos": [],
        "pagamento_confirmado": False
    }).execute()

    return jsonify({"success": True, "message": "Conta criada com sucesso!"}), 201

# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"success": False, "message": "Email e senha são obrigatórios"}), 400

    result = supabase.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
    user = result.data[0] if result.data else None

    if not user:
        return jsonify({"success": False, "message": "Email ou senha inválidos"}), 401

    return jsonify({
        "success": True,
        "email": user["email"],
        "nome": user.get("nome", ""),
        "modulos": user.get("modulos", [])
    })

# WEBHOOK de liberação (ex: após compra na Kirvano)
@app.route("/webhook/<int:modulo_id>", methods=["POST"])
def webhook_envio(modulo_id):
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "Email é obrigatório"}), 400

    # Envia e-mail com link de login
    link_login = "https://seudominio.com/login.html"
    corpo = f'''
    <h2>Seu acesso ao módulo foi liberado!</h2>
    <p><strong>Módulo:</strong> {modulo_id}</p>
    <p>Clique abaixo para criar ou acessar sua conta:</p>
    <a href="{link_login}" style="padding: 10px 20px; background: #00ffff; color: black; border-radius: 8px; text-decoration:none;">
        Entrar na Plataforma
    </a>
    '''

    try:
        yag = yagmail.SMTP(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        yag.send(to=email, subject="Acesso Liberado - CYBER.DIGITAL", contents=corpo)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    # Atualiza ou cria usuário com módulo liberado
    result = supabase.table("usuarios").select("*").eq("email", email).execute()
    user = result.data[0] if result.data else None

    if user:
        modulos = user.get("modulos", [])
        if modulo_id not in modulos:
            modulos.append(modulo_id)
        supabase.table("usuarios").update({"modulos": modulos}).eq("email", email).execute()
    else:
        supabase.table("usuarios").insert({
            "email": email,
            "nome": "Usuário",
            "senha": "senha-temporaria",  # pode forçar troca depois
            "modulos": [modulo_id],
            "pagamento_confirmado": True
        }).execute()

    return jsonify({"success": True, "message": f"Acesso ao módulo {modulo_id} enviado para {email}."})

# INÍCIO
@app.route("/", methods=["GET"])
def home():
    return "API da CYBER.DIGITAL está ativa ✅"

if __name__ == "__main__":
    app.run(debug=True)
