---
name: biblemate
description: Orchestrate the entire BibleMate AI study workflow dynamically using available skills.
---

# BibleMate Orchestration Skill

## Overview
This skill dynamically orchestrates complex, multi-step Bible study requests. It discovers available skills at runtime, refines the study request, creates a timestamped study folder, generates a Master Study Plan, executes the steps (saving outputs to individual files), performs quality control audits, produces a comprehensive final report, and syncs changes to a remote repository if configured.

## Guidelines & Objectives
When executing this skill:
- Always run the python orchestrator script located at `.agents/skills/biblemate/biblemate_orchestrator.py`.
- For skill discovery or management, execute the script with the appropriate flag:
  - `--list-skills`: List all dynamically discovered skills in the workspace.
  - `--init "<request>" "<title>"`: Create a new study folder and initialize `000-request_and_study_plan.md`.
  - `--update-plan "<folder>" "<plan>"`: Update the Master Study Plan file.
  - `--save-step "<folder>" "<step>" "<skill>" "<content>" [--sub-skill "<sub_skill>"]`: Save intermediate output files using the requested naming format (e.g. `001-skill_name.md`).
  - `--save-report "<folder>" "<last_step>" "<report>"`: Generate the final report file `<last_step>-final_report.md`.
  - `--git-sync`: Stage, commit, and push all modifications to the remote git repository if available.
