# How to run the script?

Steps:

1. download the script in your local machine.
2. Update:

    ```
    REPO_PATH = /path/to/repo
    ```

3. Create `venv`

    ```
    python -m venv venv
    source venv/bin/activate
    ```

5. Install required dependencies:

    ```
    pip install pandas openpyxl flatten-json
    ```

6. Run the script:

    ```
    python create_translation_xls_for_diff.py
    ```

Tip:
- This script compares your local branch with `uat` branch. So make sure `uat` has the required pulls.
- If you wish to change comparision to other branch, update the code 