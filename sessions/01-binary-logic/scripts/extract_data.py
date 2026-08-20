"""index.html に埋め込まれた var D={...} を data.json として取り出す。"""
import json, re, pathlib

root = pathlib.Path(__file__).resolve().parents[3]
html = (root / "index.html").read_text(encoding="utf-8")
m = re.search(r"var D=(\{.*?\});", html, re.S)
if not m:
    raise SystemExit("var D が見つからない")
data = json.loads(m.group(1))
out = pathlib.Path(__file__).parent / "data.json"
out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
print("pairs:", data["pairs"])
print("through:", data["through"], "/ be:", data["be"])
for p in data["pairs"]:
    d = data["daily"][p]
    n = sum(v["w"] + v["l"] for v in d.values())
    w = sum(v["w"] for v in d.values())
    print(f"{p:6s} 日数{len(d):4d} トレード{n:5d} 勝率{w/n*100:5.1f}%")
