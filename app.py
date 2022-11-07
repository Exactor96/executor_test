import hashlib
import os
from typing import Any, Optional
import uuid
from fastapi import Form, File, UploadFile, FastAPI, Depends
from pydantic import BaseModel, Field
import subprocess

app = FastAPI()


DEFAULT_TIMEOUT = 300

EXECUTABLE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'executables'
)


if not os.path.exists(EXECUTABLE_PATH):
    os.mkdir(EXECUTABLE_PATH)


def save_executable(file):
    file_bytes = file.file.read()
    hashsum = hashlib.sha256(file_bytes).hexdigest()
    save_path = os.path.join(
        EXECUTABLE_PATH,
        hashsum
    )

    with open(save_path, 'wb') as f:
        f.write(file_bytes)
    os.chmod(save_path, 0o777)
    return hashsum, save_path


def run_executable_program(executable: str, args:tuple, timeout: int = DEFAULT_TIMEOUT):
    print(args)
    if args:
        completed_process = subprocess.run([f'{executable}', *args], capture_output=True, timeout=timeout)
    else:
        completed_process = subprocess.run([f'{executable}'], capture_output=True, timeout=timeout)
    return completed_process.returncode, completed_process.stdout, completed_process.stderr


@app.post("/api/send_job")
async def handle_job_send(
    name: Optional[str] = Form(None),
    executable_type: str = Form(...),
    executable: UploadFile = File(...),
    args: Optional[str] = Form(None)
):

    hashsum, save_path = save_executable(executable)

    if executable_type == 'program':
        exit_code, stdout, stderr = run_executable_program(save_path, args)

        return {'name': name, 'exit_code': exit_code, 'stdout': stdout, 'stderr': stderr}