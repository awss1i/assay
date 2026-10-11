<!-- i18n-source: docs/harnesses.md 35ce1703961c0b049eb853466b5b884081a86ff7 -->

<h1 align="center">harness에 assay 설치하기</h1>

<p align="center"><a href="harnesses.md">English</a> · <a href="harnesses.zh-CN.md">简体中文</a> · <a href="harnesses.ja.md">日本語</a> · <b>한국어</b> · <a href="harnesses.ru.md">Русский</a></p>

---

<p align="center">harness(에이전트 실행 환경) 15개의 설치 방법입니다. 그중 6개는 자체 플러그인 명령으로
assay를 설치합니다. 나머지 9개는 skill 파일을 알맞은 위치에 복사하면 되며, 이 방법은 skill을
읽는 harness라면 어디서든 동작합니다.</p>

---

## <a id="contents"></a>목차

- [제공되는 기능](#what-you-get)
- [Claude Code](#claude-code)
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

플러그인(plugin)으로 설치하면 두 가지를 모두 얻습니다. 훅은 Claude Code와 DeepSeek Harness에서 동작하며, 페이지를 변경한 턴(turn)이 끝날 때마다 검사를 실행합니다. 다른 harness에서는 skill의 지시에 따라 에이전트가 직접 검사를 실행합니다. opencode와 [그 밖의 harness](#everywhere-else-the-skill-on-its-own)에 속한 harness는 skill만 설치하고, DeepSeek Harness는 Claude Code 브리지를 통해 훅만 사용합니다.

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

## <a id="deepseek-harness"></a>DeepSeek Harness

dsh는 함께 제공되는 브리지를 통해 Claude Code 훅 설정을 실행합니다. 이 브리지를 포함한 프로필은 없으므로 `$DSH_HOME/cordis.patch.yml`에 추가하세요. 이 파일은 모든 프로필의 자체 레이어 다음에 적용되므로 `web`, `headless`, 그리고 직접 만든 모든 프로필에 적용됩니다.

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
mkdir -p .claude/skills
cp -r plugins/assay/skills/checking-a-page .claude/skills/
```

opencode는 `.claude/skills/`, `.opencode/skills/`, `.agents/skills/`, `~/.config/opencode/skills/`를 읽습니다. `.claude/skills/`를 사용하는 것이 좋습니다. Claude Code도 이 폴더를 읽으므로 폴더 하나로 두 도구에서 모두 쓸 수 있습니다.

---

## <a id="devin-cli"></a>Devin CLI

```bash
devin plugins install awss1i/assay#plugins/assay
```

플러그인은 `plugins/assay`에 있으며, `#` 기호는 Devin에게 그 위치를 찾아보라고 알려 주는 표기입니다. 업데이트는 `devin plugins update assay`로 하세요.

---

## <a id="factory-droid"></a>Factory Droid

```bash
droid plugin marketplace add https://github.com/awss1i/assay
droid plugin install assay@assay
```

---

## <a id="github-copilot-cli"></a>GitHub Copilot CLI

```bash
copilot plugin marketplace add awss1i/assay
copilot plugin install assay@assay
```

---

## <a id="everywhere-else-the-skill-on-its-own"></a>그 밖의 harness에서 skill만 사용하기

*Antigravity, Codex App, Codex CLI, Cursor, Gemini CLI, Grok Build CLI, Kimi
Code, Pi, Hermes Agent.*

assay는 이 harness들의 형식에 맞는 플러그인을 제공하지 않으므로, skill을 파일로 설치합니다. skill은 마크다운 파일 하나이며, skill이나 지침 파일을 읽는 곳이라면 어디서든 동작합니다.

[`plugins/assay/skills/checking-a-page/`](../plugins/assay/skills/checking-a-page)를 harness가 skill을 읽는 폴더에 복사하세요. 예를 들어 Hermes Agent는 프로젝트의 `.agents/skills/`를 읽습니다. 또는 파일 내용을 `AGENTS.md`에 붙여 넣으세요.

훅이 없으면 매 턴이 끝날 때마다 검사가 실행되는 대신, 에이전트가 검사를 언제 실행할지 결정합니다.

**[skill의 동작 방식 →](../plugins/assay/README.ko.md#the-skill)**

---

이 문서는 [harnesses.md](harnesses.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
