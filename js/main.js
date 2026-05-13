(function () {
  "use strict";
  var toggle = document.querySelector(".menu-toggle");
  var mobileNav = document.querySelector(".nav-mobile");
  if (toggle && mobileNav) {
    toggle.addEventListener("click", function () {
      var open = mobileNav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    mobileNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        mobileNav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
  document.querySelectorAll(".powershell-block .btn-copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var block = btn.closest(".powershell-block");
      var code = block && block.querySelector("pre code");
      if (!code || !navigator.clipboard) return;
      navigator.clipboard.writeText(code.textContent).then(function () {
        var t = btn.textContent;
        btn.textContent = "Скопировано";
        setTimeout(function () { btn.textContent = t; }, 1800);
      });
    });
  });
})();