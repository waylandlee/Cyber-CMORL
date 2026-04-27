# Visio 重画清单：Overview of DA-CPSL

源图：`paper/images/Overview of DA-CPSL.png`

建议在 Visio 中分层绘制：

1. 背景容器层
2. 模块面板与卡片层
3. 流程箭头与连接线层
4. 图标与小型图表层
5. 文字与公式层

## 全局布局

### 画布

- 画布比例：宽屏横向，约为 16:9。
- 顶部居中主标题：
  - `Overview of DA-CPSL for Constrained Multi-Objective Autonomous Cyber Defense`

### 上半部分：Learning / Archive Construction

- 使用一个蓝色边框的大型圆角矩形作为外层容器。
- 左侧放置竖向标签条：
  - 旋转文字：`Learning`
- 左上角章节标题：
  - `Learning / Archive Construction`
- 内部包含四个主要模块：
  - 模块 A：Partially Observable Cyber Range
  - Four-objective reward signals 卡片
  - 模块 B：Stage 1 Preference-Diverse Initialization
  - 模块 C：Candidate Evaluation and Semantic Audit
  - 模块 D：Stage 2 Acceptance-Aware Pareto Extension

### 下半部分：Deployment / Operational Assignment

- 使用一个绿色边框的大型圆角矩形作为外层容器。
- 左侧放置竖向标签条：
  - 旋转文字：`Deployment`
- 左上角章节标题：
  - `Deployment / Operational Assignment`
- 内部包含：
  - Deployment Inputs 面板
  - Constrained Operational Assignment 面板
  - Deployable Blue-Defense Policy 输出框
  - Infeasible Assignment 输出框

## 模块 A：Partially Observable Cyber Range

### 主面板

- 蓝色边框圆角矩形。
- 左上角蓝色圆形编号徽章：
  - `A`
- 主标题：
  - `Partially Observable`
  - `Cyber Range`
- 副标题：
  - `CybORG++ Scenario 2`

### Cyber Range 示意图

图标与元素：

- 左侧红色攻击者图标：
  - 戴帽/人物剪影加笔记本电脑。
  - 下方文字：
    - `Red`
    - `attacker`
- 右侧蓝色防御者图标：
  - 人物剪影加头盔/耳机和笔记本电脑。
  - 下方文字：
    - `Blue`
    - `defender`
- 上方居中云朵图标。
- 中央圆形网络/路由器图标。
- 中央路由器下方三个服务器图标。
- 底部三个橙色数据库/资产图标。
- 资产下方文字：
  - `Critical assets`

连接线：

- 从红色攻击者指向中心的水平虚线。
- 从中心指向蓝色防御者的水平虚线。
- 中心附近使用小箭头表示双向交互。
- 从云朵到中央路由器的垂直连接线。
- 从中央路由器到服务器的斜向/垂直连接线。
- 从服务器到对应资产图标的连接线。

### Observation / Action / Trajectory 文字块

- 模块 A 底部附近放置一条水平分隔线。
- 文字块：
  - `observation o_t`
  - `defense action a_t`
  - `trajectory tau`

## Four-Objective Reward Signals 卡片

### 卡片

- 位于模块 A 和模块 B 之间的窄圆角矩形。
- 使用黑色或灰色边框。
- 顶部文字：
  - `Four-objective`
  - `reward signals`
- 公式：
  - `r_t = [r_t^sec, r_t^bus, r_t^cost, r_t^crit]`

### 四个目标框

四个纵向堆叠的圆角矩形：

- 蓝色/security 框：
  - 盾牌图标。
  - 文字：
    - `Security`
    - `Effectiveness`
- 绿色/business 框：
  - 柱状图/上升趋势图标。
  - 文字：
    - `Business`
    - `Continuity`
- 紫色/cost 框：
  - 美元图标。
  - 文字：
    - `Defense`
    - `Cost`
- 橙色/safety 框：
  - 盾牌/感叹号图标。
  - 文字：
    - `Critical-Asset`
    - `Safety`

### 连接箭头

- 从模块 A 指向该奖励卡片的粗黑色右箭头。
- 从奖励卡片指向模块 B 的粗黑色右箭头。

## 模块 B：Stage 1 Preference-Diverse Initialization

### 主面板

- 蓝色边框圆角矩形。
- 左上角蓝色圆形编号徽章：
  - `B`
- 标题：
  - `Stage 1: Preference-Diverse`
  - `Initialization`

### 三个流程行

第 1 行：

- 浅蓝色边框圆角矩形。
- 左侧为多人/群组图标。
- 文字：
  - `Sample initial preferences w in Delta^4`

