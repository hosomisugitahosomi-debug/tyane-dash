// ===== 計算ロジック（DOMに触らない純粋関数）=====
// ここを直せば表示は自動で変わる。テスト・バックテストからも同じ関数を使う。

// 勝率(0〜1)を勝ち/中立/負けに分類。be=損益分岐勝率(%)
function cls(wr, be) {
  return wr >= be / 100 ? "win" : (wr > 0.5 ? "neu" : "loss");
}

// 金額を「+¥1,234」形式に
function yen(v) {
  return (v < 0 ? "-" : "+") + "¥" + Math.abs(Math.round(v)).toLocaleString();
}

// 指定ペア・期間の日次集計と累積損益
// pairs: ペア名の配列 / from,to: "YYYY-MM-DD"(空可) / amt: 1回の金額 / pay: ペイアウト倍率
// 戻り: { rows:[{d,dw,dl,pnl}](新しい順), series:[{date,cum}](古い順), total:{w,l,n,wr,pnl} }
function aggregate(D, pairs, from, to, amt, pay) {
  var prof = pay - 1;
  var dates = {};
  pairs.forEach(function (p) {
    Object.keys(D.daily[p] || {}).forEach(function (d) {
      if ((!from || d >= from) && (!to || d <= to)) dates[d] = 1;
    });
  });
  var asc = Object.keys(dates).sort();
  var tw = 0, tl = 0, cum = 0, series = [], rows = [];
  asc.forEach(function (d) {
    var dw = 0, dl = 0;
    pairs.forEach(function (p) {
      var x = (D.daily[p] || {})[d];
      if (x) { dw += x.w; dl += x.l; }
    });
    var pnl = dw * amt * prof - dl * amt;
    cum += pnl; tw += dw; tl += dl;
    series.push({ date: d, cum: cum });
    rows.push({ d: d, dw: dw, dl: dl, pnl: pnl });
  });
  var tn = tw + tl;
  rows.reverse();
  return {
    rows: rows,
    series: series,
    total: { w: tw, l: tl, n: tn, wr: tn ? (tw / tn * 100) : 0, pnl: tw * amt * prof - tl * amt }
  };
}

// グループ貼り付け用のテキスト
function summaryText(D) {
  var L = ["[TyanePon 直近成績 " + (D.through || "") + "時点 / 3分判定]"];
  D.pairs.forEach(function (p) {
    var s = D.summary[p] || {}, a = s[7], b = s[30];
    L.push(p + " 直近7日 " + (a ? (a.wr * 100).toFixed(1) + "%(" + a.w + "-" + a.l + ")" : "--") +
      " / 30日 " + (b ? (b.wr * 100).toFixed(1) + "%" : "--"));
  });
  return L.join("\n");
}

// データに含まれる全日付（昇順）
function allDates(D) {
  var a = [];
  D.pairs.forEach(function (p) {
    Object.keys(D.daily[p] || {}).forEach(function (d) { a.push(d); });
  });
  return a.sort();
}

// Node(検証スクリプト)からも使えるように
if (typeof module !== "undefined" && module.exports) {
  module.exports = { cls: cls, yen: yen, aggregate: aggregate, summaryText: summaryText, allDates: allDates };
}
