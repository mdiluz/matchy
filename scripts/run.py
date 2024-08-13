import sys
import git
import subprocess

# Pull the release branch
repo = git.Repo(search_parent_directories=True)
if repo.active_branch.name != "release":
    print(f"Refusing to run on branch '{repo.active_branch.name}'")
    sys.exit(1)
repo.remotes.origin.pull()

# Install any new pip requirements
subprocess.run([sys.executable, "-m", "pip", "install",
               "-r", "requirements.txt"], check=True)

# Run Matchy!
subprocess.run([sys.executable, "py/matchy.py"], check=True)
