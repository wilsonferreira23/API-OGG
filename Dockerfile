FROM python:3.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY install_ffmpeg.sh install_ffmpeg.sh
RUN chmod +x install_ffmpeg.sh && ./install_ffmpeg.sh

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
