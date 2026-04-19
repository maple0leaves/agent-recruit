# resume-photo 模板完整语法参考

## 文档类与依赖

```latex
\documentclass{resume-photo}   % 使用项目内 resume-photo.cls
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif CJK SC}
\usepackage{fontspec}
\usepackage{enumitem}
\setlist[itemize]{itemsep=2pt, topsep=2pt}
```

## 页面几何（单页压缩设置）

```latex
\usepackage{geometry}
\geometry{top=0.55cm, bottom=0.45cm, left=0.85cm, right=0.85cm, includefoot}
\linespread{1.05}
\setlist[itemize]{itemsep=0pt, topsep=1pt, parsep=0pt, partopsep=0pt}
```

## 头部命令

| 命令 | 说明 |
|------|------|
| `\ResumeName{姓名}` | 设置姓名（显示在标题栏） |
| `\ResumePhoto{文件名}` | 照片文件（与 .tex 同目录），可选 |
| `\ResumeContacts{...}` | 联系信息，多项用 `,%` 分隔 |
| `\ResumeTitle` | 渲染头部，必须在 `\begin{document}` 内调用 |
| `\ResumeUrl{url}{文字}` | 带超链接文字 |

## 经历条目

```latex
\ResumeItem{主标题}[副标题（职位/性质）][右侧日期]
```

三个参数均可省略方括号部分：
- `\ResumeItem{标题}` — 仅标题
- `\ResumeItem{标题}[][日期]` — 标题 + 日期，无副标题

## itemize 样式

```latex
\begin{itemize}
  \item 普通文字
  \item \textbf{关键词}: 描述内容
\end{itemize}
```

bullet 符号由 cls 定义，无需手动指定。

## 特殊字符转义表

| 原字符 | LaTeX 写法 |
|--------|-----------|
| `%` | `\%` |
| `~` | `\textasciitilde` |
| `&` | `\&` |
| `_` | `\_` |
| `^` | `\^{}` 或 `\textasciicircum` |
| `#` | `\#` |
| `{` `}` | `\{` `\}` |
| `<` `>` | `$<$` `$>$` |

## 数字范围写法

```latex
% 推荐使用 en-dash
5\textasciitilde8pp    % 5~8pp（波浪号）
5--8pp                 % 5–8pp（en-dash）
```

## 分节命令

```latex
\section{教育背景}
\section{专业技能}
\section{科研经历}
\section{实习经历}
\section{项目经历}
\section{个人荣誉}
```

## 编译流程

```
xelatex → xelatex（两次，确保交叉引用正确）
输出：<filename>.pdf（与 .tex 同目录）
辅助文件：.aux .log .out（可忽略）
```
