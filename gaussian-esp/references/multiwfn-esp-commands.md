# Multiwfn ESP 功能深度参考

## 主功能 12: 定量分子表面分析 (Quantitative Molecular Surface Analysis)

这是 ESP 分析最核心的功能入口。进入后的子菜单：

### 子功能 0: 开始分析 (Start analysis)

标准流程:
1. 选择表面类型 (vdW / SAS / 电子密度等值面)
2. 选择要映射到表面的函数 (默认 ESP)
3. 选择输出选项 (屏幕输出 / 文件输出 / 两者)

**vdW 表面定义** (常用):
- 电子密度 ρ = 0.001 e/Bohr³ (Bader 定义)
- 电子密度 ρ = 0.002 e/Bohr³ (稍小，表面更贴近分子)

**SAS (Solvent Accessible Surface)**:
- 探针半径默认 1.4 Å (水分子半径)
- 适合分析溶剂可及表面的 ESP 分布

### 子功能 1: 修改被映射的函数

默认映射 ESP，可改为:
- 1: 电子密度
- 2: 梯度范数
- 3: 约化密度梯度 (RDG)
- 4: sign(λ₂)ρ (用于 NCI 分析)
- 5: 自旋密度
- 6: ALIE (平均局部离子化能)
- 7: LOL (定域化轨道定位函数)
- 8: ELF (电子定域化函数)
- 15: ESP (默认)
- 16: vdW 势
- 20: 自定义函数

### 子功能 2: 搜索 vdW 表面上的 ESP 极值点

找出 ESP 局部最大/最小值:
- 局部最小值 → 负电位区域 → 可能的亲电进攻位点 (Lone pair, π 电子)
- 局部最大值 → 正电位区域 → 可能的亲核进攻位点 (σ-hole, 酸性氢)
- 输出: 每个极值点的坐标 (Å)、ESP 值 (kcal/mol 和 a.u.)

### 子功能 4: 计算分子表面积和体积

输出:
- 总表面积 (Å²)
- 不同 ESP 区间的表面积分布
- 可用于定量比较分子表面静电性质

### 子功能 5: 输出表面顶点坐标和 ESP 值

输出格式: x y z ESP_value (a.u.)
可用作后续 VMD 可视化的输入，也可导入 Python/Origin 做自定义绘图。

### 子功能 12: 绘制 ESP 在表面上的填色图

直接在 Multiwfn 内生成交互式 3D 图。

## 主功能 5: 计算并输出格点数据 (立方体文件)

适合需要在 VMD 中渲染等值面的情况:

`
Main function 5
→ 1: Output ESP at grid points
→ 选格点间距:
  1: Low quality (~0.35 Bohr)
  2: Medium-low quality (~0.25 Bohr)
  3: Medium quality (~0.20 Bohr)
  4: High quality (~0.10 Bohr)
`

**格点间距建议**:
- 快速预览: Low quality (1)
- 发表级图片: Medium (3) 或 High (4)
- 大分子 (>100 原子): Low 或 Medium-low

输出文件命名为 [输入文件名]_ESP.cub，可直接被 VMD/GaussView 读取。

## 主功能 13: 可视化分子表面静电势

等价于 VMD 的替代方案。在 Multiwfn 内直接生成填色分子表面图。适合在没有 VMD 时快速预览。

## 主功能 20: 电子密度拓扑分析

虽然不是直接的 ESP 分析，但可以配合 ESP 使用:
- 找键临界点 (BCP) 处的电子密度和 ESP
- 分析氢键强度与 ESP 的相关性

## VMD 渲染参数参考

### 推荐的材料和颜色方案

**Materials (material 命令)**:
- Opaque: 标准不透明
- Transparent: 半透明 (适合叠加显示)
- AOShiny: 环境光遮蔽 + 光泽 (发表级)
- Glass1/2/3: 玻璃效果 (适合教学展示)

**ESP 色标 (Color Scale Bar)**:
- 方案一 (RWB): 红(-) → 白(0) → 蓝(+)，最常用
- 方案二 (RGB): 红(-) → 绿(0) → 蓝(+)
- 方案三 (Jet): 蓝(-) → 青 → 绿 → 黄 → 红(+)，不建议用于发表

### VMD 完整 Tcl 脚本模板

将以下内容保存为 esp_viz.tcl，在 VMD Tk Console 中 source esp_viz.tcl 运行:

`	cl
# ESP 可视化脚本
# 用法: 修改下面的文件名后 source 此脚本

set basename "molecule"

# 清空当前场景
mol delete all

# 加载结构和 ESP cube
mol new .fchk type gaussian
mol addfile _ESP.cub type gaussian

# 删除默认线条表示
mol delrep 0 top

# 添加棒状模型 (可选)
mol representation Licorice 0.1 12 12
mol color Name
mol material Opaque
mol addrep top

# 添加 ESP 着色等值面
mol representation Isosurface 0.001 0 0 0 1 1
mol color Volume 0
mol material AOShiny
mol addrep top

# 设置色标范围 (根据实际分子调整)
mol scaleminmax top 0 -0.05 0.05

# 设置背景白色、坐标轴关闭
color Display Background white
axes location Off

# 调整视角
display resetview
rotate x by 30
rotate y by 45

# 渲染
# render TachyonInternal _esp.tga
`

### 常见问题排查

**Gaussian 报错: "No WFN file written"**:
- 检查 gjf 文件末尾是否有 .wfn 文件名
- 检查 route section 是否有 output=wfn

**Multiwfn 无法打开 .fchk**:
- 确保先用 ormchk 转换了 .chk → .fchk
- Gaussian 版本过旧可能生成不兼容的 .fchk，换用 .wfn

**VMD IsoSurface 不显示**:
- 检查 ESP 值范围是否正确 (Volume 数据集的 min/max)
- 适当调大 mol scaleminmax 范围
- 确认等值面值 (0.001) 对当前格点密度合适

**ESP 色标显示全白**:
- ESP 值的范围可能过窄，调小 mol scaleminmax 范围
- 或格点间距太大导致插值精度不足
