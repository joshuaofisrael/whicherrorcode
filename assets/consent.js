/* Cookie banner and Google Analytics 4 loader.
   Consent Mode v2 defaults are set in the page head (all denied).
   This file requests gtag only after the visitor accepts. */
(function () {
  var tag = document.querySelector("script[data-ga4-loader]");
  if (!tag || typeof window.gtag !== "function") return;
  var id = tag.getAttribute("data-ga4-id") || "";
  var srcBase = tag.getAttribute("data-ga4-src") || "https://www.googletagmanager.com/gtag/js";
  var key = "wec-consent";
  var banner = document.getElementById("cookie-banner");
  var loaded = false;

  function read() {
    try { return localStorage.getItem(key) || ""; } catch (e) { return ""; }
  }
  function write(value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }
  function show(moveFocus) {
    if (!banner) return;
    banner.hidden = false;
    if (!moveFocus) return;
    var accept = document.getElementById("cookie-accept");
    if (accept) accept.focus();
  }
  function hide() {
    if (banner) banner.hidden = true;
  }
  function consent(analytics) {
    window.gtag("consent", "update", {
      analytics_storage: analytics,
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied"
    });
  }
  function load() {
    if (!id || loaded) return;
    loaded = true;
    consent("granted");
    var script = document.createElement("script");
    script.async = true;
    script.src = srcBase + "?id=" + encodeURIComponent(id);
    document.head.appendChild(script);
    window.gtag("js", new Date());
    window.gtag("config", id);
  }
  var saved = read();
  if (saved === "accepted") {
    hide();
    load();
  } else if (saved === "rejected") {
    hide();
    consent("denied");
  } else {
    show(false);
  }
  var acceptBtn = document.getElementById("cookie-accept");
  var rejectBtn = document.getElementById("cookie-reject");
  if (acceptBtn) acceptBtn.addEventListener("click", function () {
    write("accepted");
    hide();
    load();
  });
  if (rejectBtn) rejectBtn.addEventListener("click", function () {
    write("rejected");
    hide();
    consent("denied");
  });
  var settings = document.getElementById("cookie-settings");
  if (settings) settings.addEventListener("click", function (event) {
    event.preventDefault();
    show(true);
  });
})();
