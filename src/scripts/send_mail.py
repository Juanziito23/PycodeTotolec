import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import ssl
import base64

def load_config():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.json')
        
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(script_dir), 'config.json')
            
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'config.json')

        with open(config_path, 'r', encoding='utf-8') as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return None

def custom_login(server, username, password):
    """Implementação manual do processo de login SMTP"""
    auth_string = f"\x00{username}\x00{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    server.docmd("AUTH", f"PLAIN {auth_b64}")

# Carregar as configurações
config = load_config()
if not config:
    exit("Erro ao carregar configurações. Verifique o arquivo config.json")

# Configurações do servidor SMTP
SMTP_SERVER = "smtp-out.flockmail.com"  # Usando o servidor que apareceu no log
SMTP_PORT = 587
EMAIL_USER = config.get("email_user")
EMAIL_PASSWORD = config.get("email_password")

def send_test_email():
    try:
        context = ssl.create_default_context()
        
        print(f"Conectando ao servidor {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)
        
        print("Iniciando TLS...")
        server.starttls(context=context)
        
        print("Enviando EHLO após TLS...")
        server.ehlo()
        
        print("Tentando autenticação...")
        try:
            custom_login(server, EMAIL_USER, EMAIL_PASSWORD)
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"Erro de autenticação: {auth_error}")
            print("Tentando método alternativo de autenticação...")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        print("Autenticação bem-sucedida!")
        
        # Enviando email de teste
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER  # Enviando para si mesmo como teste
        msg['Subject'] = "Teste de Conexão"
        
        body = "Este é um email de teste para verificar a conexão SMTP."
        msg.attach(MIMEText(body, 'plain'))
        
        print("Enviando email de teste...")
        server.send_message(msg)
        print("Email de teste enviado com sucesso!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"\nErro detalhado:")
        print(f"Tipo de erro: {type(e).__name__}")
        print(f"Mensagem de erro: {str(e)}")
        if hasattr(e, 'smtp_code'):
            print(f"Código SMTP: {e.smtp_code}")
        if hasattr(e, 'smtp_error'):
            print(f"Erro SMTP: {e.smtp_error}")
        return False

# Executar teste
print("Iniciando teste de conexão...")
if send_test_email():
    print("\nTeste completado com sucesso!")
else:
    print("\nTeste falhou!")
    print("\nVerifique as seguintes possibilidades:")
    print("1. Confirme se a senha está correta (sem espaços extras)")
    print("2. Verifique se você pode fazer login no webmail")
    print("3. Confirme se o endereço de email está correto")
    print("4. Verifique se o servidor está correto")
    print("5. Tente gerar uma senha de aplicativo específica no painel de controle do Titan")
    print("\nSe o problema persistir, entre em contato com o suporte do Titan Email")