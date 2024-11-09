from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydub import AudioSegment
import aiohttp
import uuid
import os
import subprocess
import shutil
from fastapi.responses import FileResponse
from typing import Dict

app = FastAPI()

# Diretorio para armazenar os arquivos convertidos
OUTPUT_DIR = "converted_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dicionário para armazenar o estado das conversões
conversion_tasks: Dict[str, str] = {}

class AudioLink(BaseModel):
    url: str

@app.post("/request-conversion/")
async def request_conversion(audio_link: AudioLink):
    # Gerar um ID único para a conversão
    task_id = str(uuid.uuid4())
    conversion_tasks[task_id] = "processing"

    # Salvar o arquivo MP3 temporariamente
    input_file_path = f"{task_id}.mp3"
    output_file_name = f"{task_id}.ogg"
    output_file_path = os.path.join(OUTPUT_DIR, output_file_name)

    try:
        # Baixar o arquivo MP3 da URL fornecida
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_link.url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Não foi possível baixar o arquivo MP3.")
                audio_data = await response.read()

        with open(input_file_path, "wb") as f:
            f.write(audio_data)

        # Verificar se o ffmpeg está disponível
        if not shutil.which("ffmpeg"):
            raise HTTPException(status_code=500, detail="ffmpeg não está instalado ou não está no PATH do sistema.")

        # Converter o arquivo MP3 para OGG usando ffmpeg
        command = [
            "ffmpeg", "-y", "-i", input_file_path,
            "-ac", "1", "-ar", "24000", "-c:a", "libopus", "-b:a", "256k",
            output_file_path
        ]
        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode != 0:
            conversion_tasks[task_id] = "failed"
            raise HTTPException(status_code=500, detail=f"Erro na conversão de áudio: {process.stderr}")

        # Atualizar o status da conversão para concluído
        conversion_tasks[task_id] = "completed"

        # Remover o arquivo MP3 temporário
        os.remove(input_file_path)
    except subprocess.CalledProcessError as e:
        conversion_tasks[task_id] = "failed"
        raise HTTPException(status_code=500, detail=f"Erro na conversão de áudio: {str(e)}")
    except Exception as e:
        conversion_tasks[task_id] = "failed"
        raise HTTPException(status_code=500, detail=str(e))

    return {"task_id": task_id}

@app.get("/get-conversion-status/{task_id}")
async def get_conversion_status(task_id: str):
    if task_id not in conversion_tasks:
        raise HTTPException(status_code=404, detail="ID da conversão não encontrado.")

    status = conversion_tasks[task_id]
    if status == "completed":
        output_file_name = f"{task_id}.ogg"
        return {"status": "completed", "converted_audio_url": f"http://127.0.0.1:8000/files/{output_file_name}"}
    elif status == "failed":
        return {"status": "failed", "detail": "Houve um erro na conversão do áudio."}
    else:
        return {"status": "processing"}

@app.get("/files/{file_name}")
async def get_converted_file(file_name: str):
    file_path = os.path.join(OUTPUT_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(file_path)

# Para rodar o servidor, utilize o comando:
# uvicorn app:app --reload
# Certifique-se de substituir "app" pelo nome do arquivo Python onde este script está salvo.
