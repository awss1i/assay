<!-- i18n-source: docs/usage.md 4fc8af90f6d6d12babc4d55ec7e9668ec62ae3d8 -->

<h1 align="center">사용법</h1>

<p align="center"><a href="../README.ko.md">assay</a> › 사용법</p>

<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <a href="usage.ja.md">日本語</a> · <b>한국어</b> · <a href="usage.ru.md">Русский</a></p>

<p align="center">assay 명령의 모든 옵션, 출력하는 내용, 종료 코드, HTML 보고서, Python API를 설명합니다.</p>

---

## <a id="contents"></a>목차

- [명령어](#the-command)
- [옵션](#options)
- [assay가 출력하는 내용](#what-assay-prints)
  - [기본 출력](#the-default-output)
  - [짧은 요약](#the-short-summary)
  - [JSON](#json)
  - [컨트롤 목록](#the-controls)
- [종료 코드](#exit-codes)
- [HTML 보고서](#the-html-report)
- [색상](#colour)
- [오류](#errors)
- [Python에서 사용하기](#from-python)
  - [페이지 검사하기](#checking-a-page)
  - [인수 기준](#acceptance-criteria)
  - [컨트롤 나열하기](#listing-the-controls)

---

## <a id="the-command"></a>명령어

```console
assay ./my-app                    # 이 폴더의 index.html 검사
assay ./my-app/todo.html          # 특정 페이지 검사
assay ./my-app -e app.html        # 또는 폴더 안의 페이지 이름을 지정

assay ./my-app --report out.html  # 스크린샷이 포함된 HTML 보고서도 작성
assay ./my-app --json             # 실행 전체를 JSON으로 출력
assay ./my-app --one-line         # 스크립트와 에이전트용 짧은 요약
assay ./my-app --surface          # 찾은 컨트롤을 나열한 뒤 종료
```

assay는 경로를 하나 받습니다. 경로가 폴더이면 assay는 그 폴더를 서빙하고 그 안의 `index.html`을 엽니다. 경로가 `.html`, `.htm`, `.xhtml`로 끝나면 그 파일이 검사할 페이지이며, 페이지는 옆에 있는 파일을 불러오므로 assay는 그 파일이 들어 있는 폴더를 서빙합니다.

하나라도 실패하면 종료 코드가 0이 아닌 값이 됩니다. 첫 실행 때 Chromium을 내려받는 것을 제외하면, 요청하지 않는 한 디스크에 아무것도 쓰지 않습니다.

---

## <a id="options"></a>옵션

| 옵션 | 하는 일 |
|---|---|
| `-e ENTRY`, `--entry ENTRY` | 폴더 안에서 `index.html` 대신 `ENTRY`를 엽니다 |
| `--report FILE` | 검사마다 검사 전후의 페이지 스크린샷이 담긴 HTML 보고서(report)를 `FILE`에도 작성합니다 |
| `--json` | 기본 출력 대신 실행 전체를 JSON으로 출력합니다 |
| `--one-line` | 무엇을 검사했고 무엇을 문제로 표시했는지(flagged) 알려 주는 짧은 요약을 출력합니다 |
| `--if-page` | 경로가 assay가 검사할 수 있는 페이지가 아니면 아무것도 출력하지 않고 0으로 종료합니다 |
| `--surface` | 페이지에 있는 컨트롤(control)을 출력하고 멈추며, 검사(check)는 실행하지 않습니다 |
| `--version` | 설치된 버전을 출력하고 종료합니다 |
| `-h`, `--help` | 옵션 설명을 출력하고 종료합니다 |

`--if-page`는 편집할 때마다 실행되는 훅(hook)을 위한 옵션입니다. 편집 대부분은 페이지를 고치는 것이 아니며, 이 옵션을 주면 assay는 그런 경우에 에이전트의 대화에 오류를 출력하지 않고 조용히 끝납니다.

`--json`과 `--one-line`을 함께 주면 assay는 JSON을 출력합니다.

---

## <a id="what-assay-prints"></a>assay가 출력하는 내용

### <a id="the-default-output"></a>기본 출력

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

첫 줄은 계획한 검사, 수행한 검사, 통과한 검사, 실패한 검사의 수를 알려 줍니다. 그 뒤에 모든 검사가 실행한 순서대로 번호, 결과, 검사가 한 일과 함께 나옵니다.

| 결과 | 의미 |
|---|---|
| `[ok]` | 검사를 실행했고 문제가 없었습니다 |
| `[FAILED]` | 규칙(rule)을 어겼으며, `→`로 시작하는 줄이 무슨 일이 있었는지 알려 줍니다 |
| `[not checked]` | 검사를 수행하지 못했으며, 이는 실패로 세지 않습니다 |

앞선 발견 사항(finding)을 반복하는 실패는 메시지 대신 `↳ same finding as C003`(C003과 같은 발견 사항)을 표시하고, 첫 줄은 실패 중 몇 개가 반복인지 알려 줍니다.

검사에는 `C001`, `C002` 같은 번호가 붙습니다. 어느 한 검사로는 드러나지 않는, 실행 전체에 대한 발견 사항에는 `F001`, `F002` 같은 번호가 붙고, 페이지 전체에 대한 두 가지 발견 사항은 `C000`입니다.

---

### <a id="the-short-summary"></a>짧은 요약

문제가 없으면 `--one-line`은 문장 하나를 출력합니다.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

문제가 있으면 발견 사항마다 한 줄을 출력하고, 반복되는 발견 사항은 메시지를 반복하는 대신 첫 번째 발견 사항을 가리킵니다.

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

수행하지 못한 검사가 있으면 첫 줄이 그 개수를 알려 주므로, 실행되지 않은 검사 때문에 페이지가 문제없다고 보고되는 일이 없습니다. 페이지에서 온 텍스트는 출력 가능한 문자로 된 한 줄로 합쳐지므로, 페이지가 요약에 자기 줄을 끼워 넣을 수 없습니다.

---

### <a id="json"></a>JSON

`--json`은 다음 필드를 가진 객체 하나를 출력합니다.

| 필드 | 담긴 내용 |
|---|---|
| `version` | assay 버전 |
| `entry` | 연 페이지 |
| `planned`, `passed`, `failed` | 계획한 검사, 통과한 검사, 실패한 검사의 수 |
| `works` | 실패한 검사가 없으면 `true` |
| `sandboxed` | 페이지가 Chromium의 샌드박스 안에서 실행됐으면 `true` |
| `surface` | 찾은 모든 컨트롤. 각각의 `kind`, `selector`, `label`과 `enabled` 여부가 들어 있습니다 |
| `cases` | 모든 검사. 아래에서 설명합니다 |
| `links` | 발견 사항 사이의 모든 연결. `from`, `kind`, `to`, `why`로 이루어집니다 |
| `console_errors` | 페이지가 콘솔에 남긴 오류 |
| `failed_requests` | 페이지가 보냈지만 실패한 요청 |

`cases`의 각 항목에는 다음 필드가 있습니다.

| 필드 | 담긴 내용 |
|---|---|
| `id` | 검사 번호. 예를 들면 `C003` |
| `what` | 검사가 한 일을 말로 적은 것 |
| `outcome` | `passed`, `failed`, `unknown` 중 하나. `unknown`은 검사하지 못했다는 뜻입니다 |
| `detail` | 실패한 검사에서 무엇이 잘못됐는지 |
| `measured` | 검사가 통과했든 실패했든 assay가 측정한 내용 |
| `acts` | 검사가 순서대로 수행한 동작 |
| `rules` | 검사가 어긴 규칙의 이름 |
| `key` | 검사가 추가되어도 바뀌지 않는 발견 사항의 이름. 형식은 `rule@what the check did`입니다 |
| `links` | 이 발견 사항에서 다른 발견 사항으로 이어지는 연결. `kind`, `to`, `why`로 이루어집니다 |

콘솔 오류와 실패한 요청 때문에 검사가 실패하는 일은 없습니다. 페이지는 오류를 남기거나 아이콘 하나가 빠져도 정상 동작할 수 있기 때문입니다. 다만 검사가 실제로 실패했을 때는 가장 먼저 읽어 볼 만한 내용인 경우가 많습니다.

---

### <a id="the-controls"></a>컨트롤 목록

`--surface`는 assay가 페이지에서 찾은 것을 한 줄에 컨트롤 하나씩, 종류와 선택자, 레이블, 픽셀 단위 크기와 함께 나열합니다.

```console
$ assay benchmarks/generated/programs/dsh/gpt-oss-120b/01_counter --surface
kind: page
- button `#inc` 'Increment' 151x52
- button `#reset` 'Reset' 107x52
```

---

## <a id="exit-codes"></a>종료 코드

| 코드 | 경우 |
|---|---|
| 0 | 실패한 검사가 없음 |
| 1 | 검사가 하나 이상 실패함 |
| 2 | 페이지가 없거나, 빌드가 필요하거나, Chromium을 설치할 수 없어서 페이지를 검사하지 못함 |

`--if-page`를 주면 assay는 2 대신 0으로 종료합니다. `--surface`는 컨트롤을 나열한 뒤 0으로 종료합니다.

---

## <a id="the-html-report"></a>HTML 보고서

`--report`는 열어 볼 수 있는 페이지를 작성하며, 이 페이지는 검사마다 검사 전후의 페이지를 보여 줍니다.

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="태그 필터를 검사한 assay 보고서의 검사
한 건입니다. 태그를 두 번 클릭하자 태그 모양은 원래대로 돌아왔지만 목록은
필터링된 채로 남았습니다. 수행한 동작, 실패 이유, 그리고 항목 12개에서 1개로
바뀐 검사 전후의 페이지 스크린샷이 함께 표시됩니다.">

보고서는 검사마다 수행한 동작, 결과와 이유, assay가 측정한 내용을 보여 줍니다. 보고서는 HTML 파일 하나이며, 스크린샷은 그 옆에 보고서 이름을 딴 폴더에 들어가므로 `--report out.html`은 `out-shots/`도 작성합니다. 보고서는 인터넷에서 아무것도 불러오지 않으므로 디스크나 CI 아티팩트에서 바로 열 수 있고, 밝은 테마와 어두운 테마를 따릅니다.

---

## <a id="colour"></a>색상

터미널에서는 실패가 눈에 띄도록 assay가 결과에 색을 입힙니다. 파이프나 파일로 보내는 출력에는 색이 없습니다. 환경 변수 `NO_COLOR`를 설정하면 색이 꺼지고, `FORCE_COLOR`를 설정하면 어디서나 색이 켜집니다.

---

## <a id="errors"></a>오류

assay는 다음 메시지를 오류 스트림에 출력합니다.

| 메시지 | 의미 |
|---|---|
| `assay: my-app/index.html doesn't exist` | 경로에 열 페이지가 없습니다 |
| `assay: index.html loads /src/main.jsx, which a browser can't run without a build step.` | 폴더가 소스 트리입니다. assay는 직접 실행해야 할 빌드 명령을 출력하며, 그 명령을 실행하지는 않습니다 |
| `assay: index.html loads /src/main.jsx, which a browser can't run, but dist/index.html is built.` | 폴더에 빌드된 사본이 있으며, assay는 대신 검사할 경로를 출력합니다 |
| `assay: there's no index.html here, but there's a package.json, so the page probably comes from a build step.` | 폴더가 아직 빌드하지 않은 프로젝트입니다 |
| `assay: Chromium isn't installed yet, so assay is downloading it. This only happens once.` | 첫 실행이 Chromium을 내려받고 있습니다 |
| `assay: playwright isn't installed. Run pip install assay-ui to install it.` | 이 Python에 assay의 의존성이 없습니다 |
| `assay: Chromium's sandbox couldn't start on this system, so the page ran without it.` | 페이지 검사는 그대로 진행됐습니다. root로 실행하거나 일부 컨테이너에서 실행하면 샌드박스가 시작되지 않습니다 |

검사 하나를 수행하지 못해도 실행은 계속되며, 그 검사는 이유와 함께 검사하지 못함(not checked)으로 보고됩니다. 예를 들어 페이지가 assay가 의존하는 내장 함수를 바꿔 놓은 경우입니다.

---

## <a id="from-python"></a>Python에서 사용하기

### <a id="checking-a-page"></a>페이지 검사하기

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

`check`는 다음 인자를 받습니다.

| 인자 | 하는 일 |
|---|---|
| `folder` | 페이지가 들어 있는 폴더, 또는 페이지 자체. 명령이 경로를 읽는 것과 같은 방식으로 읽습니다 |
| `entry` | 폴더 안에서 열 페이지. 기본값은 `index.html`입니다 |
| `criteria` | assay의 검사보다 먼저 실행할 직접 작성한 검사. 아래에서 설명합니다 |
| `shots` | 검사마다 검사 전후의 스크린샷을 저장할 폴더. 주지 않으면 디스크에 아무것도 쓰지 않습니다 |

다음 속성을 가진 보고서를 돌려줍니다.

| 속성 | 담긴 내용 |
|---|---|
| `works` | 실패한 검사가 없으면 `True` |
| `plan` | 실행한 순서대로 나열한 모든 검사 |
| `results` | 검사 번호를 키로 하는 각 검사의 결과 |
| `failing` | 실패한 결과. 직접 작성한 기준이 먼저 나옵니다 |
| `unchecked` | 수행하지 못한 검사의 결과 |
| `surface` | assay가 찾은 컨트롤 |
| `console_errors`, `failed_requests` | 페이지가 남긴 오류와 실패한 요청 |
| `summary()`, `render()` | 출력의 첫 줄과 출력 전체. 둘 다 텍스트입니다 |

각 결과에는 실행한 `case`, `"passed"`, `"failed"`, `"unknown"` 중 하나인 `outcome`, 무엇이 잘못됐는지 알려 주는 `detail`, assay가 측정한 `evidence`, 어긴 `rules`, 그리고 `key`가 있습니다.

---

### <a id="acceptance-criteria"></a>인수 기준

assay는 컨트롤이 무엇을 해야 하는지 모르기 때문에, 실행은 되지만 잘못 동작하는 페이지는 대개 통과합니다. 페이지가 해야 할 일을 검사하려면 검사를 직접 작성해 인수 기준(acceptance criteria)으로 넘기세요.

```python
from assay import Case, check

total = Case(
    id="A001",
    what="adding 10 and 20 shows a total of 30",
    acts=[{"fill": "#price=10"}, {"click": "#add"},
          {"fill": "#price=20"}, {"click": "#add"}],
    expect={"want": "Total: 30"},
    origin="criterion",
)

report = check("./my-app", criteria=[total])
```

합계를 잘못 계산하는 페이지에서는 이 기준이 다음 설명과 함께 실패합니다.

```
the page doesn't contain 'Total: 30'
```

`acts`는 순서대로 수행할 동작입니다. 각 동작은 동사와 그 대상으로 이루어집니다.

| 동작 | 하는 일 |
|---|---|
| `{"click": "#add"}` | 선택자와 일치하는 요소를 클릭합니다. `{"click": "Add"}`처럼 컨트롤에 적힌 글자도 쓸 수 있습니다 |
| `{"fill": "#price=10"}` | `=` 뒤의 값을 선택자와 일치하는 입력란에 입력합니다 |
| `{"press": "Enter"}` | 키를 누릅니다 |
| `{"reload": "page"}` | 페이지를 새로 고칩니다 |
| `{"wait": "2"}` | 그만큼의 초를 기다립니다. 최대 10초입니다 |

`expect`는 그 뒤에 참이어야 하는 것을 말합니다.

| 기대 | 참이어야 하는 것 |
|---|---|
| `{"want": "Total: 30"}` | 그 텍스트가 페이지에 나타납니다 |
| `{"unchanged": True}` | 페이지가 그대로 유지됩니다 |
| `{"quiet": True}` | 특별한 조건이 없으므로, 페이지에서 오류가 발생할 때만 검사가 실패합니다 |
| `{}` | 페이지의 무언가가 바뀝니다 |

assay는 모든 검사에 직접 번호를 매기므로, 기준의 `id`는 결과에서 바뀝니다. `--json`은 assay가 계획한 모든 검사의 `acts`를 출력하므로, assay가 동작 종류별로 어떻게 적는지 볼 수 있습니다.

---

### <a id="listing-the-controls"></a>컨트롤 나열하기

`look`은 `--surface`처럼 검사를 실행하지 않고 페이지를 열어 컨트롤을 나열합니다.

```python
from assay import look

opened = look("./my-app")
print(opened.surface.render())
```

---

이 문서는 [usage.md](usage.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
