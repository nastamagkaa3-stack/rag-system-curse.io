from pathlib import Path
p = Path.home() / "Desktop" / "rag-course-site" / "build_site.py"
t = p.read_text(encoding="utf-8")
old = """def is_ps(s):
    s = s.strip()
    if not s or s.startswith("#"):
        return True
    keys = ("pip ", "python ", "cd ", "mkdir ", "ollama", "streamlit", "Get-ChildItem", "Remove-Item", "$env:", "curl ", "Set-Location", "New-Item", ".\\venv", "activate", "Invoke-")
    return any(k in s for k in keys) and not s.startswith("import ")"""
new = """def is_ps(s):
    s = s.strip()
    if not s:
        return False
    if s.startswith("#") and any(x in s for x in ("cd ", "mkdir", "python", "pip", "ollama", "streamlit")):
        return True
    keys = ("pip ", "python ", "cd ", "mkdir ", "ollama", "streamlit", "Get-ChildItem", "Remove-Item", "$env:", "curl ", "Set-Location", "New-Item", ".\\venv", "activate", "Invoke-", "Get-Content", "Add-Content")
    return (any(s.startswith(k) for k in keys)) and not s.startswith("import ")"""
if old not in t:
    raise SystemExit("old is_ps not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("patched")
