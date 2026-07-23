/*
 * Next BJJ class badge — a sticky card fixed to the right edge on every page.
 *
 * Reads /data/schedule.json (the same file that builds the /schedule/ page)
 * and shows the next upcoming BJJ session for BOTH tracks — Adults and Kids —
 * relative to *Manila* wall-clock time (correct regardless of the visitor's
 * own timezone). Self-contained: injects its own markup and styles, so it only
 * needs a single <script> tag per page, and links to /schedule/.
 *
 * Scope: BJJ only (type === "bjj"). Classes whose title matches isKids() go in
 * the Kids row, everything else BJJ in the Adults row. Each row shows the
 * relative day (NOW/TODAY/TOMORROW/weekday) + start time + class title. A row
 * is omitted if that track has no class in the schedule. Colours/fonts mirror
 * the site's Tailwind tokens (warm-dark / cream / terracotta / gold /
 * Bricolage Grotesque).
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

  // Soonest class matching `pred`, given a pre-computed `now`. Returns
  // { c, deltaMin, daysAhead, ongoing } or null. deltaMin is minutes until
  // start (0 while a class is ongoing).
  function nextMatching(classes, now, pred) {
    var nowAbs = now.dow * MIN_PER_DAY + now.minutes;
    var best = null;

    classes.forEach(function (c) {
      if (!pred(c)) return;
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

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
    });
  }

  // One "TRACK · WHEN / time — title" row.
  function rowHtml(track, info) {
    var when = relLabel(info);
    var time = info.ongoing ? "Now" : esc(info.c.start);
    return (
      '<span class="nt-row nt-' + track.toLowerCase() + '">' +
      '<span class="nt-dot" aria-hidden="true"></span>' +
      '<span class="nt-col">' +
      '<span class="nt-kicker">' + track + " · " + when + "</span>" +
      '<span class="nt-main"><span class="nt-time">' + time + "</span> — " + esc(info.c.title) + "</span>" +
      "</span></span>"
    );
  }

  function injectStyles() {
    var style = document.createElement("style");
    style.textContent = [
      "#next-training{position:fixed;right:0;top:50%;transform:translateY(-50%);z-index:40;",
      "display:block;padding:.85rem 1.15rem;text-decoration:none;",
      "background:rgba(28,20,16,.95);backdrop-filter:blur(8px);color:#f5f0e8;",
      "border:1px solid rgba(235,228,216,.14);border-right:none;border-radius:.7rem 0 0 .7rem;",
      "box-shadow:0 8px 30px rgba(0,0,0,.35);font-family:'DM Sans',system-ui,sans-serif;line-height:1.15;",
      "transform-origin:right center;transition:padding-right .25s ease,box-shadow .25s ease;",
      "opacity:0;animation:nt-in .5s ease .2s forwards}",
      "@keyframes nt-in{to{opacity:1}}",
      "#next-training:hover{padding-right:1.5rem;box-shadow:0 10px 36px rgba(192,70,43,.28)}",
      "#next-training .nt-head{display:block;font-family:'Bricolage Grotesque',system-ui,sans-serif;",
      "font-size:.56rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#c89b3c;margin-bottom:.55rem}",
      "#next-training .nt-row{display:flex;align-items:flex-start;gap:.55rem}",
      "#next-training .nt-row + .nt-row{margin-top:.55rem;padding-top:.55rem;border-top:1px solid rgba(235,228,216,.1)}",
      "#next-training .nt-dot{width:8px;height:8px;border-radius:50%;flex:none;margin-top:.28rem;background:#c0462b;",
      "box-shadow:0 0 0 0 rgba(192,70,43,.6);animation:nt-pulse 2.4s ease-out infinite}",
      "#next-training .nt-kids .nt-dot{background:#c89b3c;box-shadow:0 0 0 0 rgba(200,155,60,.6);animation-name:nt-pulse-gold}",
      "@keyframes nt-pulse{0%{box-shadow:0 0 0 0 rgba(192,70,43,.55)}70%{box-shadow:0 0 0 9px rgba(192,70,43,0)}100%{box-shadow:0 0 0 0 rgba(192,70,43,0)}}",
      "@keyframes nt-pulse-gold{0%{box-shadow:0 0 0 0 rgba(200,155,60,.55)}70%{box-shadow:0 0 0 9px rgba(200,155,60,0)}100%{box-shadow:0 0 0 0 rgba(200,155,60,0)}}",
      "#next-training .nt-col{display:flex;flex-direction:column}",
      "#next-training .nt-kicker{font-family:'Bricolage Grotesque',system-ui,sans-serif;",
      "font-size:.58rem;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:#9a8d82}",
      "#next-training .nt-main{font-size:.9rem;font-weight:600;margin-top:.1rem;white-space:nowrap}",
      "#next-training .nt-main .nt-time{color:#c89b3c}",
      "@media (max-width:640px){#next-training{top:auto;bottom:1rem;right:1rem;transform:none;",
      "border-radius:.7rem;border-right:1px solid rgba(235,228,216,.14);padding:.7rem .95rem}",
      "#next-training:hover{padding-right:.95rem}#next-training .nt-main{font-size:.82rem}}",
      "@media (prefers-reduced-motion:reduce){#next-training,#next-training .nt-dot{animation:none;opacity:1}}",
    ].join("");
    document.head.appendChild(style);
  }

  function render(adult, kids) {
    injectStyles();

    var rows = "";
    var aria = [];
    if (adult) {
      rows += rowHtml("Adults", adult);
      aria.push("Adults " + relLabel(adult) + " " + adult.c.start + " " + adult.c.title);
    }
    if (kids) {
      rows += rowHtml("Kids", kids);
      aria.push("Kids " + relLabel(kids) + " " + kids.c.start + " " + kids.c.title);
    }

    var a = document.createElement("a");
    a.id = "next-training";
    a.href = "/schedule/";
    a.setAttribute("aria-label", "Next BJJ class — " + aria.join("; "));
    a.innerHTML = '<span class="nt-head">Next BJJ Class</span>' + rows;
    document.body.appendChild(a);
  }

  function init() {
    fetch("/data/schedule.json")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !Array.isArray(data.classes)) return;
        var now = manilaNow();
        var isBjj = function (c) { return c.type === "bjj"; };
        var adult = nextMatching(data.classes, now, function (c) { return isBjj(c) && !isKids(c); });
        var kids = nextMatching(data.classes, now, function (c) { return isBjj(c) && isKids(c); });
        if (adult || kids) render(adult, kids);
      })
      .catch(function () { /* fail silent — badge is a nicety, not critical */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
