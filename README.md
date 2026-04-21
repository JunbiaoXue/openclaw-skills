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

---

## Usage

Skills are designed for [OpenClaw](https://github.com/openclaw/openclaw) agents.

Copy skill folder to your workspace:
```bash
cp -r book-distillation ~/.openclaw/workspace-YOUR_AGENT/skills/
```

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

## License

MIT