第 2 行：

- 浅蓝色边框圆角矩形。
- 左侧为大脑图标。
- 文字：
  - `Train initial defense policies`

第 3 行：

- 浅蓝色边框圆角矩形。
- 左侧为数据库图标。
- 文字：
  - `Initial evaluated archive Pi_init`

### Policy Cards

- 三个可见的小卡片，右侧再加省略号。
- 每个卡片包含：
  - 策略标签：
    - `pi_1`
    - `pi_2`
    - `pi_3`
  - 卡片内部的小型多色柱状图。
- 右侧省略号：
  - `...`

### 图注

- 底部蓝色斜体说明文字：
  - `Diverse starting policies for`
  - `Pareto exploration`

### 连接箭头

- 从奖励卡片进入模块 B 的粗黑色右箭头。
- 从模块 B 进入模块 C 的粗黑色右箭头。

## 模块 C：Candidate Evaluation and Semantic Audit

### 主面板

- 蓝色边框圆角矩形。
- 左上角蓝色圆形编号徽章：
  - `C`
- 标题：
  - `Candidate Evaluation`
  - `and Semantic Audit`

### 公式框

- 位于面板上方附近的蓝色边框圆角矩形。
- 公式：
  - `x(pi) = (pi, J_hat(pi), g_hat(pi), psi_hat(pi))`

### 三个评估卡片

Objective Returns 卡片：

- 蓝色边框圆角矩形。
- 标题：
  - `Objective`
  - `returns J_hat(pi)`
- 内部为若干彩色柱组成的小型柱状图。
- 省略号：
  - `...`

Operational Violations 卡片：

- 绿色边框圆角矩形。
- 标题：
  - `Operational`
  - `violations g_hat(pi)`
- 三个横向指标行：
  - `g_1(pi)`
  - `g_2(pi)`
  - `...`
  - `g_M(pi)`
- 每行右侧使用绿色/橙色横向条表示约束违背程度。

Critical-Risk Audit 卡片：

- 橙红色边框圆角矩形。
- 标题：
  - `Critical-risk`
  - `audit psi_hat(pi)`
- 四个复选框行：
  - `ever critical breach`
  - `persistent breach`
  - `first critical hit`
  - `critical dwell`

### 图注

- 底部蓝色斜体说明文字：
  - `Each candidate is evaluated by performance,`
  - `constraint violations, and replay-level`
  - `semantic audit.`

### 连接箭头

- 从模块 B 进入模块 C 的粗黑色右箭头。
- 从模块 C 进入模块 D 的粗黑色右箭头。

## 模块 D：Stage 2 Acceptance-Aware Pareto Extension

### 主面板

- 大型蓝色边框圆角矩形。
- 左上角蓝色圆形编号徽章：
  - `D`
- 标题：
  - `Stage 2: Acceptance-Aware`
  - `Pareto Extension`

### Archive Views 框

- 位于模块 D 左上侧的蓝色边框圆角矩形。
- 标题：
  - `Archive views:`
- 文字：
  - `Pi, Pi_p, Pi_p^acc`

### Parent Selection 框

- 位于模块 D 右上侧的蓝色边框圆角矩形。
- 标题：
  - `Parent selection`
- 项目文字：
  - `sparse region`
  - `low violation`
  - `low critical risk`

### Scatter / Pareto Plot

- 坐标轴：
  - 纵轴标签：`J_2`
  - 横轴标签：`J_1`
- 灰色散点：
  - 原始 archive 中的所有候选点。
- 蓝色散点及蓝色折线/曲线：
  - Pareto policies。
- 绿色散点：
  - Acceptable Pareto policies。
- 红色叉号：
  - Rejected policies。

图例位于散点图下方：

- 灰色圆点：
  - `Raw archive (all evaluated)`
- 蓝色圆点：
  - `Pareto policies (Pi_p)`
- 绿色圆点：
  - `Acceptable Pareto policies (Pi_p^acc)`
- 红色叉号：
  - `Rejected policies (violations / high risk)`

### Constrained Extension 框

- 位于右侧中部的蓝色边框圆角矩形。
- 标题：
  - `Constrained`
  - `extension`
- 文字：
  - `maximize one objective`
  - `preserve others`
  - `subject to g_m(pi) <= delta_m`

### Evaluate Child 框

- 位于右下侧的蓝色边框圆角矩形。
- 文字：
  - `Evaluate child`
  - `+ archive update`

### 图注

- 底部蓝色斜体说明文字：
  - `Expand toward useful and acceptable`
  - `operating points`

### 内部连接箭头

