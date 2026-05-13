# -*- coding: utf-8 -*-
import html, json, re, sys
from pathlib import Path

HOME = Path.home()
DESK = HOME / "Desktop"
ROOT = DESK / "rag-course-site"
LECT_F = DESK / "lectures.txt"
PRAC_F = DESK / "practices.txt"
QSRC = DESK / "questions.json"
QOUT = ROOT / "data" / "questions.json"

def esc(s):
    return html.escape(s or "", quote=True)

def parse_lectures(raw):
    lines = raw.splitlines()
    pat = re.compile(r"^Лекция\s+(\d+)\.\s*(.+)$")
    starts = []
    for i, line in enumerate(lines):
        m = pat.match(line.strip())
        if not m:
            continue
        if re.search(r"\t\d+\s*$", line):
            continue
        starts.append((int(m.group(1)), i, m.group(2).strip()))
    starts.sort(key=lambda x: x[1])
    out = []
    for j, (num, idx, title) in enumerate(starts):
        end = starts[j + 1][1] if j + 1 < len(starts) else len(lines)
        out.append((num, title, "\n".join(lines[idx + 1 : end]).strip()))
    return out

def extract_self_check(body):
    key = "вопросы для самоконтроля"
    low = body.lower()
    i = low.find(key)
    if i == -1:
        return body, ""
    main = body[:i].rstrip()
    rest = body[i:].splitlines()
    items = []
    for ln in rest[1:]:
        s = re.sub(r"^[\s\d\.\t\-\•]+", "", ln.strip())
        if s:
            items.append(f"<li>{esc(s)}</li>")
    sc = '<section class="self-check"><h2>Вопросы для самоконтроля</h2><ol>' + "".join(items) + "</ol></section>"
    return main, sc

def body_to_html(body):
    lines = body.splitlines()
    out, toc = [], []
    h2c = 0
    i, par = 0, []
    in_ol, in_ul = False, False

    def close():
        nonlocal in_ol, in_ul
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def flush():
        t = "\n".join(par).strip()
        if t:
            out.append(f"<p>{esc(t)}</p>")
        par.clear()

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if not st:
            flush()
            i += 1
            continue
        if re.match(r"^https?://\S+$", st):
            flush()
            close()
            out.append(f'<p><a href="{esc(st)}" target="_blank" rel="noopener">{esc(st)}</a></p>')
            i += 1
            continue
        if "\t" in line and st.count("\t") >= 2:
            flush()
            close()
            rows = []
            while i < len(lines) and lines[i].strip() and "\t" in lines[i]:
                rows.append([c.strip() for c in lines[i].split("\t")])
                i += 1
            if rows:
                out.append('<div class="table-wrap"><table class="content-table"><thead><tr>')
                out += ["".join(f"<th>{esc(c)}</th>" for c in rows[0]) + "<tr></thead><tbody>"]
                for r in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>")
                out.append("</tbody>}</div>")
            continue
        mtab = re.match(r"^(\d+)\.\t(.+)$", line)
        if mtab:
            flush()
            if not in_ol:
                close()
                out.append('<ol class="lecture-ol">')
                in_ol = True
            out.append(f"<li>{esc(mtab.group(2).strip())}</li>")
            i += 1
            continue
        msub = re.match(r"^(\d+\.\d+)\.?\s+(.+)$", st)
        if msub:
            flush()
            close()
            out.append(f"<h3>{esc(msub.group(2).strip())}</h3>")
            i += 1
            continue
        if st.startswith(("•", "-", "–", "—", "\uf0b7")):
            flush()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                close()
                out.append("<ul>")
                in_ul = True
            item = re.sub(r"^[•\-\–—\uf0b7]+\s*", "", st)
            out.append(f"<li>{esc(item)}</li>")
            i += 1
            continue
        mnum = re.match(r"^(\d+)\.\s+(.+)$", st)
        if mnum:
            flush()
            prev = lines[i - 1].strip() if i else ""
            prev_f = bool(re.search(r"[=⋅∥]", prev)) and len(prev) < 130
            if in_ol and (prev.endswith(":") or prev == ""):
                out.append(f"<li>{esc(mnum.group(2).strip())}</li>")
                i += 1
                continue
            if prev_f and int(mnum.group(1)) <= 9:
                if not in_ol:
                    close()
                    out.append('<ol class="lecture-ol">')
                    in_ol = True
                out.append(f"<li>{esc(mnum.group(2).strip())}</li>")
                i += 1
                continue
            close()
            h2c += 1
            hid = f"h2-{h2c}"
            title = mnum.group(2).strip()
            toc.append((hid, title))
            out.append(f'<h2 id="{hid}">{esc(title)}</h2>')
            i += 1
            continue
        close()
        par.append(st)
        i += 1
    flush()
    close()
    return "\n".join(out), toc

