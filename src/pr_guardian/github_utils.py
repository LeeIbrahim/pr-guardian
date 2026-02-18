# src/pr_guardian/github_utils.py
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

def fetch_commit_files(repo_name: str, commit_sha: str):
    """
    Fetches the content of all files changed in a specific commit.
    """
    # Requires GITHUB_TOKEN in your .env
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    
    try:
        repo = g.get_repo(repo_name)
        commit = repo.get_commit(commit_sha)
        
        files_data = []
        for file in commit.files:
            # We fetch the raw content of the file at that commit state
            content = repo.get_contents(file.filename, ref=commit_sha).decoded_content.decode("utf-8")
            files_data.append({"filename": file.filename, "content": content})
            
        return files_data
    except Exception as e:
        raise Exception(f"GitHub Error: {str(e)}")