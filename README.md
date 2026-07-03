# DFT 绘图技能集

DFT计算分子轨道与静电势绘图 Codex 技能合集。

## 技能列表

| 技能 | 用途 | 工具链 |
|------|------|--------|
| `homo-lumo` | HOMO/LUMO 前线分子轨道可视化 | Gaussian → Multiwfn → VMD |
| `gaussian-esp` | 分子表面静电势 (ESP) 分布计算与着色 | Gaussian → Multiwfn → VMD |

## 安装

### 方式一：克隆整个仓库

```powershell
git clone https://github.com/Redbookfish/DFT-draw-skills.git

# 安装全部技能（含 assets、references、scripts 等完整文件夹）
Copy-Item .\DFT-draw-skills\homo-lumo "$env:USERPROFILE\.codex\skills\homo-lumo" -Recurse
Copy-Item .\DFT-draw-skills\gaussian-esp "$env:USERPROFILE\.codex\skills\gaussian-esp" -Recurse
```

### 方式二：只安装单个技能

```powershell
git clone --depth 1 --filter=blob:none --sparse https://github.com/Redbookfish/DFT-draw-skills.git
cd DFT-draw-skills
git sparse-checkout set homo-lumo   # 或 gaussian-esp
Copy-Item .\homo-lumo "$env:USERPROFILE\.codex\skills\homo-lumo" -Recurse
```

### 方式三：让 Codex 帮你装

在 Codex 对话中输入：

> 请从 https://github.com/Redbookfish/DFT-draw-skills.git 安装 skills，把仓库中所有技能文件夹完整复制到 `%USERPROFILE%\.codex\skills\` 下

### 装后配置

修改各技能目录下的 `config.json`，填入本机软件路径：

```json
{
  "gaussian": { "exe": "D:\\G16W\\g16.exe" },
  "multiwfn": { "exe": "D:\\Multiwfn\\Multiwfn.exe" },
  "vmd": { "exe": "D:\\VMD\\vmd.exe" },
  "work_dir": "你的工作文件夹路径"
}
```

## 环境要求

- **Gaussian 16** / Gaussian 16W
- **Multiwfn 3.8**（showorb 系列脚本自带）
- **VMD 1.9.4**
- **Python 3.8+**
- **Windows** (PowerShell)

## 功能特性

- 自动检查/修正 Gaussian 输入关键词
- 自动解析 HOMO/LUMO 轨道编号与能量
- 高分辨率渲染（2048x2048，告别默认 512x512 糊图）
- 可调等值面 (isovalue)
- ESP 定量分子表面分析 + 亲电/亲核位点预测

## 结构

```
DFT-draw-skills/
├── README.md
├── homo-lumo/          # 前线轨道
│   ├── SKILL.md
│   ├── config.json
│   ├── agents/openai.yaml
│   └── scripts/
└── gaussian-esp/       # 静电势
    ├── SKILL.md
    ├── config.json
    ├── agents/openai.yaml
    ├── assets/
    ├── references/
    └── scripts/
```

## 致谢与引用

本技能集中的 Multiwfn 操作流程学习自 **卢天（Sob）老师** 的网络教程。Multiwfn 是一款免费、开源的波函数分析程序，由卢天老师开发维护。

**发表文章时请务必正确引用 Multiwfn：**

更多资源：
- Multiwfn 官网: [http://sobereva.com/multiwfn](http://sobereva.com/multiwfn)
- 卢天老师博客（计算化学社）: [http://sobereva.com](http://sobereva.com)

## 打赏

如果这些技能对你有帮助，欢迎请我喝杯咖啡 ☕


<img src="assets/alipay_donate.jpg" alt="支付宝打赏" width="250">

