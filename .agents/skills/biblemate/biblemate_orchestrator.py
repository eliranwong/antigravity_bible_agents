#!/usr/bin/env python3
import os
import sys
import re
import glob
import argparse
import datetime
import subprocess

def get_workspace_root():
    # This script is at: <root>/.agents/skills/biblemate/biblemate_orchestrator.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def discover_skills():
    workspace_root = get_workspace_root()
    skills_dir = os.path.join(workspace_root, ".agents", "skills")
    if not os.path.exists(skills_dir):
        print(f"Error: Skills directory not found at {skills_dir}", file=sys.stderr)
        return []
    
    skills = []
    for name in sorted(os.listdir(skills_dir)):
        sub = os.path.join(skills_dir, name)
        if os.path.isdir(sub):
            skill_md_path = os.path.join(sub, "SKILL.md")
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Extract YAML frontmatter
                    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL | re.MULTILINE)
                    desc = ""
                    skill_name = name
                    if m:
                        yaml_text = m.group(1)
                        for line in yaml_text.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                k = k.strip().lower()
                                v = v.strip()
                                if k == "name":
                                    skill_name = v
                                elif k == "description":
                                    desc = v
                    skills.append({
                        "name": skill_name,
                        "description": desc,
                        "path": skill_md_path
                    })
                except Exception as e:
                    print(f"Warning: Failed to parse {skill_md_path}: {e}", file=sys.stderr)
    return skills

def init_study(request, title):
    workspace_root = get_workspace_root()
    biblemate_dir = os.path.join(workspace_root, "biblemate")
    os.makedirs(biblemate_dir, exist_ok=True)
    
    # Format title to lowercase with underscores, alphanumeric only
    clean_title = re.sub(r"[^a-zA-Z0-9_]", "_", title).lower()
    clean_title = re.sub(r"_+", "_", clean_title).strip("_")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    folder_name = f"{timestamp}_{clean_title}"
    study_dir = os.path.join(biblemate_dir, folder_name)
    os.makedirs(study_dir, exist_ok=True)
    
    plan_filepath = os.path.join(study_dir, "000-request_and_study_plan.md")
    
    plan_template = f"""# BibleMate Study: {title}

## Original User Request
{request}

## Refined User Request
*(To be populated by the AI assistant)*

## Master Study Plan
*(To be populated by the AI assistant)*
"""
    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_template)
        
    print(f"SUCCESS_INIT:{study_dir}:{plan_filepath}")

def update_plan(folder_path, plan_content):
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    plan_filepath = os.path.join(folder_path, "000-request_and_study_plan.md")
    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_content)
    print(f"SUCCESS_UPDATE_PLAN:{plan_filepath}")

def save_step(folder_path, step_number, skill_name, content, sub_skill=None):
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    step_num = str(step_number).zfill(3)
    skill_clean = re.sub(r"[^a-zA-Z0-9-]", "-", skill_name).lower()
    skill_clean = re.sub(r"-+", "-", skill_clean).strip("-")
    
    if sub_skill:
        sub_clean = re.sub(r"[^a-zA-Z0-9-]", "-", sub_skill).lower()
        sub_clean = re.sub(r"-+", "-", sub_clean).strip("-")
        filename = f"{step_num}-{skill_clean}-{sub_clean}.md"
    else:
        filename = f"{step_num}-{skill_clean}.md"
        
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"SUCCESS_SAVE_STEP:{filepath}")

def save_report(folder_path, last_step_number, content):
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    last_step_str = str(last_step_number).zfill(3)
    filename = f"{last_step_str}-final_report.md"
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"SUCCESS_SAVE_REPORT:{filepath}")

def git_sync():
    workspace_root = get_workspace_root()
    git_dir = os.path.join(workspace_root, ".git")
    if not os.path.exists(git_dir):
        print("Note: Not a git repository. Skipping sync.")
        return
        
    try:
        # Check if remote origin is set
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], 
                             cwd=workspace_root, capture_output=True, text=True)
        if not res.stdout.strip():
            print("Note: No git remote origin configured. Skipping sync.")
            return
            
        print("Staging changes...")
        subprocess.run(["git", "add", "."], cwd=workspace_root, check=True)
        
        print("Committing changes...")
        subprocess.run(["git", "commit", "-m", "Sync BibleMate study results"], cwd=workspace_root, check=True)
        
        print("Pushing to remote...")
        subprocess.run(["git", "push"], cwd=workspace_root, check=True)
        print("SUCCESS_GIT_SYNC")
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error during git sync: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Orchestrator script for the BibleMate AI workflow.")
    parser.add_argument("--list-skills", action="store_true", help="List all dynamically discovered skills in the workspace.")
    parser.add_argument("--init", nargs=2, metavar=("REQUEST", "TITLE"), help="Initialize a new study folder and 000-request_and_study_plan.md file.")
    parser.add_argument("--update-plan", nargs=2, metavar=("FOLDER_PATH", "PLAN_CONTENT"), help="Update the 000-request_and_study_plan.md file in the given study folder.")
    parser.add_argument("--save-step", nargs=4, metavar=("FOLDER_PATH", "STEP_NUM", "SKILL_NAME", "CONTENT"), help="Save intermediate step output to folder.")
    parser.add_argument("--sub-skill", help="Optional sub-skill name for the step file.")
    parser.add_argument("--save-report", nargs=3, metavar=("FOLDER_PATH", "LAST_STEP_NUM", "CONTENT"), help="Save the final report file in the study folder.")
    parser.add_argument("--git-sync", action="store_true", help="Run git sync skill to stage, commit, and push all modifications to the remote repository.")
    
    args = parser.parse_args()
    
    if args.list_skills:
        skills = discover_skills()
        print("# Discovered Study Skills\n")
        for s in skills:
            print(f"- **{s['name']}**: {s['description']}")
    elif args.init:
        init_study(args.init[0], args.init[1])
    elif args.update_plan:  # note: argparse converts dash to underscore
        update_plan(args.update_plan[0], args.update_plan[1])
    elif args.save_step:
        save_step(args.save_step[0], args.save_step[1], args.save_step[2], args.save_step[3], args.sub_skill)
    elif args.save_report:
        save_report(args.save_report[0], args.save_report[1], args.save_report[2])
    elif args.git_sync:
        git_sync()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
