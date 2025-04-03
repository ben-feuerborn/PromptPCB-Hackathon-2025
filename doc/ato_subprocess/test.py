import subprocess

# Python script to run 'ato create' and automatically provide answers to questions
def run_ato_create(ato_project_name):
    command = "bash -c 'mkdir -p build && cd build && source /home/bix/Hackathon2025/app/venv/bin/activate && ato create'"
    answers = f"project\n{ato_project_name}\nn\n"

    try:
        process = subprocess.Popen(
            command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(input=answers)

        print("Output:", stdout)
        if stderr:
            print("Error:", stderr)

    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)

def build_and_view_project(project_name):
    build_command = f"bash -c 'cd build/{project_name} && source /home/bix/Hackathon2025/app/venv/bin/activate && ato build'"
    view_command = f"bash -c 'cd build/{project_name} && source /home/bix/Hackathon2025/app/venv/bin/activate && tmux new-session -d -s ato_view_session \"ato view\"'"

    try:
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

        print("ato view is running in tmux session 'ato_view_session'")

    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)

if __name__ == "__main__":
    # run_ato_create("test")
    build_and_view_project("test")