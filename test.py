import json
import subprocess
import pandas as pd
import os
import argparse
from flatten_json import flatten

# Defaults (can be overridden by command-line arguments)
REPO_PATH = "/Users/kiran/agLLC/caesar-console"
EN_FILE_PATH = "src/locales/en-US.json"
ZH_FILE_PATH = "src/locales/zh-CN.json"
DEFAULT_BRANCH = "uat"

def get_json_diff(branch=DEFAULT_BRANCH):
    """Get the diff between current branch and specified branch for JSON files."""
    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(REPO_PATH)

    try:
        # Get the current branch name
        current_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            universal_newlines=True
        ).strip()

        print(f"Comparing changes between {current_branch} and {branch}...")

        # Use our specific file paths
        en_file = EN_FILE_PATH
        zh_file = ZH_FILE_PATH

        # Get the old versions from the branch
        old_en, old_zh = {}, {}
        try:
            old_en_content = subprocess.check_output(
                ['git', 'show', f'{branch}:{en_file}'],
                universal_newlines=True,
                stderr=subprocess.PIPE
            )
            old_en = json.loads(old_en_content)
            print(f"Found previous version of {en_file} in {branch} branch")
        except subprocess.CalledProcessError:
            print(f"File {en_file} doesn't exist in {branch} branch")

        try:
            old_zh_content = subprocess.check_output(
                ['git', 'show', f'{branch}:{zh_file}'],
                universal_newlines=True,
                stderr=subprocess.PIPE
            )
            old_zh = json.loads(old_zh_content)
            print(f"Found previous version of {zh_file} in {branch} branch")
        except subprocess.CalledProcessError:
            print(f"File {zh_file} doesn't exist in {branch} branch")

        # Load current versions
        current_en, current_zh = {}, {}
        if os.path.exists(en_file):
            with open(en_file, 'r', encoding='utf-8') as f:
                current_en = json.load(f)
            print(f"Loaded current version of {en_file}")
        else:
            print(f"Warning: {en_file} not found in current branch")

        if os.path.exists(zh_file):
            with open(zh_file, 'r', encoding='utf-8') as f:
                current_zh = json.load(f)
            print(f"Loaded current version of {zh_file}")
        else:
            print(f"Warning: {zh_file} not found in current branch")

        return (old_en, current_en), (old_zh, current_zh)
    finally:
        os.chdir(original_dir)


def flatten_json_dict(json_dict, prefix=''):
    """Flatten nested JSON, preserving full path as key."""
    flattened = {}
    for key, value in json_dict.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(flatten_json_dict(value, new_key))
        else:
            flattened[new_key] = value
    return flattened


def find_changes(old_dict, new_dict):
    """Find keys that are new or changed in new_dict compared to old_dict."""
    old_flat = flatten_json_dict(old_dict)
    new_flat = flatten_json_dict(new_dict)
    changes = {k: v for k, v in new_flat.items() if k not in old_flat or old_flat[k] != v}
    return changes


def create_spreadsheet(en_changes, zh_changes, output_file="translation_changes.xlsx"):
    """Create a spreadsheet with all changes."""
    all_keys = set(en_changes) | set(zh_changes)
    data = [{
        'key': key,
        'en-US': en_changes.get(key, ''),
        'zh-CN': zh_changes.get(key, ''),
        'CS-Feedback': ''
    } for key in all_keys]
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"Spreadsheet created: {output_file}")

    csv_file = output_file.replace('.xlsx', '.csv')
    df.to_csv(csv_file, index=False)
    print(f"CSV version created: {csv_file}")
    return df


def main():
    parser = argparse.ArgumentParser(description='Generate translation diff spreadsheet.')
    parser.add_argument('--repo', default=REPO_PATH, help='Path to the git repository')
    parser.add_argument('--branch', default=DEFAULT_BRANCH, help='Branch to compare against')
    args = parser.parse_args()

    global REPO_PATH, DEFAULT_BRANCH
    REPO_PATH = args.repo_path
    DEFAULT_BRANCH = args.default_branch

    print(f"Using repository path: {REPO_PATH}")
    if not os.path.isdir(REPO_PATH) or not os.path.isdir(os.path.join(REPO_PATH, '.git')):
        print(f"Error: {REPO_PATH} is not a valid git repository")
        sys.exit(1)

    (old_en, current_en), (old_zh, current_zh) = get_json_diff(branch=DEFAULT_BRANCH)

    if not old_en and not old_zh:
        en_changes = flatten_json_dict(current_en)
        zh_changes = flatten_json_dict(current_zh)
    else:
        en_changes = find_changes(old_en, current_en)
        zh_changes = find_changes(old_zh, current_zh)

    if not en_changes and not zh_changes:
        print("No changes detected in translation keys.")
        return

    print(f"Found {len(en_changes)} changed/new keys in en-US.json")
    print(f"Found {len(zh_changes)} changed/new keys in zh-CN.json")

    output_file = os.path.join(os.getcwd(), "translation_changes.xlsx")
    df = create_spreadsheet(en_changes, zh_changes, output_file)
    print(f"Total entries in spreadsheet: {len(df)}")

if __name__ == "__main__":
    main()