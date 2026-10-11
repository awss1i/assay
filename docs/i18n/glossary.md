<h1 align="center">Glossary</h1>

---

<p align="center">The word each translation uses for assay's terms, so every page in a language
says the same thing the same way. <a href="rules.md">rules.md</a> covers everything else.</p>

---

## Contents

- [assay's Terms](#assays-terms)
- [Coding Agents](#coding-agents)
- [General Terms](#general-terms)
- [Never Translated](#never-translated)

---

## assay's Terms

| English | 简体中文 | 日本語 | 한국어 | Русский | Meaning |
|---|---|---|---|---|---|
| check | 检查 | チェック | 검사 | проверка | one planned action on the page, like C003 |
| finding | 问题 | 指摘 | 발견 사항 | замечание | something assay reports |
| false alarm | 误报 | 誤検知 | 오탐 | ложное срабатывание | a working page flagged as broken |
| miss | 漏报 | 見逃し | 미탐 | пропуск | a real bug assay didn't flag |
| control | 控件 | コントロール | 컨트롤 | элемент управления | anything on a page that can be used |
| rule | 规则 | ルール | 규칙 | правило | what decides whether a check failed |
| the page contradicts itself | 页面自相矛盾 | ページが自己矛盾している | 페이지가 스스로 모순된다 | страница противоречит сама себе | what every finding describes |
| deterministic | 结果确定 | 決定論的 | 결정론적 | детерминированный | the same result on every run |
| agent-native | 智能体原生 | エージェントネイティブ | 에이전트 네이티브 | созданный для агентов | built to run inside a coding agent |
| benchmark | 基准测试 | ベンチマーク | 벤치마크 | бенчмарк | |
| planted bug | 人为植入的 bug | 意図的に仕込んだバグ | 의도적으로 심은 버그 | внедрённый баг | a bug added on purpose for scoring |
| answer key | 标准答案 | 正解リスト | 정답표 | эталон | the hand-written verdicts a benchmark is scored against |
| report | 报告 | レポート | 보고서 | отчёт | the page `--report` writes |
| passed / failed / not checked | 通过 / 失败 / 未检查 | 成功 / 失敗 / 未チェック | 통과 / 실패 / 검사하지 못함 | пройдена / не пройдена / не проверена | a check's outcome, keep the English when quoting assay's output |
| evidence | 证据 | 証拠 | 근거 | свидетельства | what a check records about the page |
| flagged | 标记为有问题 | 問題ありと判定する | 문제로 표시하다 | помечена как проблемная | reported as a finding |

---

## Coding Agents

| English | 简体中文 | 日本語 | 한국어 | Русский | Note |
|---|---|---|---|---|---|
| agent | 智能体 | エージェント | 에이전트 | агент | |
| coding agent | 编程智能体 | コーディングエージェント | 코딩 에이전트 | агент для программирования | |
| harness | harness | harness | harness | harness | keep English, and gloss the first use as 智能体运行框架, エージェントの実行環境, 에이전트 실행 환경, среда запуска агента |
| skill | skill | skill | skill | skill | the feature name in the harnesses, keep English |
| plugin | 插件 | プラグイン | 플러그인 | плагин | |
| hook | 钩子 | フック | 훅 | хук | |
| turn | 一轮 | ターン | 턴 | ход | one exchange with the agent |

---

## General Terms

| English | 简体中文 | 日本語 | 한국어 | Русский |
|---|---|---|---|---|
| bug | bug | バグ | 버그 | баг |
| web page | 网页 | Web ページ | 웹 페이지 | веб-страница |
| page | 页面 | ページ | 페이지 | страница |
| browser | 浏览器 | ブラウザー | 브라우저 | браузер |
| command line | 命令行 | コマンドライン | 명령줄 | командная строка |
| repository | 仓库 | リポジトリ | 저장소 | репозиторий |
| pull request | pull request | プルリクエスト | 풀 리퀘스트 | пулреквест |
| issue | issue | Issue | 이슈 | ишью |
| test | 测试 | テスト | 테스트 | тест |
| install | 安装 | インストール | 설치 | установка |
| screenshot | 截图 | スクリーンショット | 스크린샷 | скриншот |
| canvas | 画布 | キャンバス | 캔버스 | холст |
| field | 输入框 | 入力欄 | 입력란 | поле ввода |
| form | 表单 | フォーム | 양식 | форма |
| dropdown | 下拉框 | ドロップダウン | 드롭다운 | выпадающий список |
| checkbox | 复选框 | チェックボックス | 체크박스 | чекбокс |
| slider | 滑块 | スライダー | 슬라이더 | слайдер |
| tab | 标签页 | タブ | 탭 | вкладка |
| acceptance criteria | 验收标准 | 受け入れ基準 | 인수 기준 | критерии приёмки |
| serve (a folder on localhost) | 托管 | 配信する | 서빙하다 | раздавать |
| throw an error | 抛出错误 | エラーを投げる | 오류가 발생하다 | выбрасывать ошибку |
| exit code | 退出码 | 終了コード | 종료 코드 | код завершения |
| placeholder | 占位符 | プレースホルダー | 플레이스홀더 | плейсхолдер |
| label (HTML `<label>`) | label | ラベル | 레이블 | метка |
| chip | 标签 | チップ | 칩 | чип |
| scratch folder | 临时文件夹 | 一時フォルダー | 임시 폴더 | временная папка |

---

## Never Translated

These stay exactly as written in every language:

- assay, Playwright, Chromium, Python, PyPI, pip, uv, pipx, GitHub, Discussions, MIT
- the harness names: Claude Code, DeepSeek Harness, opencode, Antigravity, Codex App, Codex CLI,
  Cursor, Devin CLI, Factory Droid, Gemini CLI, GitHub Copilot CLI, Grok Build CLI, Kimi Code, Pi
  and Hermes Agent
- CLI, DOM, LLM, QA, HTML, JSON, API, UI, NaN
