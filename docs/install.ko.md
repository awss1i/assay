<!-- i18n-source: docs/install.md c51339dcc8b0355b209153fdf0186ea21a55095f -->

<h1 align="center">설치</h1>

<p align="center"><a href="../README.ko.md">assay</a> › 설치</p>

<p align="center"><a href="install.md">English</a> · <a href="install.zh-CN.md">简体中文</a> · <a href="install.ja.md">日本語</a> · <b>한국어</b> · <a href="install.ru.md">Русский</a></p>

<p align="center">assay를 설치하는 모든 방법입니다.</p>

---

## <a id="contents"></a>목차

- [pip](#pip)
- [uv](#uv)
- [pipx](#pipx)
- [Chromium](#chromium)
- [업데이트](#updating)
- [제거](#uninstalling)
- [코딩 에이전트](#coding-agents)

---

## <a id="pip"></a>pip

```bash
pip install assay-ui
```

assay에는 Python 3.10 이상이 필요합니다. 패키지 이름은 `assay-ui`이고, 설치되는 명령은 `assay`입니다. `pip` 명령을 찾을 수 없다면 `python3 -m pip install assay-ui`를 사용하세요.

---

## <a id="uv"></a>uv

```bash
uv tool install assay-ui
```

시스템에 3.10 이상의 Python이 없으면 uv가 assay용 Python을 내려받고, `assay` 명령을 `PATH`에 추가합니다.

---

## <a id="pipx"></a>pipx

```bash
pipx install assay-ui
```

pipx는 다른 Python 패키지와 분리된 별도의 격리된 환경에 assay를 설치합니다.

---

## <a id="chromium"></a>Chromium

assay는 Playwright를 통해 Chromium에서 페이지를 엽니다. 첫 실행 때 Chromium이 설치되어 있는지 확인하고, 없으면 내려받습니다. 내려받기를 시작하기 전에 assay는 다음 메시지를 출력합니다.

```
assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.
```

pip으로 설치했다면 컨테이너 이미지를 빌드할 때처럼 Chromium을 미리 내려받을 수 있습니다.

```bash
python -m playwright install chromium
```

Linux에서는 Chromium에 몇 가지 시스템 라이브러리가 필요합니다. 라이브러리가 없어서 첫 실행이 실패하면, 다음 명령이 그 라이브러리를 Chromium과 함께 설치합니다.

```bash
python -m playwright install --with-deps chromium
```

---

## <a id="updating"></a>업데이트

| 설치 방법 | 명령 |
|---|---|
| pip | `pip install --upgrade assay-ui` |
| uv | `uv tool upgrade assay-ui` |
| pipx | `pipx upgrade assay-ui` |

`assay --version`은 설치된 버전을 출력합니다.

---

## <a id="uninstalling"></a>제거

| 설치 방법 | 명령 |
|---|---|
| pip | `pip uninstall assay-ui` |
| uv | `uv tool uninstall assay-ui` |
| pipx | `pipx uninstall assay-ui` |

assay를 제거해도 Chromium은 Playwright의 캐시에 남습니다. pip으로 설치했다면 assay를 제거하기 전에 `python -m playwright uninstall`을 실행하세요. 그러면 Playwright가 내려받은 브라우저를 삭제합니다.

---

## <a id="coding-agents"></a>코딩 에이전트

skill과 플러그인(plugin)은 모두 `assay` 명령을 실행하므로, 먼저 위의 명령 중 하나로 assay를 설치하세요. 그다음 단계는 harness(에이전트 실행 환경)마다 다릅니다.

| Harness | 설치되는 것 |
|---|---|
| [Claude Code](harnesses.ko.md#claude-code) | 플러그인으로 설치하는 skill과 훅(hook) |
| [Codex](harnesses.ko.md#codex) | 플러그인으로 설치하는 skill과 훅(hook) |
| [Grok Build CLI](harnesses.ko.md#grok-build-cli) | 플러그인으로 설치하는 skill과 훅(hook) |
| [Cursor](harnesses.ko.md#cursor) | 플러그인으로 설치하는 skill |
| [DeepSeek Harness](harnesses.ko.md#deepseek-harness) | 파일을 복사해 설치하는 skill, 그리고 Claude Code 브리지를 통해 실행되는 훅 |
| [opencode](harnesses.ko.md#opencode) | 파일을 복사해 설치하는 skill |
| [Devin CLI](harnesses.ko.md#devin-cli) | 플러그인으로 설치하는 skill과 훅(hook) |
| [Factory Droid](harnesses.ko.md#factory-droid) | 플러그인으로 설치하는 skill과 훅(hook) |
| [GitHub Copilot CLI](harnesses.ko.md#github-copilot-cli) | 플러그인으로 설치하는 skill과 훅(hook) |
| [Antigravity, Gemini CLI, Kimi Code, Pi, Hermes Agent](harnesses.ko.md#everywhere-else-the-skill-on-its-own) | 파일을 복사해 설치하는 skill |

---

이 문서는 [install.md](install.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
