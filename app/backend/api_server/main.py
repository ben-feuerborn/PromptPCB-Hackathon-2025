import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
from dotenv import load_dotenv, find_dotenv
import subprocess
import re

import os

# Get the absolute path to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build the path to the virtual environment activate script
venv_activate_path = os.path.abspath(os.path.join(BASE_DIR, "../../venv/bin/activate"))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
venv_activate_path = os.path.abspath(os.path.join(BASE_DIR, "../../venv/bin/activate"))
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI!"}

class PromptRequest(BaseModel):
    prompt: str

@app.post("/prompt")
async def generate_prompt_response(request: PromptRequest):
    try:
        result = await get_openai_response(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"response": result}


class ProjectRequest(BaseModel):
    project_name: str
    source_ato: str


@app.post("/create_project")
async def create_project(request: ProjectRequest):
    kill_tmux_cmd = "tmux kill-session -t ato_view_session || true"
    wipe_build_cmd = "rm -rf build"
    create_project_cmd = (
        f"bash -c 'mkdir -p build && cd build && source {venv_activate_path} && ato create'"
    )

    answers = f"project\n{request.project_name}\nn\n"

    try:
        # Step 1: Kill tmux session (ignore errors if session doesn't exist)
        subprocess.run(kill_tmux_cmd, shell=True, check=False)

        # Step 2: Wipe the existing build directory
        subprocess.run(wipe_build_cmd, shell=True, check=True)

        # Step 3: Run ato create and pass answers via stdin
        process = subprocess.Popen(
            create_project_cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate(input=answers)

        if process.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ato create command failed",
                    "stderr": stderr.strip(),
                    "stdout": stdout.strip()
                },
            )

        return {"output": stdout.strip()}

    except subprocess.CalledProcessError as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail={"error": "Subprocess failed", "details": str(e)}
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

import os

@app.post("/build_view_project")
async def build_view_project(request: ProjectRequest):
    project_path = f"build/{request.project_name}/elec/src"
    ato_file_path = os.path.join(project_path, f"{request.project_name}.ato")

    try:
        # Ensure the directory exists
        if not os.path.exists(project_path):
            raise HTTPException(status_code=400, detail=f"Project directory {project_path} does not exist.")

        updated_source_ato = capitalize_module_word(request.source_ato)

        # Write the provided source_ato to the .ato file
        with open(ato_file_path, 'w') as f:
            f.write(updated_source_ato)
        print(f"Replaced {ato_file_path} with provided source_ato")

        # Run build and view commands
        build_command = f"bash -c 'cd build/{request.project_name} && source {venv_activate_path} && ato build'"
        view_command = f"bash -c 'cd build/{request.project_name} && source {venv_activate_path} && tmux new-session -d -s ato_view_session \"ato view\"'"

        build_process = subprocess.Popen(
            build_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = build_process.communicate()
        print("Build Output:", stdout)
        if stderr:
            print("Build Error:", stderr)

        view_process = subprocess.Popen(
            view_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        view_stdout, view_stderr = view_process.communicate()
        if view_stdout:
            print("View Output:", view_stdout)
        if view_stderr:
            print("View Error:", view_stderr)

        return {
            "build_output": stdout,
            "build_error": stderr,
            "view_output": view_stdout,
            "view_error": view_stderr,
            "message": f"Ato view is running in tmux session 'ato_view_session'. Updated {ato_file_path}."
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

def capitalize_module_word(ato_content: str) -> str:
    """
    Find occurrences of 'module <word>' and ensure the first letter
    of <word> is capitalized. The rest of <word> is unchanged.
    E.g. 'module project' -> 'module Project'
    """
    pattern = r'(module\s+)([a-zA-Z])(\S*)'
    
    def _replacer(match):
        prefix = match.group(1)         # "module "
        first_letter = match.group(2)   # first letter of the next word
        rest_of_word = match.group(3)   # the remainder of the word
        return f"{prefix}{first_letter.upper()}{rest_of_word}"

    return re.sub(pattern, _replacer, ato_content)
    
@app.post("/stop_view_session")
async def stop_view_session():
    stop_command = "tmux kill-session -t ato_view_session"

    try:
        process = await asyncio.create_subprocess_shell(
            stop_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            text=True
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Error: {stderr.strip()}")

        return {"message": "tmux session 'ato_view_session' has been terminated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
import os
import shutil
import tempfile
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse

@app.get("/export")
async def export_project(
    project_name: str = Query(..., description="Project name to export")
):
    # Paths to export
    layout_dir = os.path.join("build", project_name, "elec", "layout", "default")
    net_file = os.path.join("build", project_name, "build", "default.net")

    # Output .zip
    zip_file_path = os.path.join("build", project_name, f"{project_name}_export.zip")

    try:
        # 1. Confirm both the layout directory and the .net file exist
        if not os.path.exists(layout_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Layout directory not found: {layout_dir}"
            )
        if not os.path.exists(net_file):
            raise HTTPException(
                status_code=400,
                detail=f"Net file not found: {net_file}"
            )

        # 2. Copy them into a temporary folder
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the layout folder
            temp_layout = os.path.join(temp_dir, "default_layout")
            shutil.copytree(layout_dir, temp_layout)

            # Copy the .net file
            shutil.copy2(net_file, os.path.join(temp_dir, "default.net"))

            # 3. Create the archive from the temp directory
            archive_base = zip_file_path.rsplit(".zip", 1)[0]
            shutil.make_archive(archive_base, 'zip', temp_dir)
            print(f"Exported {layout_dir} and {net_file} to {zip_file_path}")

        # 4. Return the ZIP
        return FileResponse(
            path=zip_file_path,
            filename=os.path.basename(zip_file_path),
            media_type="application/zip"
        )

    except Exception as e:
        print(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
