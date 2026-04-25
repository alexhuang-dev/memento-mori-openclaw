<p align="center">
  <img src="assets/hero.svg" alt="Memento Mori：人生以周为单位" width="100%">
</p>

# Memento Mori：人生以周为单位

![版本](https://img.shields.io/badge/version-v0.3.1-2563eb)
![运行环境](https://img.shields.io/badge/python-3.10%2B-3776ab)
![技能](https://img.shields.io/badge/OpenClaw-skill-0f766e)
[![许可证](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

人不是一年一年老去的。
人是一周一周消失的。

Memento Mori 会把你的人生换算成一格一格的周，然后在每个星期天问你一句：

> 这一周，有什么值得留下？

它不是生产力工具，而是一种 AI 伴侣时代的个人仪式：本地优先、每周一句，把普通的星期从时间里捞出来。

## 破防瞬间

```text
你已经活了 11,363 天。

如果按 85 年计算，
你的人生大约有 4,435 周。

你已经用掉了 1,623 周。
还剩大约 2,812 周。

████████████░░░░░░░░░░░░░░░░░░░░ 37%

这不是倒计时。
这是提醒你：
有些星期，不该空白地过去。

这一周，你想留下什么？
```

## 分享卡片

<p align="center">
  <img src="assets/share-card-demo.svg" alt="人生周历分享卡片" width="720">
</p>

## 功能概览

| 方向 | 已实现能力 |
|---|---|
| 生命概览 | 已活天数、已活周数、剩余周数、进度条、估算终点日期 |
| 每周提醒 | 适合 OpenClaw cron 的 `checkin` 命令，里程碑提醒会去重 |
| 人格语气 | 支持 `stoic`、`gentle`、`sharp`、`poetic`、`minimal` |
| 周记 | 同时保存用户原文和一句忠实摘要 |
| 分享卡片 | `share` 命令输出适合截图的文本卡片，也可导出 SVG |
| 回顾 | 最近 N 周统计、空白周、连续记录、常见主题词、年度回顾数据 |
| 导出 | 支持 Markdown 和 JSON，可打印或写入文件 |
| 安全边界 | 用户表达自伤或强烈绝望时，不继续死亡倒计时叙事 |
| 隐私 | 脚本只读写本地 state 文件，不主动联网 |

## 架构

```mermaid
flowchart LR
    A["OpenClaw 消息 / cron"] --> B["SKILL.md 指令"]
    B --> C["scripts/life_stats.py"]
    C --> D["本地 state.json"]
    C --> E["概览 / check-in / 统计 / 回顾"]
    C --> F["Markdown 或 JSON 导出"]
```

## 仓库结构

```text
SKILL.md                    技能指令和元信息
scripts/life_stats.py       本地状态、计算和导出的确定性脚本
references/install.md       安装、定时提醒和本地配置说明
references/philosophy.md    语气、设计哲学和安全边界
tests/                      最小回归测试
```

## 快速开始

克隆到 OpenClaw skills 目录：

```powershell
git clone https://github.com/alexhuang-dev/memento-mori-openclaw.git "$env:USERPROFILE\.openclaw\workspace\skills\memento-mori"
```

让 OpenClaw 重新加载 skills：

```powershell
openclaw skills list
openclaw skills check
```

然后在 OpenClaw 对话中调用：

```text
使用 memento_mori，帮我初始化。我生日是 1995-03-15，预期寿命先按 85 岁。
```

## 手动脚本用法

在仓库根目录运行：

```bash
python scripts/life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
python scripts/life_stats.py read
python scripts/life_stats.py journal --entry "这一周有一件事值得留下。" --summary "留下了这一周的一件事。"
python scripts/life_stats.py share
python scripts/life_stats.py share --format svg --out card.svg
python scripts/life_stats.py config set --checkin-style sharp
python scripts/life_stats.py stats --last-n 12
python scripts/life_stats.py review --year 2026
python scripts/life_stats.py export --format markdown --out journal.md
```

默认 state 文件位置：

```text
~/.openclaw/skills/memento-mori/state.json
```

测试或自定义部署时可以改路径：

```bash
MEMENTO_MORI_STATE=/tmp/memento-mori-state.json python scripts/life_stats.py read
```

## 每周定时提醒

手动使用不需要 cron。只有想让它主动每周出现一次时，才需要配置 cron：

```bash
openclaw cron add \
  --name "memento-mori-weekly" \
  --cron "0 21 * * 0" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "使用 memento_mori 做每周提醒。运行 checkin，最多提一个新里程碑，然后问一个简短的本周反思问题。" \
  --announce \
  --channel last
```

## 安全与隐私

- 脚本只在本地运行，不主动发起网络请求。
- 周记可能包含非常私人的内容，不要提交 `state.json` 或导出的 journal 文件。
- 如果用户表达自伤、自杀、立即危险或强烈绝望，技能指令要求代理停止死亡倒计时叙事，改用危机场景下更安全的支持性回应。

## 开发

运行测试：

```bash
python -m unittest discover -s tests
```

快速烟测：

```bash
python scripts/life_stats.py setup --birthdate 1995-03-15 --life-expectancy-years 85
python scripts/life_stats.py checkin
```

## 定位

```text
不是生产力工具。
是一个记忆仪式。

不是看板。
是每周一次安静的敲门。

不是人生技巧。
是给那些差点消失的星期，一个小盒子。
```

## 许可证

MIT 许可证。见 [LICENSE](LICENSE)。
