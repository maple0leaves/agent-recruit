---
name: generate-resume
description: Generates Chinese technical PDF resumes using the project's resume-photo LaTeX template. Handles content filling, xelatex compilation, and single-page layout. Use when user mentions generating, writing, or updating a resume, exporting PDF, or working with the LaTeX resume template.
---

# 技术简历生成（resume-photo 模板）

模板位置：`resume/resume-photo.tex`（可直接修改此文件）  
样式类：`resume/resume-photo.cls`（不需修改）  
编译方式：xelatex（已安装于系统）

## 快速流程

根据场景选择模式：

**模式 A — 用户提供真实信息**
1. 按"信息清单"收集用户信息
2. 修改 `resume/resume-photo.tex`，填入用户提供的内容
3. 运行 `bash .cursor/skills/generate-resume/scripts/compile.sh` 生成 PDF

**模式 B — AI 自主生成测试简历**（用于测试招聘系统、演示用途）
1. 自主设计一位虚构但真实感强的技术候选人（姓名、背景、技能方向自行决定）
2. 内容要求：数据量化、技术栈具体、经历连贯，符合真实求职简历风格
3. **新建文件** `resume/<候选人姓名拼音>.tex`，复制模板头部结构，填入自定义内容
   - **禁止修改** `resume/resume-photo.tex`（原始模板，只作参考）
4. 运行 `cd resume && xelatex -interaction=nonstopmode <新文件名>.tex`，输出同名 PDF

---

## 信息清单

修改简历前，确认已获取以下内容：

- **姓名**：`\ResumeName{}`
- **照片文件名**（可选）：`\ResumePhoto{}`，文件放在 `resume/` 目录下
- **联系方式**：手机、邮箱、学校/单位（逗号分隔）
- **个人简介**：3～5 句话，放在 `\ResumeTitle` 之后 `\noindent` 段落
- **教育背景**：学校、院系、学历、GPA/排名、年限（每条用 `\ResumeItem`）
- **专业技能**：分条列举，放在 `itemize` 环境中
- **实习经历**：标题、子标题（职位）、日期、详细 bullet 点
- **项目经历**：标题、子标题（性质）、日期、详细 bullet 点
- **科研经历**（可选）：默认不包含；用户明确提到有论文/课题时才添加
- **个人荣誉**：分条列举

---

## 核心命令速查

```latex
% 头部
\ResumeName{姓名}
\ResumePhoto{photo.jpg}           % 可选，不填则无照片
\ResumeContacts{
  手机号,%
  \ResumeUrl{mailto:you@email.com}{you@email.com},%
  \textnormal{单位 | 专业 · 学历 | 年份}%
}
\ResumeTitle                      % 渲染头部，必须在 \begin{document} 内

% 经历条目（科研 / 实习 / 项目通用）
\ResumeItem{标题}[子标题（可选）][日期（可选）]
\begin{itemize}
  \item \textbf{关键词}: 具体描述，包含量化数据
\end{itemize}

% 带链接的文字
\ResumeUrl{https://...}{显示文字}

% 特殊字符转义
% 百分号：\%    波浪号：\textasciitilde    竖线：|（直接用即可）
```

---

## 排版约束

- **单页压缩**：`\geometry{top=0.55cm, bottom=0.45cm, left=0.85cm, right=0.85cm}` 已在模板中设置
- **字体**：`Noto Serif CJK SC`（中文）+ 系统默认无衬线英文
- **行距**：`\linespread{1.05}`，条目间距 `itemsep=0pt`
- **内容超出单页**：优先压缩个人简介或荣誉列表，或减少项目 bullet 点数量
- **照片**：放在 `resume/` 目录下，建议方形 JPG，100×100px 以上

---

## 默认 section 顺序

```
教育背景 → 专业技能 → 实习经历 → 项目经历 → 个人荣誉
```

**科研经历** 默认省略。仅当用户满足以下任一条件时才插入（位置在"专业技能"之后，"实习经历"之前）：
- 有发表/在投的论文
- 有明确的导师课题/研究项目
- 用户主动要求添加

---

## 各 section 写作要点

### 专业技能
- 每条以"熟悉 / 掌握 / 了解"开头
- 覆盖：编程语言 → 框架 → 训练技术 → 推理/部署 → 工程工具

### 科研 / 实习 / 项目经历
- 第一 bullet：问题背景或职责范围
- 中间 bullet：具体技术方案 + **量化指标**（提升 X%、减少 Xs）
- 最后 bullet：**成果**（论文/开源/落地）

### 个人简介
- 控制在 2～4 行（约 150 字以内）
- 句式：身份 → 技术方向 → 核心成果 → 实习/竞赛亮点

---

## 编译

在仓库 **`hellojobs/` 根目录** 下执行（与 `.cursor/` 同级）：

```bash
bash .cursor/skills/generate-resume/scripts/compile.sh
```

可选：指定 `.tex` 文件路径作为参数，例如  
`bash .cursor/skills/generate-resume/scripts/compile.sh resume/zhang-haoran.tex`

编译成功后输出 `resume/resume-photo.pdf`（默认）或与输入同名的 PDF。  
如果编译失败，检查：
1. 字体是否安装：`fc-list | grep "Noto Serif CJK"`
2. 特殊字符是否已转义（`%` → `\%`）
3. 查看日志：`resume/resume-photo.log`

---

## 额外资源

- 模板语法完整参考：[reference.md](reference.md)
