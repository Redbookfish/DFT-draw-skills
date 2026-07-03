---
name: gaussian-esp
description: Gaussian + Multiwfn + VMD 联用计算分子静电势 (ESP)。当用户需要计算分子表面静电势分布、绘制 ESP 着色分子图、分析亲电/亲核位点、或生成 ESP 立方体文件用于可视化时使用。触发场景包括：静电势、ESP、分子表面静电势、vdW表面静电势、Gaussian波函数分析、Multiwfn定量分子表面分析、VMD静电势着色、亲电亲核位点预测、cube文件生成、ESPiso、密度立方体。
---

# Gaussian ESP 静电势计算

## 环境配置

首次使用前，用户需修改以下路径。所有脚本和命令均从此处读取：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GAUSSIAN_EXEDIR` | `D:\G16W` | Gaussian 安装目录 |
| `GAUSSIAN_EXE` | `D:\G16W\g16.exe` | Gaussian 可执行文件 |
| `MULTIWFN_DIR` | `D:\Multiwfn_3.8_dev_bin_Win64` | Multiwfn 安装目录 |
| `MULTIWFN_EXE` | `D:\Multiwfn_3.8_dev_bin_Win64\Multiwfn.exe` | Multiwfn 可执行文件 |
| `VMD_DIR` | `D:\VMD` | VMD 安装目录 |
| `VMD_EXE` | `D:\VMD\vmd.exe` | VMD 可执行文件 |
| `WORK_DIR` | `%USERPROFILE%\Desktop\ESP计算` | 工作文件夹（输入输出文件存放处） |

> **修改方法**：编辑 `config.json` 中的路径即可。Agent 启动时自动读取。


## 快速入口：已有 fchk 文件

如果用户已提供 `.fchk` 文件（来自之前的计算或他人提供），**跳过阶段 1-3**，直接从 Multiwfn 开始：

```
用户提供 input.fchk
    → 直接跳至阶段 4
    → 复制为 $MULTIWFN_DIR/1.fchk
    → ESPiso.bat
    → VMD 可视化 → 渲染 → {name}ESP.bmp
```

Agent 判断逻辑：检查 `$WORK_DIR` 中的文件类型。若存在 `.fchk` 且用户未提供 `.gjf`，则自动从阶段 4 开始。
## 关键词检查标准

`scripts/check_gjf.py` 自动检查并修正以下项：

| 检查项 | 标准值 | 说明 |
|--------|--------|------|
| #p | 必须有 | 详细输出模式 |
| 泛函 | b3lyp | HF/半经验自动升级 |
| 基组 | 6-311+g(d,p) | 含极化+弥散，ESP 定量分析所需 |
| opt | 必须有 | 几何优化 |
| freq | 必须有 | 频率计算，确认稳定结构 |
| %chk | %chk=文件名.chk | 与输入文件同名 |

**标准 route section**:
```
#p b3lyp/6-311+g(d,p) opt freq
```

> 注意：不需要 `output=wfn`，使用 `formchk` 将 chk 转为 fchk 即可。

## 完整操作流程

### 阶段 1: 检查与修正 Gaussian 输入

```bash
python scripts/check_gjf.py input.gjf        # 仅检查
python scripts/check_gjf.py input.gjf --fix  # 自动修正所有问题
```

### 阶段 2: 运行 Gaussian

```powershell
$env:GAUSS_EXEDIR = "$GAUSSIAN_EXEDIR"
cmd /c "$GAUSSIAN_EXE < input.gjf > input.out"
```

确认 `.out` 末尾 `Normal termination`。
`.chk` 文件命名与输入 `.gjf` 文件同名。

### 阶段 3: 转换 chk → fchk

```bash
formchk input.chk input.fchk
```

`.fchk` 保存在 `$WORK_DIR` 中。


### 阶段 3.5: 画图脚本就位检查（自动检索）

在执行 Multiwfn 和 VMD 画图前，自动检查所需脚本是否存在。若缺失，从 `$MULTIWFN_DIR\examples` 中检索并复制到目标位置：

| 脚本 | 期望位置 | 检索源 |
|------|----------|--------|
| `ESPiso.bat` | `$MULTIWFN_DIR\` | `$MULTIWFN_DIR\examples\` |
| `ESPiso.txt` | `$MULTIWFN_DIR\` | `$MULTIWFN_DIR\examples\` |
| `ESPiso.vmd` | `$VMD_DIR\` | `$MULTIWFN_DIR\examples\` |
| VMD `iso` 脚本 | `$VMD_DIR\` | `$MULTIWFN_DIR\examples\` |
| `VMDrender_full.bat` | `$VMD_DIR\` | `$MULTIWFN_DIR\examples\` |
| `tachyon_WIN32.exe` | `$VMD_DIR\` | `$MULTIWFN_DIR\examples\` |

Agent 操作步骤：
```powershell
# 1. 检查 ESPiso.bat
if (-not (Test-Path "$MULTIWFN_DIR\ESPiso.bat")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Filter "ESPiso.bat" | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName "$MULTIWFN_DIR\" }
}

# 2. 检查 ESPiso.txt（ESPiso.bat 的 Multiwfn 命令输入文件，必须配套）
if (-not (Test-Path "$MULTIWFN_DIR\ESPiso.txt")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Filter "ESPiso.txt" | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName "$MULTIWFN_DIR\" }
}

