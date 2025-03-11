import random
from gtts import gTTS
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont
import google.auth
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import json
import os
import google_auth_oauthlib.flow  # Importação necessária

# Função para gerar áudio da oração
def gerar_audio(texto, nome_arquivo):
    tts = gTTS(text=texto, lang='pt', slow=False)
    tts.save(nome_arquivo)

# Função para criar uma imagem com o texto
def criar_imagem(texto, nome_arquivo):
    img = Image.new('RGB', (1280, 720), color=(73, 109, 137))  # Cor de fundo
    d = ImageDraw.Draw(img)
    font_size = 200  # Tamanho inicial da fonte (grande)
    font = ImageFont.truetype("arial.ttf", font_size)  # Carregar a fonte com o tamanho inicial
    
    # Usar textbbox para calcular a largura e altura do texto
    bbox = d.textbbox((0, 0), texto, font=font)  # Calculando o tamanho do texto
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]  # Largura e altura do texto

    # Ajustar a fonte para que o texto caiba na largura da imagem
    while text_width > img.width - 40 and font_size > 35:  # Definir limite mínimo de 35 para o tamanho da fonte
        font_size -= 5  # Reduzir o tamanho da fonte em 5
        font = ImageFont.truetype("arial.ttf", font_size)  # Atualizar a fonte
        bbox = d.textbbox((0, 0), texto, font=font)  # Recalcular o tamanho do texto
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]  # Recalcular a largura e altura do texto

    # Quebrar o texto em múltiplas linhas
    linhas = []
    palavras = texto.split(' ')
    linha_atual = ""
    for palavra in palavras:
        if len(linha_atual + " " + palavra) < 35:  # Máximo de 35 caracteres por linha (ajustado)
            linha_atual += " " + palavra
        else:
            linhas.append(linha_atual.strip())
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual.strip())

    # Centralizar as linhas na imagem
    y_position = (img.height - len(linhas) * font_size) // 2
    for linha in linhas:
        bbox = d.textbbox((0, 0), linha, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        position = ((img.width - text_width) // 2, y_position)
        d.text(position, linha, fill=(255, 255, 255), font=font)
        y_position += text_height + 10  # Espaço entre as linhas

    img.save(nome_arquivo)

# Função para criar o vídeo a partir de imagens e áudio
def criar_video(imagens, audios, som_fundo_path, arquivo_saida):
    clips = []
    
    # Carregar som de fundo
    som_fundo = AudioFileClip(som_fundo_path)
    
    for i, img in enumerate(imagens):
        duracao_audio = AudioFileClip(audios[i]).duration  # Obter duração do áudio
        duracao_fundo = AudioFileClip(som_fundo_path).duration  # Duração do som de fundo
        
        # Caso o som de fundo seja mais longo que o áudio
        if duracao_fundo > duracao_audio:
            som_fundo = som_fundo.subclip(0, duracao_audio)  # Cortar som de fundo
        
        clip = ImageClip(img).set_duration(duracao_audio)  # Duração da imagem igual à do áudio
        clips.append(clip)

    # Concatenar os clips de imagem
    video = concatenate_videoclips(clips, method="compose")
    
    # Juntar os arquivos de áudio
    audio_clips = [AudioFileClip(audio) for audio in audios]
    audio_final = concatenate_audioclips(audio_clips)
    
    # Ajustar o volume do som de fundo
    som_fundo = som_fundo.volumex(0.2)  # Diminuir volume do som de fundo para 20% do volume original
    
    # Estender o som de fundo para 10 segundos após o final do último áudio
    duracao_video = audio_final.duration  # Duração total do áudio (da oração)
    som_fundo_extendido = som_fundo.subclip(0, duracao_video + 10)  # Adicionar 10 segundos após o áudio
    
    # Definir o áudio do vídeo como as trilhas separadas: áudio da oração + som de fundo
    video = video.set_audio(CompositeAudioClip([audio_final, som_fundo_extendido]))  # Mesclar os áudios

    video.write_videofile(arquivo_saida, fps=24)

# Função para ler orações do arquivo
def ler_oracoes_do_arquivo(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as file:
        oracoes = file.readlines()
    # Limpar as quebras de linha
    oracoes = [oracao.strip() for oracao in oracoes]
    return oracoes

# Função para obter a próxima sequência de orações
def obter_proxima_sequencia():
    caminho_progresso = "progress.json"
    
    if os.path.exists(caminho_progresso):
        with open(caminho_progresso, "r") as file:
            progresso = json.load(file)
        indice_atual = progresso["indice"]
    else:
        indice_atual = 0
    
    oracoes = ler_oracoes_do_arquivo("C:\\Users\\Tiago\\Desktop\\oracoes.txt")
    total_oracoes = len(oracoes)
    
    sequencia = []
    for i in range(3):
        sequencia.append(oracoes[(indice_atual + i) % total_oracoes])
    
    novo_indice = (indice_atual + 3) % total_oracoes
    with open(caminho_progresso, "w") as file:
        json.dump({"indice": novo_indice}, file)
    
    return sequencia

# Função para obter credenciais do YouTube (ou carregar existentes)
def obter_credenciais_youtube():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    CREDENTIALS_FILE = "credentials.json"  # Caminho do arquivo para salvar as credenciais
    
    credentials = None
    
    # Verificar se o arquivo de credenciais existe
    if os.path.exists(CREDENTIALS_FILE):
        # Carregar as credenciais
        with open(CREDENTIALS_FILE, 'r') as token:
            credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
    
    # Se não tiver credenciais ou se elas estiverem expiradas
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Atualizar as credenciais se estiverem expiradas
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                "D:\\Tiago\\3- Projetos Coding\\Mensagem Divina\\AutoVidAI\\credentials.json", SCOPES
            )
            credentials = flow.run_local_server(port=8080)  # Solicitar autenticação se necessário

        # Salvar as credenciais no arquivo para o futuro
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(credentials.to_json())

    return credentials

def upload_video(credentials, video_file, title, description):
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    request = youtube.videos().insert(
        part="snippet, status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["orações", "cristianismo", "religião", "espiritualidade"],
            },
            "status": {
                "privacyStatus": "public",  # Vídeo configurado como público
            },
        },
        media_body=MediaFileUpload(video_file)
    )

    response = request.execute()  # Executa o upload
    print(f"Vídeo '{title}' Enviado pro youtube com sucesso! ID: {response['id']}")

# Função principal
def main():
    textos = obter_proxima_sequencia()  # Buscar as próximas 3 orações sequenciais
    imagens = []
    audios = []
    
    # Criar imagens e salvar áudio para cada oração
    for i, texto in enumerate(textos):
        nome_imagem = f"image_{i}.png"
        nome_audio = f"audio_{i}.mp3"
        criar_imagem(texto, nome_imagem)  # Criar imagem com a oração
        gerar_audio(texto, nome_audio)  # Gerar áudio da oração
        imagens.append(nome_imagem)
        audios.append(nome_audio)

    # Criar o vídeo
    arquivo_saida = "video_final.mp4"
    som_fundo_path = "C:\\Users\\Tiago\\Desktop\\fundo_oracao.mp3"  # Caminho para o arquivo de música de fundo
    criar_video(imagens, audios, som_fundo_path, arquivo_saida)
    
    # Fazer upload do vídeo para o YouTube
    credentials = obter_credenciais_youtube()
    title = "Oração do Dia"
    description = "Assista e reflita sobre a oração do dia."
    upload_video(credentials, arquivo_saida, title, description)

# Executar o script
if __name__ == "__main__":
    main()
