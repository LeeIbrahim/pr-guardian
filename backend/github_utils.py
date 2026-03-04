# src/pr_guardian/github_utils.py
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

def fetch_commit_files(repo_name: str, commit_sha: str):
    """
    Fetches the content of all files changed in a specific commit.
    """
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


def fetch_branch_files(repo_name: str, branch_name: str):
    """
    Fetches the content of all files in a specific branch.
    """
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    
    try:
        repo = g.get_repo(repo_name)

        sha = repo.get_branch(branch_name).commit.sha
        tree = repo.get_git_tree(sha, recursive=True).tree
        
        files_data = []
        extensions_to_include = (".py", ".js", ".java", ".cpp", ".c", ".rb", ".go", ".ts")

        for item in tree:
            if item.type == "blob" and item.path.endswith(extensions_to_include):
                content = repo.get_contents(item.path, ref=sha).decoded_content.decode("utf-8")
                files_data.append({"filename": item.path, "content": content})

        return files_data
    except Exception as e:
        raise Exception(f"GitHub Error: {str(e)}")
    
def fetch_branches(repo_name: str):
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    
    try:
        repo = g.get_repo(repo_name)
        branches = repo.get_branches()
        return [branch.name for branch in branches]
    except Exception as e:
        raise Exception(f"GitHub Error: {str(e)}")