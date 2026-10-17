<!-- i18n-source: docs/harnesses.md 754a27f7ad6e3db62fad6db5ec61f13ed63618f1 -->

<h1 align="center">harness에 assay 설치하기</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <a href="harnesses.ja.md">日本語</a> · <b>한국어</b> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">harness(에이전트 실행 환경) 15개의 설치 방법입니다. 그중 8개는 자체 플러그인 명령으로
assay를 설치합니다. 나머지 7개는 skill 파일을 알맞은 위치에 복사하면 되며, 이 방법은 skill을
읽는 harness라면 어디서든 동작합니다.</p>

---

## <a id="contents"></a>목차

- [제공되는 기능](#what-you-get)
- [Claude Code](#claude-code)
- [Codex](#codex)
- [Grok Build CLI](#grok-build-cli)
- [Cursor](#cursor)
- [DeepSeek Harness](#deepseek-harness)
- [opencode](#opencode)
- [Devin CLI](#devin-cli)
- [Factory Droid](#factory-droid)
- [GitHub Copilot CLI](#github-copilot-cli)
- [그 밖의 harness에서 skill만 사용하기](#everywhere-else-the-skill-on-its-own)

---

## <a id="what-you-get"></a>제공되는 기능

assay는 두 부분으로 구성됩니다.

- 에이전트가 페이지를 완성한 뒤 `assay`를 실행하고 그 결과를 보여 주도록 지시하는 **skill**
- 검사(check)를 자동으로 실행하는 **훅(hook)**

플러그인(plugin)으로 설치하면 두 가지를 모두 얻습니다. 단, Cursor에서는 skill만 얻습니다. Claude Code, Codex, Grok Build CLI, Devin CLI, Factory Droid, GitHub Copilot CLI, DeepSeek Harness에서는 페이지를 변경한 턴(turn)이 끝날 때마다 훅이 검사를 실행합니다. DeepSeek Harness에서는 skill을 파일로 복사해 설치하고, 훅은 Claude Code 브리지를 통해 실행합니다. opencode와 [그 밖의 harness](#everywhere-else-the-skill-on-its-own)에 속한 harness는 skill만 설치하며, 이들 harness에서는 skill의 지시에 따라 에이전트가 직접 검사를 실행합니다.

harness 15개 모두 먼저 `assay`가 `PATH`에 있어야 합니다.

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # Python 3.10+가 없으면 uv가 내려받습니다
```

```bash
pipx install assay-ui          # assay를 별도의 격리된 환경에 설치합니다
```

---

## <a id="claude-code"></a>Claude Code

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

---

## <a id="codex"></a>Codex

Codex CLI에서 마켓플레이스를 추가하고 플러그인을 설치하세요.

```bash
codex plugin marketplace add awss1i/assay
codex plugin add assay@assay
```

그런 다음 새 세션을 시작하고 `/hooks`를 열어 assay 훅을 신뢰하도록 설정하세요. Codex는 사용자가 신뢰하기 전까지 플러그인의 훅을 건너뛰므로, 이 단계를 거치지 않으면 skill만 사용하게 됩니다. 업데이트는 `codex plugin marketplace upgrade assay`로 하세요.

Codex App(ChatGPT 데스크톱 앱 안의 Codex)에서는 위의 `codex plugin marketplace add` 명령을 실행하고 앱을 다시 시작한 다음, Plugins 메뉴의 assay 마켓플레이스에서 assay를 설치하세요.

---

## <a id="grok-build-cli"></a>Grok Build CLI

```bash
grok plugin marketplace add awss1i/assay
grok plugin install assay --trust
```

`--trust`가 없으면 Grok은 훅이 있는 플러그인을 설치하지 않습니다. 설치를 멈추고 `--trust`를 붙여 명령을 다시 실행하라고 안내합니다. 설치가 제대로 되었다면 `grok inspect`가 `checking-a-page` skill과 훅을 목록에 보여 줍니다. 업데이트는 `grok plugin marketplace update`를 실행한 다음 `grok plugin update assay`를 실행하세요.

---

## <a id="cursor"></a>Cursor

편집기에서는 Cursor 2.5부터 Agent 채팅에 다음을 입력하세요.

```
/add-plugin assay@https://github.com/awss1i/assay
```

Cursor CLI에서는 마켓플레이스를 추가한 다음, 세션 안에서 `/plugin`으로 assay를 설치하세요.

```bash
agent plugin marketplace add https://github.com/awss1i/assay
```

어느 방법이든 skill이 설치됩니다. Cursor의 훅은 형식이 다르기 때문에, Cursor에서는 플러그인이 훅을 추가하지 않습니다. 플러그인 대신 skill만 설치하려면 skills CLI를 사용하세요.

```bash
npx skills add awss1i/assay --agent cursor       # 이 프로젝트에만, .agents/skills/에 설치
npx skills add awss1i/assay --agent cursor -g    # 모든 프로젝트에, ~/.agents/skills/에 설치
```

---

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh는 프로젝트의 `.agents/skills/`와 모든 프로젝트에 적용되는 `~/.agents/skills/`에서 skill을 읽지만, `.claude/skills/`에서는 읽지 않습니다. 둘 중 한 곳에 skill을 복사하세요.

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

dsh의 기본 권한 모드는 명령이 프로젝트 밖에 파일을 쓰지 못하게 막습니다. 첫 검사는 Chromium을 홈 폴더에 내려받으므로, dsh가 이를 한 번 승인해 달라고 요청할 수 있습니다. 이 요청을 피하려면 첫 검사를 dsh가 아닌 일반 셸에서 실행하세요.

훅의 경우, dsh는 함께 제공되는 브리지를 통해 Claude Code 훅 설정을 실행합니다. 이 브리지를 포함한 프로필은 없으므로 `$DSH_HOME/cordis.patch.yml`에 추가하세요. 이 파일은 모든 프로필의 자체 레이어 다음에 적용되므로 `web`, `headless`, 그리고 직접 만든 모든 프로필에 적용됩니다.

```yaml
- insert:
    - id: hooks-claude-code
      name: '@deepseek-ai/dsh-hooks-claude-code'
      config:
        configPath: /abs/path/to/assay/plugins/assay/hooks/hooks.json
        pluginRoot: /abs/path/to/assay/plugins/assay
```

`$DSH_HOME`은 따로 설정하지 않으면 `~/.dsh`입니다. 훅은 자체 작업 디렉터리에서 실행되므로 두 경로 모두 절대 경로로 지정합니다. `dsh --dump-config`는 합쳐진 설정 트리를 출력하므로, 이 명령으로 브리지가 마운트되었는지 확인할 수 있습니다.

한 프로필에만 적용하려면 같은 블록을 대신 그 프로필의 `cordis.patch.yml`에 넣거나, 실행할 때마다 `--patch`로 전달하세요.

---

## <a id="opencode"></a>opencode

```bash
mkdir -p .agents/skills
cp -r plugins/assay/skills/checking-a-page .agents/skills/
```

opencode는 `.agents/skills/`, `.opencode/skills/`, `.claude/skills/`, `~/.config/opencode/skills/`를 읽습니다. `.agents/skills/`를 사용하는 것이 좋습니다. DeepSeek Harness, Cursor, Hermes Agent도 이 폴더를 읽으므로 폴더 하나로 네 도구에서 모두 쓸 수 있습니다.

---

## <a id="devin-cli"></a>Devin CLI

Devin은 로그인한 상태에서만 플러그인을 관리하므로, 먼저 `devin auth login`을 실행하세요.

```bash
devin plugins install awss1i/assay#plugins/assay
```

플러그인은 `plugins/assay`에 있으며, `#` 기호는 Devin에게 그 위치를 찾아보라고 알려 주는 표기입니다. Devin Cloud 매니페스트 대신 이 머신에만 설치하려면 `--local`을 추가하세요. 업데이트는 `devin plugins update assay`로 하세요. Devin은 플러그인 훅을 실행하려고 시도하지만 실행을 보장하지는 않으며, 훅이 실패해도 턴은 멈추지 않습니다.

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

대화형 Droid에서는 신뢰한 폴더에서만 훅이 실행됩니다.

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

Copilot은 훅의 보고를 에이전트에게 전달하지 않고 화면에 직접 보여 줍니다. 보고는 터미널에서 에이전트에게 보내는 줄 아래에 나타나며, 에이전트는 그 보고를 다시 말하지 않습니다.

---

## <a id="everywhere-else-the-skill-on-its-own"></a>그 밖의 harness에서 skill만 사용하기

*Antigravity, Gemini CLI, Kimi Code, Pi, Hermes Agent.*

assay는 이 harness들의 형식에 맞는 플러그인을 제공하지 않으므로, skill을 파일로 설치합니다. skill은 마크다운 파일 하나이며, skill이나 지침 파일을 읽는 곳이라면 어디서든 동작합니다.

[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page)를 harness가 skill을 읽는 폴더에 복사하세요. 예를 들어 Hermes Agent는 프로젝트의 `.agents/skills/`를 읽습니다. 또는 파일 내용을 `AGENTS.md`에 붙여 넣으세요.

훅이 없으면 매 턴이 끝날 때마다 검사가 실행되는 대신, 에이전트가 검사를 언제 실행할지 결정합니다.

**[skill의 동작 방식 →](../plugins/assay/README.ko.md#the-skill)**

---

이 문서는 [harnesses.md](harnesses.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
