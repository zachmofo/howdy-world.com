(function () {
  var form = document.getElementById("quote");
  if (!form) return;

  var fields = ["name", "email", "business", "location", "tier", "message"];
  var status = document.getElementById("quote-status");
  var success = document.getElementById("quote-success");
  var limits = { name: 80, email: 254, business: 120, location: 120, message: 4000 };
  var tiers = { Basic: 1, Standard: 1, Premium: 1, "Not sure": 1 };
  var emailRe =
    /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;
  var sitekeyRe = /^[0-3]x[A-Za-z0-9_-]{20,}$/;
  var widgetId = null;
  var turnstileBroken = false;
  var staleStatus = {
    "Complete the spam check.": 1,
    "The spam check expired. Complete it again.": 1,
    "The spam check could not load. Try again.": 1,
  };

  form.noValidate = true;

  var params = new URLSearchParams(location.search);
  var sent = params.get("sent");
  if (sent === "1" || document.documentElement.classList.contains("quote-sent")) {
    form.hidden = true;
    success.hidden = false;
    success.focus();
    if (sent) history.replaceState(null, "", location.pathname + "#quote");
    return;
  }
  if (sent === "0" || document.documentElement.classList.contains("quote-failed")) {
    var note = document.getElementById("quote-return");
    if (note) {
      note.hidden = false;
      note.tabIndex = -1;
      note.focus();
    }
    if (sent) history.replaceState(null, "", location.pathname + "#quote");
  }

  function messageFor(name, value) {
    var text = String(value || "").trim();
    if (name === "name" && (!text || text.length > limits.name)) return "Enter your name.";
    if (name === "email" && (text.length > limits.email || !emailRe.test(text))) {
      return "Enter a valid email address.";
    }
    if (name === "business" && (!text || text.length > limits.business)) {
      return "Enter the business name.";
    }
    if (name === "location" && (!text || text.length > limits.location)) {
      return "Enter the city and state.";
    }
    if (name === "tier" && !tiers[text]) return "Choose a tier.";
    if (name === "message" && (!text || text.length > limits.message)) {
      return "Add a message (4,000 characters or fewer).";
    }
    return "";
  }

  function showError(name, message) {
    var input = form.elements[name];
    var err = document.getElementById("quote-" + name + "-error");
    if (!input || !err) return;
    err.textContent = message;
    if (message) {
      input.setAttribute("aria-invalid", "true");
      input.setAttribute("aria-describedby", err.id);
    } else {
      input.removeAttribute("aria-invalid");
      input.removeAttribute("aria-describedby");
    }
  }

  function validate() {
    var first = null;
    fields.forEach(function (name) {
      var input = form.elements[name];
      var message = messageFor(name, input.value);
      showError(name, message);
      if (message && !first) first = input;
    });
    return first;
  }

  document.querySelectorAll("a[data-tier]").forEach(function (link) {
    link.addEventListener("click", function () {
      var select = form.elements.tier;
      var tier = link.getAttribute("data-tier");
      if (!select || !tiers[tier]) return;
      select.value = tier;
      showError("tier", "");
    });
  });

  fields.forEach(function (name) {
    var input = form.elements[name];
    input.addEventListener("blur", function () {
      if (input.value.trim() === "") return;
      showError(name, messageFor(name, input.value));
    });
    input.addEventListener("input", function () {
      if (input.getAttribute("aria-invalid") === "true") {
        showError(name, messageFor(name, input.value));
      }
    });
  });

  function markTurnstileBroken() {
    turnstileBroken = true;
    status.textContent = "The spam check could not load. Try again.";
  }

  function clearStaleStatus() {
    if (staleStatus[status.textContent]) status.textContent = "";
  }

  function renderQuoteTurnstile() {
    if (widgetId != null) return;
    var box = document.getElementById("turnstile");
    if (!box || !window.turnstile || typeof window.turnstile.render !== "function") return;
    var key = box.getAttribute("data-sitekey") || "";
    var theme = box.getAttribute("data-theme") || "light";
    if (!sitekeyRe.test(key)) {
      markTurnstileBroken();
      return;
    }
    if (theme !== "light" && theme !== "dark" && theme !== "auto") theme = "light";
    box.classList.add("is-on");
    var note = document.getElementById("turnstile-note");
    if (note) note.hidden = false;
    try {
      widgetId = window.turnstile.render(box, {
        sitekey: key,
        theme: theme,
        action: "quote",
        "response-field": true,
        "response-field-name": "cf-turnstile-response",
        callback: function () {
          turnstileBroken = false;
          clearStaleStatus();
        },
        "error-callback": function () {
          markTurnstileBroken();
        },
        "expired-callback": function () {
          turnstileBroken = false;
          status.textContent = "The spam check expired. Complete it again.";
          resetWidget();
        },
        "timeout-callback": function () {
          turnstileBroken = false;
          status.textContent = "The spam check expired. Complete it again.";
          resetWidget();
        },
      });
    } catch (err) {
      widgetId = null;
      markTurnstileBroken();
    }
    if (widgetId == null) markTurnstileBroken();
  }

  window.__renderQuoteTurnstile = renderQuoteTurnstile;
  window.__quoteTurnstileScriptError = markTurnstileBroken;
  window.onQuoteTurnstileLoad = function () {
    window.__quoteTurnstileReady = true;
    renderQuoteTurnstile();
  };
  if (window.__quoteTurnstileFailed) markTurnstileBroken();
  if (window.__quoteTurnstileReady || window.turnstile) renderQuoteTurnstile();

  if (!turnstileScriptPresent() && !window.turnstile) {
    var script = document.createElement("script");
    script.src =
      "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=onQuoteTurnstileLoad";
    script.async = true;
    script.defer = true;
    script.onerror = markTurnstileBroken;
    document.head.appendChild(script);
  }

  function turnstileScriptPresent() {
    var scripts = document.querySelectorAll("script[src]");
    for (var i = 0; i < scripts.length; i += 1) {
      var src = scripts[i].getAttribute("src") || "";
      if (src.indexOf("challenges.cloudflare.com/turnstile/v0/api.js") !== -1) return true;
    }
    return false;
  }

  function resetWidget() {
    if (widgetId == null || !window.turnstile || typeof window.turnstile.reset !== "function") return;
    try {
      window.turnstile.reset(widgetId);
    } catch (err) {
      markTurnstileBroken();
    }
  }

  function currentToken() {
    var fromWidget = "";
    if (widgetId != null && window.turnstile && typeof window.turnstile.getResponse === "function") {
      try {
        fromWidget = window.turnstile.getResponse(widgetId) || "";
      } catch (err) {
        fromWidget = "";
      }
    }
    var input = form.querySelector('input[name="cf-turnstile-response"]');
    var fromInput = input && typeof input.value === "string" ? input.value : "";
    var token = fromWidget || fromInput;
    if (!token || token.length > 2048) return "";
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = "cf-turnstile-response";
      form.appendChild(input);
    }
    input.value = token;
    return token;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var first = validate();
    if (first) {
      status.textContent = "Check the highlighted fields.";
      first.focus();
      return;
    }
    if (turnstileBroken || !currentToken()) {
      status.textContent = turnstileBroken
        ? "The spam check could not load. Try again."
        : "Complete the spam check.";
      return;
    }
    status.textContent = "";
    var button = form.querySelector("[type=submit]");
    button.disabled = true;
    form.setAttribute("aria-busy", "true");
    // A full navigation. GitHub Pages cannot read a cross-origin fetch response,
    // and resetting the widget here would clear the token before the browser posts it.
    HTMLFormElement.prototype.submit.call(form);
  });
})();
