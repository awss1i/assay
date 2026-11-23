<!-- i18n-source: docs/getting-started.md 87f5daae1ec1d0ee044476575debceac6d4328a6 -->

<h1 align="center">시작하기</h1>

<p align="center"><a href="../README.ko.md">assay</a> › 시작하기</p>

<p align="center"><a href="getting-started.md">English</a> · <a href="getting-started.zh-CN.md">简体中文</a> · <a href="getting-started.ja.md">日本語</a> · <b>한국어</b> · <a href="getting-started.ru.md">Русский</a></p>

<p align="center">assay 설치부터 매일 사용하기까지를 설명합니다.</p>

---

## <a id="contents"></a>목차

- [시작하기 전에](#before-you-start)
- [페이지 검사하기](#checking-a-page)
- [결과 읽기](#reading-the-result)
- [버그가 있는 페이지](#a-page-with-a-bug)
- [페이지 지정하기](#choosing-the-page)
- [HTML 보고서](#the-html-report)
- [짧은 요약](#a-short-summary)
- [코딩 에이전트와 함께 쓰기](#with-a-coding-agent)
- [다음에 읽을 문서](#where-to-go-next)

---

## <a id="before-you-start"></a>시작하기 전에

Python 3.10 이상과 브라우저가 열 수 있는 페이지, 즉 `.html` 파일이 들어 있는 폴더가 필요합니다.

```bash
pip install assay-ui
```

프로젝트에 빌드 단계가 있다면 먼저 빌드한 뒤 출력 폴더를 검사하세요. assay는 빌드를 직접 실행하지 않습니다.

[모든 설치 방법](install.ko.md)

---

## <a id="checking-a-page"></a>페이지 검사하기

페이지가 들어 있는 폴더를 assay에 지정하세요.

```console
assay ./my-app
```

첫 실행 때는 Chromium을 내려받으며, 이는 한 번만 일어납니다. 그다음 assay는 폴더를 localhost에서 서빙하고, Chromium에서 `index.html`을 열고, 페이지가 렌더링한 모든 컨트롤(control)을 나열하고, 그 컨트롤로 검사(check)를 계획한 뒤, 검사마다 새 탭에서 실행합니다. 대부분의 페이지는 몇 초에서 1분이면 끝납니다.

저장소에는 assay를 채점하는 데 쓰는 페이지가 들어 있으므로, 저장소를 클론하면 이 문서의 예시를 그대로 실행할 수 있습니다. 다음은 정상 동작하는 클릭 카운터입니다.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter
7 cases planned, 7 carried out, 7 passed, 0 failed

C001 [ok] open the page and let it settle
C002 [ok] press Increment
C003 [ok] press Increment twice
C004 [ok] press Reset
C005 [ok] press Reset twice
C006 [ok] press Increment, then Reset
C007 [ok] press Reset, then Increment
```

---

## <a id="reading-the-result"></a>결과 읽기

첫 줄은 assay가 계획한 검사 수, 그중 수행한 수, 통과한 수와 실패한 수를 알려 줍니다. 그 뒤의 각 줄은 검사 하나이며, 번호와 결과, 검사가 한 일을 보여 줍니다.

| 결과 | 의미 |
|---|---|
| `[ok]` | 검사를 실행했고 문제가 없었습니다 |
| `[FAILED]` | 페이지가 스스로 모순되었고(the page contradicts itself), 검사 아래 줄이 그 내용을 알려 줍니다 |
| `[not checked]` | assay가 검사를 수행하지 못했으며, 이는 실패로 세지 않습니다 |

종료 코드는 실패가 없으면 0, 검사가 하나라도 실패하면 1, 페이지를 아예 검사할 수 없으면 2이므로 스크립트에서 이 값으로 판단할 수 있습니다.

첫 실행 때 Chromium을 내려받는 것을 제외하면, 요청하지 않는 한 디스크에 아무것도 쓰지 않습니다.

---

## <a id="a-page-with-a-bug"></a>버그가 있는 페이지

다음은 Undo가 한 번 늦게 반응하는 작은 그림 프로그램입니다.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

실패한 검사는 C016입니다. 첫 번째 Undo는 아무것도 하지 않았고 두 번째 Undo가 실제 작업을 했으므로, Undo가 한 번씩 늦게 반응합니다.

버그 하나 때문에 여러 검사가 실패하면, 첫 번째 실패가 메시지를 보여 주고 나머지는 첫 번째 실패를 가리키므로 메시지는 한 번만 읽으면 됩니다.

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

assay는 페이지의 용도를 모르기 때문에, 발견 사항(finding)은 살펴볼 곳이지 확인된 버그가 아닙니다. 컨트롤이 눌린 시점의 상태에서는 아무 일도 하지 않는 것이 올바른 동작일 수 있습니다.

---

## <a id="choosing-the-page"></a>페이지 지정하기

```console
assay ./my-app                    # 이 폴더의 index.html 검사
assay ./my-app/todo.html          # 특정 페이지 검사
assay ./my-app -e app.html        # 또는 폴더 안의 페이지 이름을 지정
```

assay는 로컬 폴더에서 서빙한 페이지를 한 번에 하나씩 검사합니다. 빌드가 필요한 소스 트리를 지정하면 무엇을 실행해야 하는지 알려 줍니다.

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

## <a id="the-html-report"></a>HTML 보고서

`--report`는 열어 볼 수 있는 페이지를 작성하며, 이 페이지는 검사마다 검사 전후의 페이지를 보여 줍니다.

```console
assay ./my-app --report out.html
```

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="태그 필터를 검사한 assay 보고서의 검사
한 건입니다. 태그를 두 번 클릭하자 태그 모양은 원래대로 돌아왔지만 목록은
필터링된 채로 남았습니다. 수행한 동작, 실패 이유, 그리고 항목 12개에서 1개로
바뀐 검사 전후의 페이지 스크린샷이 함께 표시됩니다.">

보고서(report)는 HTML 파일 하나이며, 스크린샷은 그 옆에 보고서 이름을 딴 폴더에 들어갑니다. 여기서는 `out-shots`입니다.

---

## <a id="a-short-summary"></a>짧은 요약

`--one-line`은 스크립트와 에이전트를 위한 짧은 요약을 출력합니다.

```console
$ assay ./todo --one-line
assay: checked todo/index.html, 8 checks, nothing flagged.
```

문제가 있으면 요약에 발견 사항이 하나씩 나열되고, 반복되는 발견 사항은 메시지를 반복하는 대신 첫 번째 발견 사항을 가리킵니다.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

---

## <a id="with-a-coding-agent"></a>코딩 에이전트와 함께 쓰기

assay에는 코딩 에이전트(coding agent)를 위한 두 가지가 함께 들어 있습니다.

**skill**은 에이전트에게 페이지를 완성한 뒤 assay를 실행하고, 그 결과로 답변을 끝내라고 지시합니다.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**플러그인**(plugin)은 페이지를 변경한 턴(turn)이 끝날 때마다 검사를 자동으로 실행하는 훅(hook)을 추가합니다. Claude Code에서는 다음 두 명령이 skill과 훅을 함께 설치합니다.

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

어느 쪽이든 에이전트는 assay가 찾은 내용을 보고하고, 요청하지 않는 한 그 결과 때문에 코드를 수정하지 않습니다.

[Harness](harnesses.ko.md) · [skill과 플러그인](../plugins/assay/README.ko.md)

---

## <a id="where-to-go-next"></a>다음에 읽을 문서

문서는 모든 옵션과 Python API, assay가 하는 모든 검사와 각 검사가 출력하는 메시지, 그리고 코딩 에이전트 harness(에이전트 실행 환경)별 설정을 다룹니다.

[문서](../README.ko.md#docs)

---

이 문서는 [getting-started.md](getting-started.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
