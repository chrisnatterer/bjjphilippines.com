/*
 * Next BJJ class badge — a sticky pill fixed to the right edge on every page.
 *
 * Reads /data/schedule.json (the same file that builds the /schedule/ page),
 * finds the next upcoming BJJ session relative to *Manila* wall-clock time
 * (so it's correct regardless of the visitor's own timezone), and renders a
 * small pill that links to /schedule/. Self-contained: injects its own markup
 * and styles, so it only needs a single <script> tag per page.
 *
 * Scope: BJJ only (type === "bjj"), excluding kids classes — the badge is a
 * prospect-facing "when can I come train" signal, so a children's class
 * shouldn't surface as the next session. To include everything, drop the
 * isKids() filter in nextClass(). Colours/fonts mirror the site's Tailwind
 * tokens (warm-dark / cream / terracotta / Bricolage Grotesque).
 */
(function () {
  "use strict";

  var TZ = "Asia/Manila";
  // schedule.json day labels -> JS getDay() index (0 = Sunday)
  var DOW = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  var WEEKDAY = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
  var MIN_PER_DAY = 1440;
  var WEEK_MIN = 7 * MIN_PER_DAY;

  // Current Manila day-of-week + minutes-since-midnight, independent of the
  // visitor's local timezone.
  function manilaNow() {
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: TZ, weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false,
    }).formatToParts(new Date());
    var get = function (t) { return (parts.find(function (p) { return p.type === t; }) || {}).value; };
    var wd = get("weekday");                 // "Mon", "Tue", ...
    var hour = parseInt(get("hour"), 10) % 24; // Intl can emit "24" at midnight
    var min = parseInt(get("minute"), 10);
    return { dow: DOW[wd], minutes: hour * 60 + min };
  }

  function toMinutes(hhmm) {
    var m = /^(\d{1,2}):(\d{2})$/.exec(hhmm.trim());
    return m ? parseInt(m[1], 10) * 60 + parseInt(m[2], 10) : null;
  }

  function isKids(c) {
    return /kids?|junior|youth/i.test(c.title || "");
  }

  // Returns { class, deltaMin, daysAhead, ongoing } for the soonest BJJ class,
  // or null. deltaMin is minutes until start (<=0 while a class is ongoing).
  function nextClass(classes) {
    var now = manilaNow();
    var nowAbs = now.dow * MIN_PER_DAY + now.minutes;
    var best = null;

    classes.forEach(function (c) {
      if (c.type !== "bjj" || isKids(c)) return;
      var start = toMinutes(c.start);
      var end = toMinutes(c.end);
      if (start == null) return;
      var startAbs = DOW[c.day] * MIN_PER_DAY + start;

      // Minutes from now to this occurrence's start, wrapped into [0, week).
      var delta = ((startAbs - nowAbs) % WEEK_MIN + WEEK_MIN) % WEEK_MIN;

      // Ongoing right now? A start within the last `dur` minutes wraps to a
      // value just below WEEK_MIN — treat that (and delta 0) as live.
      var dur = end != null && end > start ? end - start : 0;
      var live = delta === 0 || delta > WEEK_MIN - dur;
      if (live) delta = 0;

      if (!best || delta < best.delta) {
        best = { c: c, delta: delta, live: live };
      }
    });

    if (!best) return null;
    var daysAhead = Math.floor((nowAbs + best.delta) / MIN_PER_DAY) - now.dow;
    if (daysAhead < 0) daysAhead += 7;
    return { c: best.c, deltaMin: best.delta, daysAhead: daysAhead, ongoing: best.live };
  }

  function relLabel(info) {
    if (info.ongoing) return "NOW";
    if (info.daysAhead === 0) return "TODAY";
    if (info.daysAhead === 1) return "TOMORROW";
    return WEEKDAY[DOW[info.c.day]];
  }

  function render(info) {
    var style = document.createElement("style");
    style.textContent = [
      "#next-training{position:fixed;right:0;top:50%;transform:translateY(-50%);z-index:40;",
      "display:flex;align-items:center;gap:.6rem;padding:.7rem 1.15rem;",
      "background:rgba(28,20,16,.95);backdrop-filter:blur(8px);color:#f5f0e8;",
      "border:1px solid rgba(235,228,216,.14);border-right:none;border-radius:.6rem 0 0 .6rem;",
      "box-shadow:0 8px 30px rgba(0,0,0,.35);text-decoration:none;",
      "font-family:'DM Sans',system-ui,sans-serif;line-height:1.15;",
      "transform-origin:right center;transition:padding-right .25s ease,box-shadow .25s ease;",
      "opacity:0;animation:nt-in .5s ease .2s forwards}",
      "@keyframes nt-in{to{opacity:1}}",
      "#next-training:hover{padding-right:1.5rem;box-shadow:0 10px 36px rgba(192,70,43,.28)}",
      "#next-training .nt-dot{width:8px;height:8px;border-radius:50%;background:#c0462b;flex:none;",
      "box-shadow:0 0 0 0 rgba(192,70,43,.6);animation:nt-pulse 2.4s ease-out infinite}",
      "@keyframes nt-pulse{0%{box-shadow:0 0 0 0 rgba(192,70,43,.55)}70%{box-shadow:0 0 0 9px rgba(192,70,43,0)}100%{box-shadow:0 0 0 0 rgba(192,70,43,0)}}",
      "#next-training .nt-kicker{font-family:'Bricolage Grotesque',system-ui,sans-serif;",
      "font-size:.58rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#9a8d82}",
      "#next-training .nt-main{font-size:.9rem;font-weight:600;margin-top:.12rem;white-space:nowrap}",
      "#next-training .nt-main .nt-time{color:#c89b3c}",
      "@media (max-width:640px){#next-training{top:auto;bottom:1rem;right:1rem;transform:none;",
      "border-radius:.6rem;border-right:1px solid rgba(235,228,216,.14);padding:.6rem .9rem}",
      "#next-training:hover{padding-right:.9rem}#next-training .nt-main{font-size:.82rem}",
      "#next-training{animation:nt-in .5s ease .2s forwards}}",
      "@media (prefers-reduced-motion:reduce){#next-training,#next-training .nt-dot{animation:none;opacity:1}}",
    ].join("");
    document.head.appendChild(style);

    var kicker = "Next BJJ Class · " + relLabel(info);
    var timeLabel = info.ongoing ? "Now — " : info.c.start + " — ";
    var a = document.createElement("a");
    a.id = "next-training";
    a.href = "/schedule/";
    a.setAttribute("aria-label", kicker + ": " + info.c.title + " at " + info.c.start);
    a.innerHTML =
      '<span class="nt-dot" aria-hidden="true"></span>' +
      '<span class="nt-text">' +
      '<span class="nt-kicker">' + kicker + "</span><br>" +
      '<span class="nt-main">' +
      (info.ongoing ? '<span class="nt-time">Now</span> — ' : '<span class="nt-time">' + esc(info.c.start) + "</span> — ") +
      esc(info.c.title) +
      "</span></span>";
    document.body.appendChild(a);
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
    });
  }

  function init() {
    fetch("/data/schedule.json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !Array.isArray(data.classes)) return;
        var info = nextClass(data.classes);
        if (info) render(info);
      })
      .catch(function () { /* fail silent — badge is a nicety, not critical */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
