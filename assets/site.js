(function () {
  var status = document.getElementById("contact-status");
  if (status && /[?&]sent=1/.test(location.search)) {
    status.hidden = false;
    status.className = "form-status ok";
    status.textContent = "Thanks. Your message was sent. We will reply by email.";
  }
  var input = document.getElementById("code-search");
  var out = document.getElementById("code-results");
  var dataEl = document.getElementById("code-index");
  if (!input || !out || !dataEl) return;
  var data = JSON.parse(dataEl.textContent);
  function norm(s) { return (s || "").toLowerCase().replace(/[^a-z0-9]/g, ""); }
  function show(q) {
    var n = norm(q);
    out.innerHTML = "";
    if (!n) return;
    var hits = data.filter(function (d) {
      return norm(d.code + " " + d.aliases + " " + d.brand + " " + d.appliance + " " + d.meaning).indexOf(n) !== -1;
    }).slice(0, 12);
    if (!hits.length) {
      var li = document.createElement("li");
      li.textContent = "No matching code in the pages we have checked. Try the brand list, or the code as printed, without spaces.";
      out.appendChild(li);
      return;
    }
    hits.forEach(function (d) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = d.path;
      a.textContent = d.brand + " " + d.appliance + " " + d.code;
      li.appendChild(a);
      li.appendChild(document.createTextNode(": " + d.meaning));
      out.appendChild(li);
    });
  }
  input.addEventListener("input", function () { show(input.value); });
  var params = new URLSearchParams(location.search);
  var preset = params.get("code");
  if (preset) { input.value = preset; show(preset); }
})();