# 3. 检查 ESPiso.vmd（VMD 的 ESP 可视化状态文件）
if (-not (Test-Path "$VMD_DIR\ESPiso.vmd")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Filter "ESPiso.vmd" | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName "$VMD_DIR\" }
}

# 4. 检查 VMD iso 脚本（通常为 .tcl 或 .vmd 文件，名称含 "iso" 或 "esp"）
if (-not (Test-Path "$VMD_DIR\iso.tcl") -and -not (Test-Path "$VMD_DIR\esp_viz.tcl")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Include "*.tcl","*.vmd" |
             Where-Object { $_.Name -match 'iso|esp|ESP' } | Select-Object -First 1
    if ($found) {
        Copy-Item $found.FullName "$VMD_DIR\iso.tcl"
    } else {
        # 备选：使用 skill 自带的 esp_viz.tcl
        Copy-Item "$SKILL_DIR\assets\esp_viz.tcl" "$VMD_DIR\iso.tcl"
    }
}

# 5. 检查 VMDrender_full.bat
if (-not (Test-Path "$VMD_DIR\VMDrender_full.bat")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Filter "VMDrender*.bat" | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName "$VMD_DIR\" }
}

# 6. 检查 tachyon_WIN32.exe（VMD 外部渲染器）
if (-not (Test-Path "$VMD_DIR\tachyon_WIN32.exe")) {
    $found = Get-ChildItem -Path "$MULTIWFN_DIR\examples" -Recurse -Filter "tachyon_WIN32.exe" | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName "$VMD_DIR\" }
}
```

> 六项检索均失败时，提示用户手动提供对应脚本，或从 Multiwfn 官网下载 examples 压缩包。### 阶段 4: Multiwfn ESPiso.bat

`ESPiso.bat` 位于 `$MULTIWFN_DIR` 中，该脚本期望在 Multiwfn 文件夹内找到编号的 `.fchk` 文件（如 `1.fchk`）。

操作步骤：
1. 将 `input.fchk` 复制到 `$MULTIWFN_DIR`，重命名为 `1.fchk`
2. 如 `ESPiso.bat` 中的文件后缀与输入不匹配，修改 bat 中的后缀
3. 在 `$MULTIWFN_DIR` 中运行 `ESPiso.bat`
4. 脚本自动计算 ESP 格点，输出 `density.cub`、`density1.cub`
5. 脚本自动将 cub 文件移至 `$VMD_DIR`

```bash
cd $MULTIWFN_DIR
ESPiso.bat
```

### 阶段 5: VMD 可视化

1. 打开 VMD
2. Tk Console → 输入 `iso` 回车（调用预置的画图脚本）
3. 调整视角至满意
4. `File` → `Render...` → 选择 `Tachyon` → `Start Rendering`
5. 在 `$VMD_DIR` 中生成 `vmdscene.dat`

> 如果外部 Tachyon 与 VMD 版本不兼容，改用 VMD 内置 `TachyonInternal` 渲染为 TGA，
> 再用 Python PIL 将 TGA 转为 BMP。

### 阶段 6: 最终渲染

```bash
cd $VMD_DIR
VMDrender_full.bat
```

生成 `full.bmp` → 重命名为 `{输入文件名}ESP.bmp` → 移动到 `$WORK_DIR`。

## 文件流转

```
$WORK_DIR/input.gjf
    → g16 → input.out + input.chk
    → formchk → input.fchk
    → 复制为 $MULTIWFN_DIR/1.fchk
    → ESPiso.bat
        → $VMD_DIR/density.cub
        → $VMD_DIR/density1.cub
    → VMD iso 脚本
        → vmdscene.dat
        → VMDrender_full.bat
        → full.bmp → {name}ESP.bmp → $WORK_DIR/
```

## 环境要求

- **Gaussian 16W** (或 Gaussian 16)
- **Multiwfn 3.8** (dev 版，含 `ESPiso.bat`)
- **VMD 1.9.4** (含 `VMDrender_full.bat`)
- **Python 3.8+** (用于 `check_gjf.py` 和 TGA→BMP 转换)
- **Windows** (PowerShell)

## 故障排查

**Gaussian 运行无响应**: 检查 `$env:GAUSS_EXEDIR` 是否设置正确；终止残留的 `g16.exe` 和 `l*.exe` 进程后再重试。

**formchk 报错**: 确认 `.chk` 文件路径正确，且 Gaussian 正常终止后才可转换。

**ESPiso.bat 找不到文件**: 确保 `1.fchk` 已复制到 `$MULTIWFN_DIR`，且文件后缀与 bat 脚本中的一致（`.fchk` 或 `.fch`）。

**脚本缺失（ESPiso.bat / VMDrender_full.bat / iso.tcl）**: 阶段 3.5 会自动从 `$MULTIWFN_DIR\examples` 检索并复制。如果 examples 中也找不到，从 Multiwfn 官网下载 examples 压缩包解压到 `$MULTIWFN_DIR\examples` 后重试。
**VMD 渲染失败**: 使用 VMD 内置 `TachyonInternal` 渲染器，避免外部 `tachyon_WIN32.exe` 兼容性问题。