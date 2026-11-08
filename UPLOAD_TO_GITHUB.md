# Upload instructions: Assignment #2 first milestone

**Destination:** https://github.com/azmatullah93/npm-compatibility-aware-rag

**Author:** Azmat Ullah (26i-7841), i267841@isb.nu.edu.pk

The source repository URL and institutional email are already inserted in `paper/milestone1.tex` and the compiled `paper/milestone1.pdf`.

## Fastest method: GitHub web interface

1. Sign into GitHub as **azmatullah93** and open the repository URL above.
2. On the repository's Code page, select **Add file > Upload files** (or the initial **uploading an existing file** prompt if empty).
3. Unzip `26i-7841_Assignment2_Final_Repository_Ready.zip` on your computer.
4. Upload the **contents** of `npm-compatibility-aware-rag/` preserving the `src/`, `data/`, `tests/`, `outputs/`, `execution/`, `scripts/`, and `paper/` subfolders. Do not upload the outer ZIP alone.
5. Commit to the `main` branch with a message such as `Add Assignment 2 methodology and preliminary retrieval experiments`.
6. Verify the repository shows `README.md`, `src/retrieval.py`, `data/tasks.json`, `outputs/extended_results.csv`, and `paper/milestone1.pdf`.
7. Submit `26i-7841_Assignment2_Final_Research_Paper.pdf` to Google Classroom. There is no requirement to upload the ZIP to Classroom.

## Alternative: command-line git

From the unzipped `npm-compatibility-aware-rag/` folder, using credentials for azmatullah93:

```bash
git init
git branch -M main
git add .
git commit -m "Assignment 2: methodology and preliminary retrieval pilot"
git remote add origin https://github.com/azmatullah93/npm-compatibility-aware-rag.git
git push -u origin main
```

If the repository already contains a README or other commits, clone the repository first, copy the project contents into the clone, then `git add`, `git commit`, and `git push` instead of using `git init`.

## Verify experiments locally

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/evaluate_extended.py
```

## Academic status

This is a retrieval-stage pilot (BM25 / LSA with and without exact-version filtering), not complete reproduction of DocPrompting's published benchmark and not execution-based LLM code generation. The manuscript states these limitations. Original benchmark reproduction is still necessary for full compliance with the complete six-page Assignment #2 rubric.
