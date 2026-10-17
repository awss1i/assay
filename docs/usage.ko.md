<!-- i18n-source: docs/usage.md 3b28af15e7fcd3c1fba90ffdf0ef7cdc24513549 -->

<h1 align="center">assay 사용법</h1>

<p align="center"><a href="usage.md">English</a> · <a href="usage.zh-CN.md">简体中文</a> · <a href="usage.ja.md">日本語</a> · <b>한국어</b> · <a href="usage.ru.md">Русский</a></p>

---

<p align="center">assay가 명령줄과 Python에서 할 수 있는 모든 일을 설명합니다.</p>

---

## <a id="contents"></a>목차

- [명령어](#the-command)
- [예시](#an-example)
- [HTML 보고서](#the-html-report)
- [Python에서 사용하기](#from-python)

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

하나라도 실패하면 종료 코드가 0이 아닌 값이 됩니다. 첫 실행 때 Chromium을 내려받는 것을 제외하면, 요청하지 않는 한 디스크에 아무것도 쓰지 않습니다.

---

## <a id="an-example"></a>예시

assay에는 채점에 쓰는 벤치마크 페이지가 함께 들어 있으므로, 지금 바로 그중 하나에 assay를 실행해 볼 수 있습니다. 다음은 Undo가 한 번 늦게 반응하는 작은 그림 프로그램입니다.

```console
$ assay bench/programs/dsh/gpt-oss-120b/37_draw2
24 cases planned, 24 carried out, 23 passed, 1 failed

C015 [ok] draw on canvas, then draw somewhere else on it
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
C017 [ok] draw on canvas twice, then press Redo twice
```

실패한 검사(check)는 C016입니다. 첫 번째 Undo는 아무것도 하지 않았고 두 번째 Undo가 실제 작업을 했으므로, Undo가 한 번씩 늦게 반응합니다.

---

## <a id="the-html-report"></a>HTML 보고서

`--report`는 열어 볼 수 있는 페이지를 작성하며, 이 페이지는 검사마다 검사 전후의 페이지를 보여 줍니다.

<img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/report.png" alt="태그 필터를 검사한 assay 보고서의 검사
한 건입니다. 태그를 두 번 클릭하자 태그 모양은 원래대로 돌아왔지만 목록은
필터링된 채로 남았습니다. 수행한 동작, 실패 이유, 그리고 항목 12개에서 1개로
바뀐 검사 전후의 페이지 스크린샷이 함께 표시됩니다.">

---

## <a id="from-python"></a>Python에서 사용하기

```python
from assay import check

report = check("./my-app")
for result in report.failing:
    print(result.case.what, "->", result.detail)
```

---

이 문서는 [usage.md](usage.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
