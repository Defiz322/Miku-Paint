<div align="center">

# ♪ MikuPaint ♪

**A tiny paint studio that sings in teal, pink and purple.**  
*Hatsune Miku Edition · v1.0*

[![Python](https://img.shields.io/badge/python-3.8%2B-39c5bb?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/tkinter-built--in-ff6b9d?style=flat-square)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/license-MIT-b84dff?style=flat-square)](LICENSE)
[![Miku](https://img.shields.io/badge/Miku-39-39c5bb?style=flat-square)](#-behind-the-palette)

**English** · [Русский](#русский) · [日本語](#日本語)

</div>

---

## English

> *"Miku Miku ni shite ageru♪"* — a lightweight desktop paint app built with Python and Tkinter, dressed in Hatsune Miku's colors. No frameworks, no dependencies, just a canvas and good vibes.

### ✨ Features

| | |
|---|---|
| 🎨 **10 tools** | Pencil, brush, eraser, fill, line, rectangle, ellipse, color picker, text, select |
| ↩️ **Undo / Redo** | Up to 50 steps of canvas history |
| 💾 **Project files** | Save and load your work as human-readable `.mipaint` JSON |
| 🖌️ **Adjustable brush** | Size from 1 to 50 px, live preview in the status bar |
| 📐 **Custom canvas** | Any size from 1×1 to 4096×4096 px |
| ⌨️ **Keyboard-first** | Every tool has a single-key shortcut |
| 🌈 **Miku palette** | Teal `#39c5bb`, pink `#ff6b9d`, purple `#b84dff` on a dark stage |

### 🚀 Quick start

**Requirements:** Python 3.8+ with Tkinter (bundled with the official Windows and macOS installers).

```bash
git clone https://github.com/Defiz322/Miku-Paint.git
cd Miku-Paint
python MikuPaint/main.py
```

On Debian/Ubuntu, install Tkinter first if it is missing:

```bash
sudo apt install python3-tk
```

A "Create New Canvas" dialog appears on launch — pick your size, hit **CREATE**, and start drawing.

### ⌨️ Controls

| Action | Shortcut | Action | Shortcut |
|---|---|---|---|
| Pencil | `P` | Line | `L` |
| Brush | `B` | Rectangle | `R` |
| Eraser | `E` | Ellipse | `C` |
| Fill | `F` | Color picker | `I` |
| Text | `T` | Select | `V` |
| Undo | `Ctrl + Z` | Redo | `Ctrl + Y` |
| New | `Ctrl + N` | Open | `Ctrl + O` |
| Save | `Ctrl + S` | | |

Hover over the color swatch in the left toolbar to open the system color picker. Drag the **SIZE** slider to change the brush width.

### 📁 Project format

MikuPaint saves plain JSON, so your drawings stay readable and diff-friendly:

```json
{
  "version": "1.0",
  "app": "MikuPaint",
  "created": "2026-10-25T12:00:00",
  "canvas_width": 800,
  "canvas_height": 600,
  "items": [
    { "type": "line", "coords": [10, 10, 200, 200], "fill": "#39c5bb", "width": "3.0" },
    { "type": "text", "coords": [40, 80], "text": "Miku!", "fill": "#ff6b9d", "font": "Arial 12 bold" }
  ]
}
```

### 🎀 Behind the palette

- `39` is a pun on *Miku* (mi = 3, ku = 9) and on *thank you* — it sits quietly at the bottom of the toolbar.
- The interface uses Miku's signature teal for accents, pink for active states and purple for hover.
- The app is a love letter to Vocaloid and to simple, hackable desktop software: the whole editor lives in a single `MikuPaint/main.py`.

### 🧪 Known limitations

This is a cozy v1.0, not a Photoshop replacement:

- **Fill** paints the entire canvas instead of flood-filling a region.
- **Color picker** is a placeholder and always returns Miku pink.
- **Select** is a stub — no moving, copying or deleting selections yet.
- The eraser paints with the canvas background color, so there is no true transparency.
- Projects can only be saved as `.mipaint`; there is no PNG export yet.

PRs that fix any of these are very welcome — especially a real flood fill. ♪

### 🤝 Contributing

1. Fork the repo and create a branch: `git checkout -b feature/leek-brush`.
2. Keep it dependency-free and in the spirit of the existing code.
3. Open a pull request with a short description and a screenshot, if possible.

### 📜 License & disclaimer

Released under the [MIT License](LICENSE) © 2026 Defiz322.

MikuPaint is an unofficial fan project. Hatsune Miku is a character by Crypton Future Media, Inc. This project is not affiliated with or endorsed by Crypton, Piapro or any Vocaloid rights holder.

---

## Русский

> *«Мику-Мику ни ситэ агэру♪»* — лёгкий графический редактор для рабочего стола на Python и Tkinter в цветах Хацунэ Мику. Без фреймворков, без зависимостей: только холст и хорошее настроение.

### ✨ Возможности

| | |
|---|---|
| 🎨 **10 инструментов** | Карандаш, кисть, ластик, заливка, линия, прямоугольник, эллипс, пипетка, текст, выделение |
| ↩️ **Отмена / повтор** | До 50 шагов истории холста |
| 💾 **Файлы проектов** | Сохранение и загрузка в читаемом JSON-формате `.mipaint` |
| 🖌️ **Гибкая кисть** | Размер от 1 до 50 px, значение видно в строке состояния |
| 📐 **Свой холст** | Любой размер от 1×1 до 4096×4096 px |
| ⌨️ **Горячие клавиши** | У каждого инструмента есть клавиша быстрого доступа |
| 🌈 **Палитра Мику** | Бирюзовый `#39c5bb`, розовый `#ff6b9d`, фиолетовый `#b84dff` на тёмной сцене |

### 🚀 Быстрый старт

**Требования:** Python 3.8+ и Tkinter (входит в официальные установщики Windows и macOS).

```bash
git clone https://github.com/Defiz322/Miku-Paint.git
cd Miku-Paint
python MikuPaint/main.py
```

На Debian/Ubuntu при необходимости установите Tkinter:

```bash
sudo apt install python3-tk
```

При запуске появится окно «Create New Canvas» — выберите размер, нажмите **CREATE** и рисуйте.

### ⌨️ Управление

| Действие | Клавиши | Действие | Клавиши |
|---|---|---|---|
| Карандаш | `P` | Линия | `L` |
| Кисть | `B` | Прямоугольник | `R` |
| Ластик | `E` | Эллипс | `C` |
| Заливка | `F` | Пипетка | `I` |
| Текст | `T` | Выделение | `V` |
| Отменить | `Ctrl + Z` | Повторить | `Ctrl + Y` |
| Новый | `Ctrl + N` | Открыть | `Ctrl + O` |
| Сохранить | `Ctrl + S` | | |

Нажмите на цветной квадрат в левой панели, чтобы выбрать цвет. Ползунок **SIZE** задаёт толщину кисти.

### 📁 Формат проекта

Проекты хранятся в обычном JSON — их удобно читать, сравнивать и править вручную:

```json
{
  "version": "1.0",
  "app": "MikuPaint",
  "created": "2026-10-25T12:00:00",
  "canvas_width": 800,
  "canvas_height": 600,
  "items": [
    { "type": "line", "coords": [10, 10, 200, 200], "fill": "#39c5bb", "width": "3.0" },
    { "type": "text", "coords": [40, 80], "text": "Мику!", "fill": "#ff6b9d", "font": "Arial 12 bold" }
  ]
}
```

### 🎀 Немного о палитре

- `39` — игра слов: *ми* = 3, *ку* = 9, а ещё «спасибо». Число скромно живёт внизу панели инструментов.
- Фирменный бирюзовый цвет Мику используется для акцентов, розовый — для активных кнопок, фиолетовый — для наведения.
- Проект — признание в любви Vocaloid и простому редактируемому коду: весь редактор помещается в одном файле `MikuPaint/main.py`.

### 🧪 Известные ограничения

Это уютная версия v1.0, а не замена Photoshop:

- **Заливка** закрашивает весь холст, а не выбранную область.
- **Пипетка** пока заглушка и всегда возвращает розовый цвет Мику.
- **Выделение** не реализовано: перемещать, копировать и удалять фрагменты нельзя.
- Ластик рисует цветом фона холста — настоящей прозрачности нет.
- Проекты сохраняются только в `.mipaint`; экспорта в PNG пока нет.

Будем рады PR, которые это исправят — особенно настоящей заливке по области. ♪

### 🤝 Участие в разработке

1. Сделайте форк и создайте ветку: `git checkout -b feature/leek-brush`.
2. Сохраняйте стиль кода и обходитесь без внешних зависимостей.
3. Откройте pull request с кратким описанием и, если можно, скриншотом.

### 📜 Лицензия и дисклеймер

Распространяется по [лицензии MIT](LICENSE) © 2026 Defiz322.

MikuPaint — неофициальный фанатский проект. Хацунэ Мику принадлежит Crypton Future Media, Inc. Проект не связан с Crypton, Piapro и правообладателями Vocaloid и не одобрен ими.

---

## 日本語

> *「みくみくにしてあげる♪」* — Python と Tkinter で作られた、初音ミクのカラーをまとった軽量ペイントアプリ。フレームワークも外部依存もなし。キャンバスと気分だけ。

### ✨ 機能

| | |
|---|---|
| 🎨 **10 種類のツール** | 鉛筆、ブラシ、消しゴム、塗りつぶし、直線、矩形、楕円、スポイト、テキスト、選択 |
| ↩️ **元に戻す / やり直し** | 最大 50 ステップの履歴 |
| 💾 **プロジェクトファイル** | 読める JSON 形式 `.mipaint` で保存・読み込み |
| 🖌️ **ブラシサイズ調整** | 1〜50 px、ステータスバーにリアルタイム表示 |
| 📐 **キャンバスサイズ** | 1×1 〜 4096×4096 px まで自由に設定 |
| ⌨️ **キーボード操作** | すべてのツールにショートカットあり |
| 🌈 **ミクのパレット** | ティール `#39c5bb`、ピンク `#ff6b9d`、パープル `#b84dff` のダークステージ |

### 🚀 クイックスタート

**必要なもの:** Python 3.8 以上と Tkinter（Windows / macOS の公式インストーラーに同梱）。

```bash
git clone https://github.com/Defiz322/Miku-Paint.git
cd Miku-Paint
python MikuPaint/main.py
```

Debian / Ubuntu で Tkinter が無い場合:

```bash
sudo apt install python3-tk
```

起動すると「Create New Canvas」ダイアログが開きます。サイズを決めて **CREATE** を押せば、すぐに描き始められます。

### ⌨️ 操作

| 操作 | キー | 操作 | キー |
|---|---|---|---|
| 鉛筆 | `P` | 直線 | `L` |
| ブラシ | `B` | 矩形 | `R` |
| 消しゴム | `E` | 楕円 | `C` |
| 塗りつぶし | `F` | スポイト | `I` |
| テキスト | `T` | 選択 | `V` |
| 元に戻す | `Ctrl + Z` | やり直し | `Ctrl + Y` |
| 新規 | `Ctrl + N` | 開く | `Ctrl + O` |
| 保存 | `Ctrl + S` | | |

左パネルのカラースウォッチをクリックすると色選択ダイアログが開きます。**SIZE** スライダーでブラシの太さを変更できます。

### 📁 プロジェクト形式

プロジェクトはシンプルな JSON なので、中身を読んだり手で編集したりできます:

```json
{
  "version": "1.0",
  "app": "MikuPaint",
  "created": "2026-10-25T12:00:00",
  "canvas_width": 800,
  "canvas_height": 600,
  "items": [
    { "type": "line", "coords": [10, 10, 200, 200], "fill": "#39c5bb", "width": "3.0" },
    { "type": "text", "coords": [40, 80], "text": "ミク！", "fill": "#ff6b9d", "font": "Arial 12 bold" }
  ]
}
```

### 🎀 パレットの秘密

- `39` は「ミ（3）ク（9）」、そして「サンキュー」の語呂合わせ。ツールバーの一番下にひっそり鎮座しています。
- ミクのトレードマークであるティールをアクセントに、ピンクをアクティブ状態に、パープルをホバーに使用。
- エディタ全体が `MikuPaint/main.py` の 1 ファイルに収まった、Vocaloid とハックしやすいデスクトップソフトへのラブレターです。

### 🧪 既知の制限

v1.0 は居心地の良い小さなアトリエであり、Photoshop の代替ではありません:

- **塗りつぶし** は領域ではなくキャンバス全体を塗ります。
- **スポイト** は仮実装で、常にミクピンクを返します。
- **選択** は未実装です（移動・コピー・削除はできません）。
- 消しゴムはキャンバス背景色で塗るため、完全な透明にはなりません。
- 保存形式は `.mipaint` のみ。PNG 書き出しは未対応です。

これらを改善する PR を歓迎します。とくに本物の領域塗りつぶしを待っています。♪

### 🤝 コントリビュート

1. リポジトリをフォークし、ブランチを作成: `git checkout -b feature/leek-brush`
2. 外部依存を増やさず、既存コードの雰囲気を保ってください。
3. 簡単な説明とスクリーンショットを添えて pull request を送ってください。

### 📜 ライセンスと免責事項

[MIT ライセンス](LICENSE) © 2026 Defiz322 のもとで公開されています。

MikuPaint は非公式のファンプロジェクトです。初音ミクは Crypton Future Media, Inc. のキャラクターです。本プロジェクトは Crypton、Piapro、その他 Vocaloid の権利者とは関係なく、承認も受けていません。

---

<div align="center">

**♪ Thanks for stopping by — now go draw something cute. ♪**

`39` · `#39c5bb` · `#ff6b9d` · `#b84dff`

</div>
