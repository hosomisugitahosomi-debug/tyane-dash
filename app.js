// ===== 画面描画（data.js の D と logic.js の関数を使う）=====
var BE = D.be;
var WD = ["日", "月", "火", "水", "木", "金", "土"];

document.getElementById("be").textContent = BE;
document.getElementById("meta").textContent = "データ最終: " + (D.through || "-") + " / 生成: " + D.generated;

// 直近成績カード
(function () {
  var h = "";
  D.pairs.forEach(function (p) {
    var s = D.summary[p] || {}, a = s[7], b = s[30];
    var wr7 = a ? (a.wr * 100).toFixed(1) : "--", c7 = a ? cls(a.wr, BE) : "neu";
    var wr30 = b ? (b.wr * 100).toFixed(1) + "%" : "--", c30 = b ? cls(b.wr, BE) : "neu";
    h += "<div class='pc'><div class='nm'>" + p + "</div>" +
      "<div class='big " + c7 + "'>" + wr7 + (a ? "%" : "") + "</div>" +
      "<div class='wl'>" + (a ? a.w + "勝" + a.l + "敗 / 7日" : "データ無") + "</div>" +
      "<div class='m30'>30日 <span class='" + c30 + "'>" + wr30 + "</span> <span class='small'>" + (b ? "(" + b.w + "-" + b.l + ")" : "") + "</span></div></div>";
  });
  document.getElementById("cards").innerHTML = h;
})();

function copySummary() {
  var t = summaryText(D);
  if (navigator.clipboard) {
    navigator.clipboard.writeText(t).then(function () {
      alert("コピーしました。グループに貼り付けて投稿してください。");
    }, function () { prompt("コピーして使ってください:", t); });
  } else prompt("コピーして使ってください:", t);
}

// 期間別テーブル
(function () {
  var h = "<thead><tr><th>ペア</th><th>7日</th><th>14日</th><th>30日</th></tr></thead><tbody>";
  D.pairs.forEach(function (p) {
    var s = D.summary[p] || {};
    h += "<tr><td>" + p + "</td>";
    [7, 14, 30].forEach(function (k) {
      var x = s[k];
      if (x) h += "<td><span class='pct " + cls(x.wr, BE) + "'>" + (x.wr * 100).toFixed(1) + "%</span><br><span class='small'>" + x.w + "-" + x.l + "</span></td>";
      else h += "<td class='small'>-</td>";
    });
    h += "</tr>";
  });
  document.getElementById("summary").innerHTML = h + "</tbody>";
})();

var sel = document.getElementById("fpair");
sel.innerHTML = "<option value='__all'>全ペア</option>" + D.pairs.map(function (p) { return "<option>" + p + "</option>"; }).join("");

var ff = document.getElementById("ffrom"), ft = document.getElementById("fto");
(function () {
  var ad = allDates(D), dmin = ad[0], dmax = ad[ad.length - 1];
  if (!dmin) return;
  ff.min = ft.min = dmin; ff.max = ft.max = dmax;
  var def = new Date(dmax); def.setDate(def.getDate() - 30);
  ff.value = def.toISOString().slice(0, 10); ft.value = dmax;
})();

function drawChart(series) {
  var c = document.getElementById("chart"), dpr = window.devicePixelRatio || 1;
  var W = c.clientWidth, H = 170;
  c.width = W * dpr; c.height = H * dpr;
  var x = c.getContext("2d"); x.scale(dpr, dpr); x.clearRect(0, 0, W, H);
  if (series.length < 2) { x.fillStyle = "#9aa0ac"; x.font = "12px sans-serif"; x.fillText("データ不足", 10, 20); return; }
  var vals = series.map(function (s) { return s.cum; });
  var mn = Math.min(0, Math.min.apply(null, vals)), mx = Math.max(0, Math.max.apply(null, vals));
  if (mx === mn) mx = mn + 1;
  var pad = 24, w = W - pad * 2, h = H - pad * 2;
  function px(i) { return pad + w * i / (series.length - 1); }
  function py(v) { return pad + h * (1 - (v - mn) / (mx - mn)); }
  x.strokeStyle = "#2a2e38"; x.lineWidth = 1;
  var zy = py(0); x.beginPath(); x.moveTo(pad, zy); x.lineTo(W - pad, zy); x.stroke();
  var last = vals[vals.length - 1];
  x.strokeStyle = last >= 0 ? "#3ecf8e" : "#ff6b6b"; x.lineWidth = 2; x.beginPath();
  series.forEach(function (s, i) { var X = px(i), Y = py(s.cum); if (i === 0) x.moveTo(X, Y); else x.lineTo(X, Y); });
  x.stroke();
  x.fillStyle = "#9aa0ac"; x.font = "11px sans-serif";
  x.fillText(yen(mx), 2, pad - 6); x.fillText(yen(mn), 2, H - 6);
}

function render() {
  var pairs = sel.value === "__all" ? D.pairs : [sel.value];
  var amt = parseFloat(document.getElementById("amt").value) || 0;
  var pay = parseFloat(document.getElementById("pay").value) || 1;
  var r = aggregate(D, pairs, ff.value, ft.value, amt, pay);

  var h = "<thead><tr><th>日付</th><th>勝-敗</th><th>損益</th></tr></thead><tbody>";
  r.rows.forEach(function (row) {
    var wd = WD[new Date(row.d).getDay()];
    var c = row.dw > row.dl ? "win" : (row.dw < row.dl ? "loss" : "neu");
    var pc = row.pnl >= 0 ? "win" : "loss";
    h += "<tr><td>" + row.d.slice(5) + " " + wd + "</td><td class='" + c + "'>" + row.dw + "-" + row.dl + "</td><td class='" + pc + "'>" + yen(row.pnl) + "</td></tr>";
  });
  if (r.rows.length === 0) h += "<tr><td colspan='3' class='small'>該当なし</td></tr>";
  document.getElementById("daily").innerHTML = h + "</tbody>";

  var t = r.total;
  document.getElementById("agg").innerHTML =
    "<div class='stat'><div class='n'>" + t.n + "</div><div class='l'>エントリー</div></div>" +
    "<div class='stat'><div class='n " + (t.wr >= BE ? "win" : "loss") + "'>" + t.wr.toFixed(1) + "%</div><div class='l'>勝率</div></div>" +
    "<div class='stat'><div class='n'>" + t.w + "-" + t.l + "</div><div class='l'>勝-敗</div></div>" +
    "<div class='stat'><div class='n " + (t.pnl >= 0 ? "win" : "loss") + "'>" + yen(t.pnl) + "</div><div class='l'>損益</div></div>";
  drawChart(r.series);
}

sel.onchange = ff.onchange = ft.onchange = render;
document.getElementById("amt").oninput = render;
document.getElementById("pay").oninput = render;
window.addEventListener("resize", render);
render();

document.getElementById("foot").innerHTML =
  "※終値ベースの簡易判定。実際のスプレッド・約定で数%下振れ。<br>※最新はColab/更新.bat取得の最終データ+生成時点まで。";
