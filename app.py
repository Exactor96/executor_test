import hashlib
import os
import subprocess
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, Request, Depends, Response

app = FastAPI()


DEFAULT_TIMEOUT = 300
TOKEN = os.environ['TOKEN']

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
    print(type(args))
    if args:
        completed_process = subprocess.run([f'{executable}', *args], capture_output=True, timeout=timeout)
    else:
        completed_process = subprocess.run([f'{executable}'], capture_output=True, timeout=timeout)
    return completed_process.returncode, completed_process.stdout, completed_process.stderr


def verify_token(request: Request) -> bool:
    
    user_token = request.headers.get('token')

    return user_token and user_token == TOKEN


@app.get('/ping')
async def ping():
    return {'message': 'pong'}


@app.post("/api/send_job")
async def handle_job_send(
    is_auth: bool = Depends(verify_token),
    name: Optional[str] = Form(None),
    executable_type: str = Form(...),
    executable: UploadFile = File(...),
    args: Optional[tuple[str]] = Form(None)
):
    if is_auth:
        return Response(status_code=401)

    hashsum, save_path = save_executable(executable)
    print(args)

    if executable_type == 'program':
        exit_code, stdout, stderr = run_executable_program(save_path, args)

        return {'name': name, 'exit_code': exit_code, 'stdout': stdout, 'stderr': stderr}
