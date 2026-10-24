# Publish this repository on GitHub

This folder is a self-contained V1 repository. Publish this folder, not the parent coursework directory. The account owner's email need not be made public and is not a GitHub username.

## Option A: GitHub CLI

Install [GitHub CLI from its official site](https://cli.github.com/), open a terminal in this repository, and authenticate to the intended account:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh api user --jq .login
```

Complete authentication yourself in the browser and check that the printed account is the intended owner. Never paste a password, token or recovery code into a project file or chat.

If this package already has a local Git history, use it. If you downloaded a ZIP without `.git`, initialize it first:

```powershell
git init -b main
git add .
git commit -m "Publish reproducible indoor drone mapping student project"
```

Review the tracked files and create the public repository:

```powershell
git status
git ls-files
gh repo create indoor-drone-mapping --public --source . --remote origin --push --description "Student indoor drone mapping with CoppeliaSim, Python and short-range sensing"
```

This uploads the code, attributed simulation scenes, recorded examples and public documentation to the signed-in account. If the name is already in use, inspect the existing repository before taking any action. Do not overwrite or force-push into unrelated work.

## Option B: GitHub web and normal Git

1. Sign in to the intended account on [GitHub](https://github.com/).
2. Create a new **public** repository named `indoor-drone-mapping`.
3. Leave README, license and `.gitignore` initialization unchecked because this folder already contains them.
4. Copy the repository's HTTPS URL from GitHub.
5. In this folder, add that exact URL as `origin`, then push the existing `main` branch:

```powershell
git remote add origin YOUR_REPOSITORY_HTTPS_URL
git push -u origin main
```

Replace `YOUR_REPOSITORY_HTTPS_URL` with the actual value shown by GitHub. If an origin already exists, inspect it with `git remote -v` rather than replacing it blindly. Git Credential Manager may open a sign-in flow; complete it yourself.

## Check the published result

Confirm that the README displays its images and links, both `.ttt` scenes and `requirements-lock.txt` are present, the license/third-party notice are visible and the Python checks workflow completes. Download a fresh ZIP or clone to another directory and follow the README.

The repository should not contain `.venv`, new `output/` runs, account email, PRN numbers, credentials, local application logs or other coursework. The sanitized chat documents intentionally omit account details and machine paths. Baseline telemetry describes a simulated drone in a synthetic room.
