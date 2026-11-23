<!-- i18n-source: docs/development.md 8f7e644727f16095e74e0ce33482485d38527a96 -->

<h1 align="center">개발</h1>

<p align="center"><a href="../README.ko.md">assay</a> › 개발</p>

<p align="center"><a href="development.md">English</a> · <a href="development.zh-CN.md">简体中文</a> · <a href="development.ja.md">日本語</a> · <b>한국어</b> · <a href="development.ru.md">Русский</a></p>

<p align="center">assay의 코드가 어떻게 구성되어 있는지, 그리고 변경 종류마다 무엇이 필요한지 설명합니다.</p>

---

## <a id="contents"></a>목차

- [코드 구성](#how-the-code-is-laid-out)
- [규칙 변경하기](#changing-a-rule)
- [테스트](#tests)
- [벤치마크](#benchmarks)
- [harness 추가하기](#adding-a-harness)
- [문서 변경하기](#changing-the-docs)
- [문서](#docs)

---

## <a id="how-the-code-is-laid-out"></a>코드 구성

**`src/assay/`**는 도구 본체입니다.

- `browser.py`는 폴더를 서빙하고, 페이지를 열고, 로딩을 기다리고, 픽셀과 텍스트, 입력란, 스타일을 읽습니다. 측정만 할 뿐 무언가가 실패했는지는 판단하지 않습니다.
- `surface.py`는 렌더링된 페이지를 컨트롤(control) 목록으로 바꾸고 검사(check) 계획을 만듭니다.
- `run.py`에는 모든 것을 실행하는 `check()`와, 검사마다 검사 전후의 페이지를 비교해 통과 여부를 판단하는 `judge()`가 있습니다. 규칙(rule) 대부분이 여기에 있습니다.
- `qa.py`는 계획을 실행하고 결과를 보관합니다. 브라우저 코드가 없어서 브라우저 없이 테스트할 수 있습니다.
- `links.py`는 같은 발견 사항(finding)인 실패를 묶습니다. 끝난 결과를 읽기만 하고 결과를 바꾸지 않습니다.
- `report.py`는 `--report` 페이지를 작성합니다.
- `tint.py`는 터미널 색상을 다룹니다.
- `cli.py`는 `assay` 명령입니다.

**`plugins/assay/`**는 skill과 플러그인(plugin)입니다.

- `skills/checking-a-page/`가 skill이며, 마크다운 파일 하나입니다.
- `hooks/pages.py`는 파일 시각을 보고 한 턴(turn)에서 변경된 페이지를 찾습니다.
- `hooks/check_pages.py`는 그 페이지들을 검사하고 결과를 항상 보고합니다.

**`benchmarks/`**는 assay를 채점하는 데 쓰는 페이지입니다.

- `generated/`에는 AI가 작성한 프로그램과 그 정답표(answer key)가 있습니다.
- `planted/`에는 정상 동작하는 프로그램과 의도적으로 심은 버그(planted bug)가 있는 복사본이 있습니다.
- `harness/`에는 채점 스크립트 두 개와, 발견 사항 묶기를 확인하는 정답표가 있습니다.

**`tests/`**는 테스트 스위트입니다. **`docs/`**에는 문서와, 실제 실행 결과로 README의 그림을 그리는 스크립트가 있습니다.

---

## <a id="changing-a-rule"></a>규칙 변경하기

규칙은 검사가 실패했는지를 결정하는 모든 것입니다. 대부분 `run.py`의 `judge`에 있고, 규칙을 건드리는 검사는 `surface.py`에서 만듭니다.

1. **테스트를 두 개 작성합니다.** 하나는 규칙이 문제로 표시해야 하는 페이지이고, 다른 하나는 표시해서는 안 되는 페이지입니다. 순수한 비교는 브라우저가 필요 없는 `tests/test_judge.py`에 넣습니다. 실제 페이지가 필요한 것은 `tests/test_end_to_end.py`에 넣습니다.
2. **두 벤치마크를 모두 실행**하고, 변경 전과 후의 숫자를 풀 리퀘스트에 적습니다. 테스트로는 정상 동작하는 프로그램의 오탐(false alarm)을 볼 수 없지만, 벤치마크로는 볼 수 있습니다.
3. **오탐은 미탐(miss)보다 비용이 큽니다.** 버그를 세 개 더 잡더라도 정상 동작하는 페이지 하나를 문제로 표시하는 규칙은 개선이 아닙니다. 오탐은 누군가가 올바른 코드를 고치게 만들기 때문입니다.
4. **무슨 일이 있었는지 쉬운 말로 알립니다.** 메시지는 assay가 무엇을 했고 페이지가 어떻게 반응했는지를 말합니다. 예를 들면 *when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late*(같은 상태에서 두 번 눌렀을 때 첫 번째에는 아무것도 바뀌지 않고 두 번째에 페이지가 바뀌었으므로 한 번 늦게 반응한다)와 같습니다. *this page is broken*(이 페이지는 고장 났다) 같은 결론만 내놓지 않으며, 규칙을 읽지 않은 사람도 이해할 수 있어야 합니다.
5. **문서에 적습니다.** `docs/how-it-works.md`에서 그 규칙을 일으키는 동작 아래에 규칙을 추가하고, assay가 하는 일, 출력하는 메시지, 보고하지 않는 경우와 그 이유를 적습니다.

오탐을 고치려면 문제로 표시된 페이지가 필요하며, 그 페이지를 문제없는 상태로 남아야 하는 테스트로 추가합니다.

---

## <a id="tests"></a>테스트

```bash
pytest -q
```

전체 스위트는 약 25분이 걸립니다. 테스트 대부분이 실제 브라우저를 구동하기 때문입니다. `tests/test_judge.py`, `tests/test_plan.py`, `tests/test_links.py`, `tests/test_perform.py`, `tests/test_translations.py`는 브라우저가 필요 없고 몇 초 만에 끝나므로, 작업하는 동안에는 이 테스트를 실행하세요. 시간 대부분은 `tests/test_end_to_end.py`가 차지하며, 브라우저가 없으면 실패하지 않고 건너뜁니다.

CI는 풀 리퀘스트마다 Python 3.10, 3.11, 3.12, 3.13, 3.14에서 전체 스위트를 실행하고, 두 벤치마크 채점 스크립트도 짧게 실행합니다. 모두 통과해야 병합할 수 있습니다.

버그 수정에는 수정 전에 실패하고 수정 후에 통과하는 테스트가 필요합니다.

---

## <a id="benchmarks"></a>벤치마크

```bash
python benchmarks/harness/generated.py    # 생성된 세트
python benchmarks/harness/planted.py      # 버그를 심은 세트
```

규칙이나 `benchmarks/`를 변경하면 변경 전과 후에 두 채점 스크립트를 모두 실행해야 합니다. 각 스크립트는 요약 한 줄을 출력하며, 두 줄 모두 풀 리퀘스트에 적습니다. 정상 동작하는 페이지를 문제로 표시하지 않으면서 버그를 더 많이 찾을 때만 변경을 개선으로 봅니다.

정답표의 판단은 사람이 직접 작성합니다. 변경 때문에 assay가 벤치마크 프로그램에서 새로운 내용을 보고하게 되면, 그 새 발견 사항이 무엇인지 기록할 때까지 채점 스크립트는 아무것도 쓰지 않습니다.

[Harness](../benchmarks/harness/README.md)

---

## <a id="adding-a-harness"></a>harness 추가하기

- **harness(에이전트 실행 환경)가 skill을 읽는다면,** 설치 방법을 `docs/harnesses.md`에 추가하고 `plugins/assay/skills/checking-a-page/`를 가리키게 하세요.
- **자체 플러그인 형식이 있다면,** marketplace 파일을 다른 파일들(`.claude-plugin/`, `.cursor-plugin/`, `.grok-plugin/`, `.agents/plugins/`, `.github/plugin/`) 옆에 추가하고 같은 곳에 설명을 적으세요.
- **그 harness에서 직접 테스트하고,** 사용한 버전을 알려 주세요.
- **개수를 고칩니다.** README, 설치 문서, harness 문서, 플러그인의 README는 모두 지원하는 harness가 몇 개인지 적고 있습니다.
- **보고만 하고 고치지 않습니다.** skill과 플러그인은 무엇을 눌렀고 무슨 일이 있었는지를 전달할 뿐, 그 때문에 코드를 수정하지 않습니다. 이 원칙을 지켜 주세요.

---

## <a id="changing-the-docs"></a>문서 변경하기

문서는 중국어 간체, 일본어, 한국어, 러시아어로도 제공합니다. 영어만 변경하세요. 그러면 `tests/test_translations.py`가 실패하는데, 이는 예상된 일이며 변경을 병합하기 전에 메인테이너가 번역을 고칩니다.

---

## <a id="docs"></a>문서

| 문서 | 다루는 내용 |
|---|---|
| [문서 번역하기](development/translating.md) | 모든 번역이 따르는 규칙과, 테스트가 번역을 최신 상태로 유지하는 방법 |
| [용어집](development/glossary.md) | assay의 용어에 각 언어가 쓰는 단어 |

---

이 문서는 [development.md](development.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
