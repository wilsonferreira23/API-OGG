FROM python:3.9

WORKDIR /app

# Copiar os arquivos necessários
COPY requirements.txt requirements.txt
COPY install_ffmpeg.sh install_ffmpeg.sh

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Tornar o script de instalação do ffmpeg executável e executá-lo
RUN chmod +x install_ffmpeg.sh && ./install_ffmpeg.sh

# Copiar o restante dos arquivos
COPY . .

# Executar o FastAPI usando o Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

