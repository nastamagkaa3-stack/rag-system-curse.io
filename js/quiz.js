(function () {
  "use strict";
  var KEY = "rag-course-quiz-v1";
  var questions = [];
  var index = 0;
  var answers = {};

  function $(id) { return document.getElementById(id); }

  function norm(s) {
    return String(s || "").trim().toLowerCase().replace(/\s+/g, " ");
  }

  function loadStore() {
    try {
      var r = localStorage.getItem(KEY);
      return r ? JSON.parse(r) : null;
    } catch (e) { return null; }
  }

  function saveStore() {
    try {
      localStorage.setItem(KEY, JSON.stringify({
        index: index,
        answers: answers,
        at: Date.now()
      }));
      var h = $("saved-hint");
      if (h) {
        h.textContent = "Сохранено";
        h.classList.add("is-live");
        clearTimeout(saveStore._t);
        saveStore._t = setTimeout(function () {
          h.textContent = "Автосохранение";
          h.classList.remove("is-live");
        }, 1000);
      }
    } catch (e) {}
  }

  function pct() {
    if (!questions.length) return 0;
    return Math.round(((index + 1) / questions.length) * 100);
  }

  function setProgress() {
    var p = pct();
    var pn = $("progress-num");
    var pf = $("progress-fill");
    var qn = $("question-num");
    if (pn) pn.textContent = String(p);
    if (pf) pf.style.width = p + "%";
    if (qn) qn.textContent = "Вопрос " + (index + 1) + " из " + questions.length;
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function qText(q) {
    return q.text || q.question || "";
  }

  function openOk(q, text) {
    var u = norm(text);
    if (!u) return false;
    var k = q.correctKeywords || [];
    for (var i = 0; i < k.length; i++) {
      if (u.indexOf(norm(k[i])) !== -1) return true;
    }
    return false;
  }

  function render() {
    var body = $("question-body");
    if (!body || !questions.length) return;
    var q = questions[index];
    var a = answers[String(q.id)];
    if (q.type === "closed" && (a === undefined || a === null)) a = null;
    if (q.type === "open" && typeof a !== "string") a = "";

    var html = "<h1>" + esc(qText(q)) + "</h1>";
    if (q.type === "closed") {
      html += "<div class=\"quiz-options\" role=\"radiogroup\">";
      (q.options || []).forEach(function (opt, i) {
        var c = Number(a) === i ? " checked" : "";
        html += "<label><input type=\"radio\" name=\"q\" value=\"" + i + "\"" + c + "><span>" + esc(opt) + "</span></label>";
      });
      html += "</div>";
    } else {
      html += "<label class=\"sr-only\" for=\"open-answer\">Ответ</label>";
      html += "<textarea id=\"open-answer\" class=\"open-input\" rows=\"3\" placeholder=\"Введите ответ…\">" + esc(a) + "</textarea>";
    }
    body.innerHTML = html;

    if (q.type === "closed") {
      body.querySelectorAll("input[type=radio]").forEach(function (inp) {
        inp.addEventListener("change", function () {
          answers[String(q.id)] = parseInt(inp.value, 10);
          saveStore();
        });
      });
    } else {
      var ta = $("open-answer");
      var tmr;
      if (ta) ta.addEventListener("input", function () {
        answers[String(q.id)] = ta.value;
        clearTimeout(tmr);
        tmr = setTimeout(saveStore, 250);
      });
    }

    setProgress();
    $("btn-prev").disabled = index === 0;
    $("btn-next").style.display = index >= questions.length - 1 ? "none" : "inline-block";
    $("btn-finish").style.display = index >= questions.length - 1 ? "inline-block" : "none";
  }

  function readCurrent() {
    var q = questions[index];
    if (q.type === "closed") {
      var s = document.querySelector(".quiz-card input[name=q]:checked");
      if (s) answers[String(q.id)] = parseInt(s.value, 10);
    } else {
      var ta = $("open-answer");
      if (ta) answers[String(q.id)] = ta.value;
    }
  }

  function grade() {
    var ok = 0;
    var rows = [];
    questions.forEach(function (q) {
      var id = String(q.id);
      var ua = answers[id];
      var good = false;
      var show = "";
      if (q.type === "closed") {
        show = ua != null && q.options ? q.options[ua] : "(нет ответа)";
        good = Number(ua) === Number(q.correct);
      } else {
        show = typeof ua === "string" ? ua : "";
        good = openOk(q, show);
      }
      if (good) ok++;
      rows.push({ q: q, good: good, show: show });
    });
    var max = questions.length;
    var score = max ? Math.round((ok / max) * 100) : 0;
    return { ok: ok, max: max, score: score, rows: rows };
  }

  function showResults() {
    readCurrent();
    saveStore();
    var g = grade();
    var html = "<div class=\"results-summary\"><div class=\"score-big\">" + g.score + "</div>";
    html += "<div class=\"score-sub\">баллов из 100 · верно " + g.ok + " из " + g.max + "</div></div>";
    html += "<h2 class=\"content-block\" style=\"margin-top:0;color:var(--accent);font-size:1.1rem;\">Разбор</h2>";
    g.rows.forEach(function (r) {
      var q = r.q;
      html += "<article class=\"break-item " + (r.good ? "ok" : "bad") + "\">";
      html += "<h3>" + esc(qText(q)) + "</h3>";
      html += "<p class=\"break-meta\">" + (r.good ? "Верно" : "Ошибка") + " · Ваш ответ: " + esc(String(r.show || "")) + "</p>";
      if (q.type === "closed" && q.options) {
        html += "<p><strong>Правильно:</strong> " + esc(q.options[q.correct] || "") + "</p>";
      } else {
        html += "<p><strong>Ключевые слова:</strong> " + esc((q.correctKeywords || []).join(", ")) + "</p>";
      }
      if (q.explanation) html += "<p class=\"explanation\">" + esc(q.explanation) + "</p>";
      html += "</article>";
    });
    $("results-content").innerHTML = html;
    $("view-quiz").hidden = true;
    $("view-results").hidden = false;
    $("progress-fill").style.width = "100%";
    $("progress-num").textContent = "100";
  }

  function next() {
    readCurrent();
    saveStore();
    if (index < questions.length - 1) { index++; render(); }
  }

  function prev() {
    readCurrent();
    saveStore();
    if (index > 0) { index--; render(); }
  }

  function restart() {
    localStorage.removeItem(KEY);
    answers = {};
    index = 0;
    $("view-results").hidden = true;
    $("view-quiz").hidden = false;
    $("load-error").classList.remove("is-visible");
    render();
    saveStore();
  }

  function init(data) {
    questions = Array.isArray(data) ? data : [];
    if (!questions.length) {
      $("load-error").textContent = "Нет вопросов в JSON.";
      $("load-error").classList.add("is-visible");
      if ($("view-quiz")) $("view-quiz").hidden = true;
      return;
    }
    var st = loadStore();
    if (st && st.answers && typeof st.index === "number") {
      answers = st.answers;
      index = Math.min(Math.max(0, st.index), questions.length - 1);
    }
    $("btn-prev").addEventListener("click", prev);
    $("btn-next").addEventListener("click", next);
    $("btn-finish").addEventListener("click", showResults);
    $("btn-restart").addEventListener("click", restart);
    render();
  }

  var url = document.body.getAttribute("data-json") || "../data/questions.json";
  fetch(url)
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(init)
    .catch(function (e) {
      $("load-error").textContent = "Не удалось загрузить questions.json. Запустите сайт через локальный сервер (например: python -m http.server).";
      $("load-error").classList.add("is-visible");
      $("view-quiz").hidden = true;
    });
})();