- 从 Archive views 框指向 Parent selection 框的箭头。
- 从 Parent selection 框向下指向 Constrained Extension 框的箭头。
- 从 Constrained Extension 框向下/弯曲指向 Evaluate Child 框的箭头。
- 从 Evaluate Child 区域回到 archive/plot 区域的弯曲反馈箭头。
- 散点图左侧附近放置一个弯曲箭头，表示迭代扩展过程。

### 外部连接箭头

- 从模块 D 向下连接到底部 Deployment 区域的粗黑色连接线。
- 连接线附近标注：
  - `Evaluated`
  - `policy archive`

## Deployment Inputs 面板

### 主面板

- 绿色边框圆角矩形。
- 标题：
  - `Deployment Inputs`

### 输入行

第 1 行：

- 绿色边框圆角矩形。
- 操作员/人物图标。
- 文字：
  - `Operator preference w in Delta^4`

第 2 行：

- 绿色边框圆角矩形。
- 滑杆/调参图标。
- 文字：
  - `Hard operational limits delta`

### 连接箭头

- 从 Deployment Inputs 面板指向 Constrained Operational Assignment 面板的粗黑色右箭头。

## Constrained Operational Assignment 面板

### 主面板

- 位于底部中央的大型绿色边框圆角矩形。
- 标题：
  - `Constrained Operational Assignment`

### 步骤 1：Acceptable Pareto Set

- 绿色圆形步骤徽章：
  - `1`
- 绿色边框圆角矩形。
- 内部放置类似模块 D 散点图的迷你 scatter/Pareto 图标。
- 文字：
  - `Acceptable Pareto set`
  - `Pi_p^acc(Pi, delta)`

### 步骤 2：Utility-Based Selection

- 绿色圆形步骤徽章：
  - `2`
- 绿色边框圆角矩形。
- 天平图标。
- 文字：
  - `Utility-based`
  - `selection`

### 步骤 3：Optimization Rule

- 绿色圆形步骤徽章：
  - `3`
- 绿色边框圆角矩形。
- 公式：
  - `pi*(w, delta) =`
  - `argmax_{pi in Pi_p^acc} w^T J_tilde(pi)`

### 底部条件文字

- 位于步骤框下方居中：
  - `If Pi_p^acc = empty set, return infeasible.`

### 内部连接箭头

- 从步骤 1 指向步骤 2 的粗黑色右箭头。
- 从步骤 2 指向步骤 3 的粗黑色右箭头。

### 外部连接箭头

- 从 Deployment Inputs 面板进入步骤 1 的粗黑色箭头。
- 从步骤 3 分叉到右侧两个输出框的粗黑色括号/分支连接线。

## 输出：Deployable Blue-Defense Policy

### 输出框

- 青绿/绿色边框圆角矩形。
- 标题：
  - `Deployable Blue-Defense Policy`
- 左侧盾牌/勾选图标。
- 文字：
  - `selected policy pi*`

### 连接箭头

- 从 Constrained Operational Assignment 面板出来的上方分支连接到该输出框。

## 输出：Infeasible Assignment

### 输出框

- 红色/橙色边框圆角矩形。
- 标题：
  - `Infeasible Assignment`
- 左侧警告三角形图标。
- 文字：
  - `no policy satisfies`
  - `hard limits`

### 连接箭头

- 从 Constrained Operational Assignment 面板出来的下方分支连接到该输出框。

## 视觉风格说明

### 颜色

- Learning 区域：
  - 主要使用蓝色边框和标题。
  - 模块 A-D 使用蓝色圆形徽章。
- Deployment 区域：
  - 主要使用绿色边框和标题。
  - 步骤 1-3 使用绿色圆形徽章。
- 风险/不可行相关元素：
  - 使用红色或橙色边框与警告强调色。
- 四个目标颜色：
  - Security：蓝色。
  - Business：绿色。
  - Cost：紫色。
  - Critical-asset safety：橙色。

### 形状风格

- 大多数容器使用圆角矩形。
- 边框为细到中等粗细。
- 主流程箭头为粗黑色。
- 内部箭头为较细黑色。
- 正文文字以深蓝或黑色为主；图注为蓝色斜体。

### 推荐的 Visio 重画顺序

1. 先画两个大型外层容器和左侧竖向章节标签。
2. 放置 A-D 主模块，以及底部 Deployment 区域的几个主面板。
3. 添加所有模块之间的粗黑色主流程箭头。
4. 添加内部小卡片、流程行和目标框。
5. 用可编辑的 Visio 形状或 SVG 图标重建图标、mini chart 和图例。
6. 最后添加文字和公式，便于整体对齐和微调。

