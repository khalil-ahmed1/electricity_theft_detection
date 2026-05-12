After cloning a Python repo, the usual steps are:

# 1. Go into the project folder

```bash id="dxk26w"
cd project-name
```

---

# 2. Create virtual environment

## Windows

```bash id="y4mlm3"
python -m venv .venv
```

## macOS/Linux

```bash id="mwdw7w"
python3 -m venv .venv
```

---

# 3. Activate virtual environment

## Windows (PowerShell)

```powershell id="9g2h9m"
.venv\Scripts\Activate
```

## Windows (CMD)

```cmd id="4v9m6f"
.venv\Scripts\activate.bat
```

## macOS/Linux

```bash id="4b0v04"
source .venv/bin/activate
```

After activation you’ll see something like:

```text id="5uq6ng"
(.venv)
```

in terminal.

---

# 4. Install dependencies

If repo has `requirements.txt`:

```bash id="vb3d0e"
pip install -r requirements.txt
```

---

# 5. Run the project

Depends on project type.

Common examples:

## Normal Python app

```bash id="s04ym6"
python app.py
```

or

```bash id="j7vhb2"
python main.py
```

---

## Jupyter notebook

Install notebook:

```bash id="4h0r5u"
pip install notebook
```

Run:

```bash id="f8ikv0"
jupyter notebook
```

---

## Flask app

```bash id="i7j2xt"
flask run
```

---

## FastAPI

```bash id="zv0j5o"
uvicorn main:app --reload
```

---

# 6. If package installation fails

Upgrade pip first:

```bash id="3n4rzm"
python -m pip install --upgrade pip
```

---

# 7. Check Python version

Some repos require specific versions:

```bash id="g7m8r4"
python --version
```

Look for:

* `.python-version`
* `runtime.txt`
* `pyproject.toml`
* README instructions

inside the repo.
