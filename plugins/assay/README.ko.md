<!-- i18n-source: plugins/assay/README.md 228c8a685c996bdf309f1d30fcdd9410cff35811 -->

<h1 align="center">skill과 플러그인</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <b>한국어</b> · <a href="README.ru.md">Русский</a></p>

---

<p align="center">에이전트가 방금 작성한 페이지를 검사(check)하게 하는 두 가지 방법입니다.
<strong><a href="../../docs/harnesses.ko.md">harness(에이전트 실행 환경) 15개의 설치 방법 →</a></strong></p>

---

## <a id="contents"></a>목차

- [skill](#the-skill)
- [플러그인](#the-plugin)
- [수정하지 않고 보고만 하기](#reporting-not-fixing)

---

## <a id="the-skill"></a>skill

skill은 지원하는 harness 15개 모두에서 동작합니다. [`skills/checking-a-page/SKILL.md`](skills/checking-a-page/SKILL.md)는 에이전트에게 페이지를 완성한 뒤 다음 명령을 실행하라고 지시합니다.

```bash
assay <the page> --one-line
```

그리고 출력을 한 글자도 바꾸지 않고 그대로 옮겨 답변을 끝내라고 지시합니다.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

문제가 있을 때는 다음과 같습니다.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

이 네 줄은 버그 하나입니다. 반복되는 줄은 메시지를 되풀이하는 대신 첫 번째 발견 사항(finding)을 가리킵니다. 에이전트는 assay의 출력을 요약하지 않고 그대로 옮기므로, 숫자와 문구가 정확하게 유지됩니다. skill만 사용하면 검사를 언제 실행할지는 에이전트가 결정합니다.

---

## <a id="the-plugin"></a>플러그인

플러그인(plugin)은 `Stop` 훅(hook)을 추가합니다. 이 훅은 페이지를 변경한 턴(turn)이 끝날 때마다 검사를 실행합니다. Claude Code에서는 플러그인이 skill과 훅을 함께 설치합니다. DeepSeek Harness는 Claude Code 브리지를 통해 훅만 단독으로 사용합니다.

- **검사하는 페이지.** 웹 파일이 하나라도 바뀌면 같은 폴더의 페이지를 검사 대상으로 표시하므로, `app.js`만 수정해도 검사합니다. 폴더마다 가장 최근에 바뀐 `.html` 파일을 검사하며, 바뀐 시각이 같으면 `index.html`을 우선합니다.
- **탐색 범위.** 폴더를 최대 네 단계 깊이까지 찾고, `node_modules`와 `.git`은 건너뛰며, 마지막 실행 이후 바뀐 파일만 고려하고, 턴마다 최대 세 페이지를 검사합니다.
- **페이지를 검사하면 항상 보고합니다.** 그래서 문제없다는 결과를 assay가 실행되지 않은 것으로 착각할 일이 없습니다. 페이지를 변경하지 않은 턴은 아무것도 보고하지 않습니다.
- **결과를 볼 수 있도록 턴을 열어 둡니다.** 단, 두 번 연속으로 열어 두지는 않습니다. 이를 위해 harness의 `stop_hook_active` 플래그를 확인하고 타임스탬프를 기록합니다(harness의 임시 폴더, 없으면 `.git/`, 그것도 없으면 `.assay-last-run` 파일에 기록). 타임스탬프를 기록할 수 없으면 턴을 열어 두지 않고 보고만 합니다.

---

## <a id="reporting-not-fixing"></a>수정하지 않고 보고만 하기

에이전트는 assay가 찾은 내용을 보여 주고, 요청하지 않는 한 그 결과 때문에 코드를 수정하지 않습니다. assay는 페이지의 용도를 모르므로, 발견 사항은 확인된 버그가 아니라 살펴볼 곳입니다. 컨트롤(control)은 눌린 시점의 상태에서 아무것도 하지 않는 것이 맞을 수 있고, 값이 일부러 제한되어 있을 수도 있습니다. 에이전트에게 무언가를 고쳐 달라고 요청하면 에이전트가 고칩니다.

---

이 문서는 [README.md](README.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