# Русские названия лекций
LECTURE_TITLES_RU = {
    1: "Введение в RAG-системы",
    2: "Эмбеддинги и векторные представления",
    3: "Векторные базы данных",
    4: "Поиск и ранжирование",
    5: "LLM и генерация ответов",
    6: "Оценка RAG-систем",
    7: "Практическое построение RAG-приложения",
    8: "Оптимизация и масштабирование RAG"
}

# Русские названия практик
PRACTICE_TITLES_RU = {
    1: "Подготовка данных и настройка окружения",
    2: "Работа с эмбеддингами",
    3: "Создание векторной базы данных",
    4: "Реализация поискового модуля",
    5: "Интеграция с LLM",
    6: "Создание веб-интерфейса",
    7: "Оценка качества RAG-системы",
    8: "Финальная сборка и оптимизация"
}

def lecture_page(num, title, inner, toc):
    # Используем русское название, если оно есть
    display_title = LECTURE_TITLES_RU.get(num, title)
    prev = f'<a href="lecture{num-1}.html">← Лекция {num-1}</a>' if num > 1 else "<span></span>"
    next_ = f'<a href="lecture{num+1}.html">Лекция {num+1} →</a>' if num < 8 else "<span></span>"
    tnav = '<nav class="toc" aria-labelledby="toc-h"><h2 id="toc-h">Оглавление</h2><ul>'
    tnav += "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in toc) + "</ul></nav>"
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Лекция {num} — {esc(display_title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="site-header"><div class="header-inner">
<a class="logo" href="../index.html">RAG <span>курс</span></a>
<nav class="nav-desktop">
<a href="../index.html">Главная</a>
<a href="lecture1.html">Лекции</a>
<a href="../practices/practice1.html">Практики</a>
<a href="../tests/test.html">Тест</a>
</nav>
<button type="button" class="menu-toggle" aria-expanded="false" aria-label="Меню">Меню</button>
</div>
<nav class="nav-mobile">
<a href="../index.html">Главная</a>
<a href="lecture1.html">Лекции</a>
<a href="../practices/practice1.html">Практики</a>
<a href="../tests/test.html">Тест</a>
</nav>
</header>
<main>
<nav class="breadcrumb"><a href="../index.html">Главная</a> / <a href="lecture1.html">Лекции</a> / Лекция {num}</nav>
<header class="page-header"><h1>Лекция {num}. {esc(display_title)}</h1><p class="meta">Курс «Разработка RAG-систем»</p></header>
{tnav}
<article class="content-block lecture-body">
{inner}
</article>
<nav class="nav-prev-next">{prev}{next_}</nav>
</main>
<footer class="site-footer">Лекция {num}</footer>
<script src="../js/main.js"></script>
</body></html>'''

def parse_practices(raw):
    pat = re.compile(r"^Методическое пособие №(\d+)\.\s*(.+)$", re.MULTILINE)
    ms = [m for m in pat.finditer(raw) if not re.search(r"\t\d+\s*$", m.group(0))]
    out = []
    for j, m in enumerate(ms):
        num = int(m.group(1))
        title = m.group(2).strip()
        if "\t" in title:
            title = title.split("\t")[0].strip()
        start = m.end()
        end = ms[j + 1].start() if j + 1 < len(ms) else len(raw)
        out.append((num, title, raw[start:end].strip()))
    return sorted(out, key=lambda x: x[0])

def split_practice(body):
    d = {"goal": "", "steps": "", "hw": "", "qq": "", "crit": ""}
    low = body.lower()
    i_hw = low.find("задание для самостоятельного выполнения")
    i_qq = low.find("контрольные вопросы")
    i_cr = low.find("критерии оценки")
    if i_hw == -1:
        d["steps"] = body
        return d
    d["steps"] = body[:i_hw].strip()
    rest = body[i_hw:]
    ri_qq = rest.lower().find("контрольные вопросы")
    ri_cr = rest.lower().find("критерии оценки")
    if ri_qq == -1 or ri_cr == -1:
        d["hw"] = rest.strip()
        return d
    d["hw"] = rest[:ri_qq].strip()
    d["qq"] = rest[ri_qq:ri_cr].strip()
    d["crit"] = rest[ri_cr:].strip()
    return d

def is_ps(s):
    s = s.strip()
    if not s:
        return False
    if s.startswith("#") and any(x in s for x in ("cd ", "mkdir", "python", "pip", "ollama", "streamlit")):
        return True
    keys = (
        "pip ", "python ", "cd ", "mkdir ", "ollama", "streamlit",
        "Get-ChildItem", "Remove-Item", "$env:", "curl ", "Set-Location",
        "New-Item", ".\\venv", "activate", "Invoke-", "Get-Content", "Add-Content",
    )
    if re.match(r"^[\w./]+\s+-\s+", s) and not s.startswith(("pip", "python", "cd", "$", "Get", "Remove", "Set", "New", "Invoke")):
        return False
    return any(s.startswith(k) for k in keys) and not s.startswith("import ")

def html_steps(body, goal_line):
    lines = body.splitlines()
    out = []
    i = 0
    goal = ""
    for j, ln in enumerate(lines):
        if ln.lower().startswith("цель занятия"):
            goal = re.sub(r"(?i)^цель занятия:\s*", "", ln).strip()
            lines = lines[j + 1 :]
            break
    in_step_ol = False
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.strip().startswith("#"):
            blk = []
            while i < len(lines) and lines[i].strip():
                blk.append(lines[i].rstrip())
                i += 1
            code = "\n".join(blk).strip()
            if in_step_ol:
                out.append("</ol>")
                in_step_ol = False
            out.append(
                '<div class="powershell-block copyable"><div class="powershell-block__bar"><span>PowerShell</span>'
                '<button type="button" class="btn-copy" aria-label="Копировать">Копировать</button></div>'
                f"<pre><code>{esc(code)}</code></pre></div>"
            )
            continue
        if re.match(r"^(import |from |def |class |if __name__)", line):
            blk = []
            while i < len(lines) and lines[i].strip():
                if blk and lines[i].strip() and not re.match(r"^(import |from |def |class |if |    |\s)", lines[i]):
                    break
                if lines[i].strip().startswith("#") and blk and "def " in "\n".join(blk):
                    blk.append(lines[i].rstrip())
                    i += 1
                    continue
                if not re.match(r"^(import |from |def |class |if |    |\s|@|\w+\s*=)", lines[i]) and blk:
                    break
                blk.append(lines[i].rstrip())
                i += 1
            code = "\n".join(blk)
            if in_step_ol:
                out.append("</ol>")
                in_step_ol = False
            out.append('<pre><code class="language-python">' + esc(code) + "</code></pre>")
            continue
        if is_ps(line):
            blk = []
            while i < len(lines) and lines[i].strip():
                if re.match(r"^(import |from |def )", lines[i]):
                    break
                blk.append(lines[i].rstrip())
                i += 1
            code = "\n".join(blk).strip()
            if in_step_ol:
                out.append("</ol>")
                in_step_ol = False
            out.append('<div class="powershell-block copyable"><div class="powershell-block__bar"><span>PowerShell</span>'
                       '<button type="button" class="btn-copy" aria-label="Копировать">Копировать</button></div>'
                       f"<pre><code>{esc(code)}</code></pre></div>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip():
            if re.match(r"^(import |from |def |pip |python |\$|cd |mkdir )", lines[i]) and not buf:
                break
            buf.append(lines[i].strip())
            i += 1
        t = " ".join(buf)
        if t:
            mstep = re.match(r"^(\d+)[\.\:]\s*(.+)$", t)
            if mstep and len(t) < 300:
                if not in_step_ol:
                    out.append('<ol class="practice-steps-ol">')
                    in_step_ol = True
                out.append(f"<li><strong>{esc(mstep.group(1))}.</strong> {esc(mstep.group(2))}</li>")
            else:
                if in_step_ol:
                    out.append("</ol>")
                    in_step_ol = False
                out.append(f"<p>{esc(t)}</p>")
    if in_step_ol:
        out.append("</ol>")
    joined = "\n".join(out)
    steps_only = joined
    goal_block = ""
    gval = goal_line or goal
    if gval:
        goal_block = f'<div class="practice-goal"><p class="practice-goal__label">Цель занятия</p><p>{esc(gval)}</p></div>'
    return goal_block, steps_only

def strip_heading_block(txt, needle):
    txt = (txt or "").strip()
    if not txt:
        return ""
    lines = txt.splitlines()
    if lines and needle in lines[0].lower():
        return "\n".join(lines[1:]).strip()
    return txt

def practice_page(num, title, body):
    # Используем русское название, если оно есть
    display_title = PRACTICE_TITLES_RU.get(num, title)
    sec = split_practice(body)
    raw_steps = sec["steps"]
    goal_line = ""
    for ln in raw_steps.splitlines():
        if ln.lower().startswith("цель занятия"):
            goal_line = re.sub(r"(?i)^цель занятия:\s*", "", ln).strip()
            break
    goal_block, inner = html_steps(raw_steps, goal_line)
    hw = strip_heading_block(sec.get("hw", ""), "задание")
    qq = strip_heading_block(sec.get("qq", ""), "контрольные")
    crit = strip_heading_block(sec.get("crit", ""), "критерии")
    extra = ""
    if hw:
        extra += "<h2>Задание для самостоятельного выполнения</h2>"
        for para in re.split(r"\n\s*\n", hw):
            p = para.strip()
            if p:
                extra += f"<p>{esc(p)}</p>"
    if qq.strip():
        extra += "<h2>Контрольные вопросы</h2><ol>"
        for ln in qq.splitlines():
            s = ln.strip()
            if s:
                extra += f"<li>{esc(s)}</li>"
        extra += "</ol>"
    crit_html = ""
    if crit:
        rows = []
        for ln in crit.splitlines():
            if "\t" in ln:
                rows.append([c.strip() for c in ln.split("\t")])
        if rows:
            crit_html = '<h2>Критерии оценки</h2><div class="criteria-table-wrap"><table class="criteria-table"><thead><tr>'
            crit_html += "".join(f"<th>{esc(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>"
            for r in rows[1:]:
                crit_html += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
            crit_html += "</tbody>}</div>"
    prev = f'<a href="practice{num-1}.html">← Практика {num-1}</a>' if num > 1 else "<span></span>"
    next_ = f'<a href="practice{num+1}.html">Практика {num+1} →</a>' if num < 8 else "<span></span>"
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Практика {num} — {esc(display_title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="site-header"><div class="header-inner">
<a class="logo" href="../index.html">RAG <span>курс</span></a>
<nav class="nav-desktop">
<a href="../index.html">Главная</a>
<a href="../lectures/lecture1.html">Лекции</a>
<a href="practice1.html">Практики</a>
<a href="../tests/test.html">Тест</a>
</nav>
<button type="button" class="menu-toggle" aria-expanded="false" aria-label="Меню">Меню</button>
</div>
<nav class="nav-mobile">
<a href="../index.html">Главная</a>
<a href="../lectures/lecture1.html">Лекции</a>
<a href="practice1.html">Практики</a>
<a href="../tests/test.html">Тест</a>
</nav>
</header>
<main>
<nav class="breadcrumb"><a href="../index.html">Главная</a> / <a href="practice1.html">Практики</a> / Практика {num}</nav>
<header class="page-header"><h1>Методическое пособие №{num}. {esc(display_title)}</h1></header>
{goal_block}
<p class="practice-duration"><strong>Продолжительность:</strong> 4 академических часа</p>
<section class="content-block">
<h2>Пошаговая инструкция</h2>
{inner}
{extra}
{crit_html}
</section>
<nav class="nav-prev-next">{prev}{next_}</nav>
</main>
<footer class="site-footer">Практика {num}</footer>
<script src="../js/main.js"></script>
</body></html>'''

def strip_opt(o):
    return re.sub(r"^[A-D]\)\s*", "", o.strip())

def letter_idx(ch):
    return {"A": 0, "B": 1, "C": 2, "D": 3}[ch.strip().upper()[0]]

def kw_from(ans):
    ans = (ans or "").strip()
    if not ans:
        return ["ответ"]
    kws = []
    for p in re.split(r"[\.\n;]+", ans):
        p = p.strip()
        if 3 <= len(p) <= 120:
            kws.append(p)
    for w in re.findall(r"[\w\-/.]{4,}", ans):
        wl = w.lower()
        if wl not in {x.lower() for x in kws}:
            kws.append(w)
        if len(kws) >= 14:
            break
    if "\n" in ans:
        kws.insert(0, ans.split("\n")[0].strip()[:120])
    seen, out = set(), []
    for k in kws:
        kl = k.lower()
        if kl not in seen and len(k) > 2:
            seen.add(kl)
            out.append(k)
    return out[:16] if out else [ans[:80]]

def flatten_questions(data):
    flat = []
    expl = "См. материалы курса «Разработка RAG-систем»."
    parts = data.get("test", {}).get("parts", {})

    def walk_closed(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("questions"), list):
                for q in obj["questions"]:
                    if "options" in q:
                        flat.append({
                            "id": q["id"], "type": "closed", "text": q["text"],
                            "options": [strip_opt(o) for o in q["options"]],
                            "correct": letter_idx(q.get("correct_answer", "A")),
                            "explanation": q.get("explanation") or expl,
                        })
            for v in obj.values():
                walk_closed(v)

    def walk_open(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get("questions"), list):
                for q in obj["questions"]:
                    if "answer" in q and "options" not in q:
                        flat.append({
                            "id": q["id"], "type": "open", "text": q["text"],
                            "correctKeywords": kw_from(q["answer"]),
                            "explanation": q.get("explanation") or expl,
                        })
            for v in obj.values():
                walk_open(v)

    walk_closed(parts.get("part1", {}))
    walk_open(parts.get("part2", {}))
    walk_open(parts.get("part3", {}))
    flat.sort(key=lambda x: x["id"])
    return flat

def main():
    raw = LECT_F.read_text(encoding="utf-8")
    for num, title, body in parse_lectures(raw):
        main, sc = extract_self_check(body)
        inner, toc = body_to_html(main)
        if sc:
            inner += "\n" + sc
        (ROOT / "lectures" / f"lecture{num}.html").write_text(lecture_page(num, title, inner, toc), encoding="utf-8")
        print(f"Лекция {num}: {LECTURE_TITLES_RU.get(num, title)}")
    rawp = PRAC_F.read_text(encoding="utf-8")
    for num, title, body in parse_practices(rawp):
        (ROOT / "practices" / f"practice{num}.html").write_text(practice_page(num, title, body), encoding="utf-8")
        print(f"Практика {num}: {PRACTICE_TITLES_RU.get(num, title)}")
    qd = json.loads(QSRC.read_text(encoding="utf-8"))
    flat = flatten_questions(qd)
    QOUT.write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Вопросы: {len(flat)}")
    json.loads(QOUT.read_text(encoding="utf-8"))
    return 0

if __name__ == "__main__":
    sys.exit(main())