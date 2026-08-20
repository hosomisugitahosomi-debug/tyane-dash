# FundedElite サポートへの確認事項

公式FAQで解決した項目は削除済み。**残り2問。**

### 英語（そのままコピペ）

> Hello,
>
> Could you please clarify two things?
>
> **1.** How is the "scalp limit" shown on the client dashboard determined?
> Please tell me the exact amount, or the formula used to calculate it.
>
> **2.** Could you provide the typical spread for **GBPJPYc, EURJPYc and BTCUSD**?
> The "Tradable Instruments and commissions" article lists the symbols but not the spreads.
> Also, regarding the commission table in that article: the heading says
> "Futures & Derivatives trading commissions" — does the **$3 FX commission apply to spot FX as well**,
> and is it **per side or per round turn, per standard lot**?
>
> Thank you.

### 日本語（日本語サポート向け）

> お世話になります。2点確認させてください。
>
> **1.** ダッシュボードに表示される「スキャルピング上限額（scalp limit）」は
> どのように決まりますか？ 具体的な金額または算出方法を教えてください。
>
> **2.** GBPJPYc / EURJPYc / BTCUSD の平均スプレッドを教えてください。
> また「取引可能な金融商品および手数料」ページの手数料表は見出しが
> 「先物・デリバティブ取引手数料」となっていますが、**FXの$3はスポットFXにも適用されますか？**
> **片道か往復か、1ロットあたりか**もあわせて教えてください。

| # | 何のために聞くか |
|---|---|
| 2 | 損益分岐の計算に必要。これが出ないと合否判定ができない |

## 回答記入欄
| # | 回答 | 確認日 |
|---|---|---|
| 1 | **回答済み。** スキャル上限は口座サイズ連動（$10k口座で$150＝1.5%）。チャレンジ中は利益の小さいスキャル1〜2回なら見逃される場合あり、それ以上は不合格。Funded段階は1回でも分配減額・口座リセットの可能性。上限超過はハードブリーチで口座終了・利益没収 | 2026-08-20 |
| 2 | | |

---

## 解決済み（公式FAQで確認）

| 元の質問 | 回答 |
|---|---|
| 3分保有のEAはHFTに該当するか | **該当しない見込み。** FAQはHFTをSEC基準（コロケーション、大量発注と即時取消等）で定義し、**「3分以上保有すればHFTフラグを回避できる」**と明記 |
| Scalping Add-onは必要か | **不要。** 3分以上保有するなら通常口座でよい |
| プラン別のDLL・MLL・DD方式 | LITE1: 3% / 8%可変 / STATIC　LITE2: 4% / 8%可変 / MLLはSTATIC・DLLはEOD　1step+リトライ: 3% / 8%可変 / STATIC　インスタント: 3% / 6% / トレーリング　フラッシュ: 評価フェーズはSTATIC |
| 戦略リスク制限の枠は決済後に戻るか | **戻らない。** 同一取引日・同一商品の全取引が合算され、決済日に計算される |
| 一貫性ルールの計算式 | 口座開設時（または前回出金時）からの累計利益の30%が1日の利益上限 |
| 最低保有時間・違反時の扱い | 3分（アドオン付き30秒）。違反はソフトブリーチ扱いで分配30%に減額＋出金サイクルリセット |
| EAの使用可否 | 許可。ただし共有EA（他人と同一EAでの一斉売買）は不可 |
