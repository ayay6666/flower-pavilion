# 花信小筑 (Flower Pavilion)

> 零依赖纯前端中式田园养花与插花休闲网页游戏，适配桌面与移动端，支持在线游玩与单文件离线打包。

- **在线游玩**：[https://ayay6666.github.io/flower-pavilion/](https://ayay6666.github.io/flower-pavilion/)
- **单文件离线版**：[GitHub Releases](https://github.com/ayay6666/flower-pavilion/releases)（下载单个 HTML 文件，离线用浏览器打开即可游玩）

---

## 核心玩法

- **小院种花**
  - 开垦花畦、播种浇水除虫，支持横划连种、连采、连浇与杂交育种。
  - 收录 35 种花卉及多色变种（含稀有杂交品种与山野花卉），配合昼夜天光变化与 24 节气当令花提示及专属插图。
- **花艺台插花**
  - 内置 10 款花器与 8 类器型物理约束（大肚敞口、大肚收口、圆罐、细颈、纤瘦高挑、细长喇叭、直筒、水盘），支持水下花茎渲染与花枝形态调整。
  - 实时意境评分与甲 / 乙 / 丙品级盖章，支持立轴高清 PNG 画片导出、花架珍藏锁定以及花笺订单交付。
- **小镇、花铺与山野**
  - **小镇**：在陶坊拉坯自制陶器，参与花展评比，收取乡邻知己时令来信并赠花互动。
  - **花铺**：选购时令花种、花器、杂货与雇工，亦可收购富余花材。
  - **山野**：亲自操控人物探险（点地面行走、点物件采摘），溪谷、竹海、荷塘三张地图随乡邻支线逐步开放；路上可采野花、露水、花种与陶土，玩扑蝶、打水漂、拨草寻踪三种小游戏，收集各地图的「拾遗」。
- **手账与体验细节**
  - 内置花谱图鉴与 16 枚成就徽章。
  - 支持离线近况小结、掌柜分步引导、五声级进配乐、本地自动存档及 JSON 存档导出 / 导入。

---

## 本地运行

项目为纯静态 HTML + WebP 资源，无需安装 Node.js 或构建工具即可直接运行：

```bash
python3 -m http.server 8770
```

启动后在浏览器中访问 `http://localhost:8770`。

---

## 单文件打包与字体子集维护

仓库自带 [`build.py`](build.py) 脚本（仅依赖 Python 3 标准库），可将 `index.html` 与 `assets/` 下全部图片内嵌为单个可独立分发的 HTML 文件：

```bash
# 生成单文件离线版：dist/花信小筑.html
python3 build.py
```

- 打包过程会自动对 CSS / HTML 中重复引用的资源去重，并将动态脚本用到的图片转为按需懒加载 Blob（同时保留 Blob 供离线导出高清画片）。
- 当界面展示文案或诗意题名库新增生字时，可运行以下命令重新提取并更新内嵌在 `index.html` 中的马善政楷体字体子集（需联网请求 Google Fonts）：

```bash
python3 build.py --subset-font
```

---

## 目录结构

```text
.
├── index.html                  # 游戏主入口（HTML / CSS / JS 与内嵌书法字体子集）
├── build.py                    # 单文件离线打包与字体子集更新脚本
├── assets/                     # 326 张 WebP 游戏美术资源
│   ├── jq/                     # 二十四节气当令花插图（00.webp ~ 23.webp）
│   └── st/                     # 花材与植物贴图
├── .github/workflows/
│   ├── pages.yml               # 校验 build.py 并自动部署 GitHub Pages
│   └── release.yml             # 推送 v* 标签时自动发布单文件离线版 Release
└── LICENSE                     # MIT License
```

---

## 版本发布说明

已配置 GitHub Actions 自动发版工作流。推送以 `v` 开头的版本标签即可自动构建并发布单文件离线 HTML 到 GitHub Releases：

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 开源协议与字体声明

- 本项目代码采用 [MIT License](LICENSE) 开源。
- 内嵌标题书法字体「马善政楷体（Ma Shan Zheng）」遵循 [SIL Open Font License 1.1](https://scripts.sil.org/OFL) 开源协议。
