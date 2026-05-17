# OpenClaw Skills

Agent skills distilled from books and best practices.

## Skills

### book-distillation

将专业书籍蒸馏为可复用 Agent Skill 的系统化方法。

**六阶段 SOP**：
- 阶段0：整书理解，判断书籍类型
- 阶段1：并行提取（Agent数量=提取维度）
- 阶段2：三重验证筛选（淘汰率40-70%）
- 阶段3：Skill构造（触发条件+核心内容）
- 阶段4：关系链接（可选）
- 阶段5：压力测试（可选）

**书籍类型 → Agent数量**：
| 类型 | Agent数 | 提取维度 |
|------|---------|----------|
| 方法论导向 | 3-4 | 方法+工具+评估+局限 |
| 概念导向 | 2-3 | 概念+关系+应用 |
| 参考导向 | 1-2 | 查找表+常见问题 |
| 案例导向 | 2-3 | 模式+反模式+决策 |

**参考来源**：灵感来自 [kangarooking/cangjie-skill](https://github.com/kangarooking/cangjie-skill)

---

### protein-sss

蛋白质超二级结构（Supersecondary Structure）分析方法。

**核心方法**：
- ABEGO 构象分类
- Walker-A Motif 检测
- CAFS 非冗余数据集构建
- 突变效应预测
- 卷曲螺旋设计
- AlphaFold 局限与补充策略

**来源**：《Protein Supersecondary Structures: Methods and Protocols》第3版

---

### stock-technical-analysis

A股股票技术分析 + 基本面多源验证，短线交易建议。

**核心能力**：
- 腾讯API获取K线数据（东方财富被屏蔽）
- 8指标技术分析：均线/MACD/KDJ/RSI/布林带/WR/DMI/成交量
- 基本面多源交叉验证（至少3次搜索）
- 中文字体图表（FontProperties直接加载）
- T+0品种批量分析（可转债+跨境ETF）

**文件**：
| 文件 | 说明 |
|------|------|
| `tech_analysis_v3.py` | 单股技术分析脚本 |
| `t0_analysis.py` | T+0品种批量分析 |
| `002124_ta.png` | 天邦食品分析示例 |
| `t0_analysis.png` | T+0品种分析示例 |

---

### lottery-prediction

双色球历史数据分析 + Transformer预测模型。

**核心能力**：
- 历史数据抓取（2003-2025年，3296期）
- 特征工程：奇偶比、大小比、和值、跨度、AC值、遗漏值
- Transformer Encoder模型（2层，d_model=64，4头注意力）
- 训练/测试集按时间顺序分割

**重要声明**：彩票本质是随机事件，模型仅用于学习和娱乐。

**文件**：
| 文件 | 说明 |
|------|------|
| `train_final.py` | Transformer模型训练脚本 |
| `fetch_data.py` | 历史数据抓取脚本 |
| `README.md` | 项目详细报告 |

---

### comfyui-ltx-video

ComfyUI LTX 2.3 (Sulphur) 图生视频/文生视频工作流。

**核心能力**：
- Sulphur主模型(30GB) + Gemma3文本编码器(fp8, 9GB)
- 双LoRA链：sulphur_final(1.0) + distilled(0.5/0.7)
- T2V/I2V工作流
- 采样器：euler_ancestral_cfg_pp + ltxv_beta_dist

**关键配置**：
- LTX 2.3使用Gemma3 fp8(hidden=4096)，不是LTX 2.1的fp4_mixed(hidden=3840)
- ComfyUI必须v0.21.1+（旧版不支持hidden_size=4096）
- 下载模型需VPN代理(http://127.0.0.1:7892)

**文件**：
| 文件 | 说明 |
|------|------|
| `sulphur_test.json` | T2V工作流 |
| `sulphur_i2v_baby.json` | I2V工作流 |

---

## Usage

Skills 适用于各种 AI Agent 框架，包括 [OpenClaw](https://github.com/openclaw/openclaw)、[Hermes Agent](https://github.com/nousresearch/hermes-agent)、[Claude Code](https://docs.anthropic.com/en/docs/claude-code) 等。

每个 skill 文件夹包含：
- `SKILL.md` — 核心知识和流程（Agent 可直接读取）
- `scripts/` — 参考实现代码
- `references/` — 补充资料

### 直接使用

将 skill 文件夹复制到你的项目或 Agent 工作区：

```bash
# OpenClaw
cp -r stock-technical-analysis ~/.openclaw/workspace-YOUR_AGENT/skills/

# Hermes Agent
cp -r stock-technical-analysis ~/.hermes/skills/

# 任意项目
cp -r stock-technical-analysis ./your-project/skills/
```

### 作为知识库

Skill 也可直接阅读，无需 Agent 框架：
- `SKILL.md` 包含完整的方法论和步骤
- `scripts/` 包含可运行的代码
- 适合学习和参考

---

## License

MIT