<!-- i18n-source: README.md 8c074d8000142ff19d4c5491cdd2f2a8293ab8ad -->

<h1 align="center">assay</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <b>한국어</b> · <a href="README.ru.md">Русский</a></p>

<p align="center">
  <a href="https://github.com/awss1i/assay/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-7c3aed" alt="python"></a>
  <a href="https://github.com/awss1i/assay/blob/main/LICENSE"><img src="https://img.shields.io/badge/licence-MIT-7c3aed" alt="licence"></a>
  <a href="https://github.com/sickn33/agentic-awesome-skills"><img src="https://img.shields.io/badge/listed%20in-agentic--awesome--skills-db2777" alt="listed in agentic-awesome-skills"></a>
  <a href="https://github.com/TheJambo/awesome-testing"><img src="https://img.shields.io/badge/listed%20in-awesome--testing-db2777" alt="listed in awesome-testing"></a>
</p>

<p align="center">
  <a href="#install">설치</a> · <a href="#use">사용법</a> · <a href="#benchmarks">벤치마크</a> · <a href="#how-it-works">동작 방식</a> · <a href="#why">왜 assay인가</a> · <a href="#limits">한계</a> · <a href="#contributing">기여하기</a> · <a href="#licence">라이선스</a>
</p>

---

<p align="center"><strong>에이전트 네이티브 웹 페이지 QA CLI. 결정론적이며 테스트 작성도, LLM도 필요 없습니다.</strong></p>

<p align="center"><code>pip install assay-ui</code></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/awss1i/assay/main/docs/run.svg" alt="드래그로 순서를 바꾸는 목록에 assay를 실행한 터미널입니다.
페이지에서 검사 7개를 계획했고 1개가 통과, 6개가 실패했습니다. 첫 번째 실패는
페이지에서 아무것도 바뀌지 않았다고 알리고, 나머지 다섯 개는 같은 발견 사항이라고
알립니다.">
</p>

<p align="center"><i>버그가 들어 있는, 드래그로 순서를 바꾸는 목록을 검사하는 모습.</i></p>

---

assay는 Chromium에서 페이지를 열고, 페이지의 모든 컨트롤(control)을 찾아 전부 사용해 본 뒤, 무엇이 잘못되었는지 보고합니다.

- **테스트를 작성할 필요가 없습니다.** assay는 페이지에서 찾은 컨트롤로 검사(check)를 만듭니다.
- **LLM을 쓰지 않습니다.** API 키도 비용도 필요 없고, 몇 번을 실행해도 결과가 같습니다.
- **코딩 에이전트(coding agent)와 함께 동작합니다.** harness(에이전트 실행 환경) 15개에서 지원하는 skill은 에이전트가 작성한 페이지를 하나하나 검사하게 하고, Claude Code와 DeepSeek Harness용 플러그인(plugin)은 매 턴(turn)이 끝날 때마다 검사를 자동으로 실행합니다.
- **반복되는 실패를 묶습니다.** 버그 하나 때문에 여러 검사가 실패하면, 뒤에 실패한 검사는 같은 메시지를 반복하는 대신 *same finding as C003*(C003과 같은 발견 사항)이라고 표시합니다.

---

## <a id="install"></a>설치

```bash
pip install assay-ui           # Python 3.10+
```

```bash
uv tool install assay-ui       # Python 3.10+가 없으면 uv가 내려받습니다
```

```bash
pipx install assay-ui          # assay를 별도의 격리된 환경에 설치합니다
```

`pip` 명령을 찾을 수 없다면 `python3 -m pip install assay-ui`를 사용하세요. 첫 실행 때 필요하면 Chromium을 내려받습니다.

assay 자체를 개발하려면 다음 명령을 실행하세요.

```bash
git clone https://github.com/awss1i/assay.git && cd assay
pip install -e ".[dev]"
```

### <a id="for-coding-agents"></a>코딩 에이전트용

먼저 위의 CLI를 설치한 다음, **[harness 설정 →](https://github.com/awss1i/assay/blob/main/docs/harnesses.ko.md)** 안내에 따라 지원하는 harness 15개 중 원하는 곳에 skill이나 플러그인을 추가하세요.

---

## <a id="use"></a>사용법

```console
assay ./my-app                    # 이 폴더의 index.html 검사
assay ./my-app --report out.html  # 스크린샷이 포함된 HTML 보고서도 작성
assay ./my-app --one-line         # 스크립트와 에이전트용 짧은 요약
```

하나라도 실패하면 종료 코드가 0이 아닌 값이 되고, 요청하지 않으면 디스크에 아무것도 쓰지 않습니다.

**[전체 플래그, 실제 예시, Python API, HTML 보고서(report) →](https://github.com/awss1i/assay/blob/main/docs/usage.ko.md)**

### <a id="with-coding-agents"></a>코딩 에이전트와 함께 쓰기

**skill**은 지원하는 harness 15개, 즉 Claude Code, DeepSeek Harness, opencode, Antigravity, Codex App, Codex CLI, Cursor, Devin CLI, Factory Droid, Gemini CLI, GitHub Copilot CLI, Grok Build CLI, Kimi Code, Pi, Hermes Agent 모두에서 동작합니다. 이 skill은 에이전트에게 페이지를 완성한 뒤 assay를 실행하고, 그 결과로 답변을 끝내라고 지시합니다.

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

**플러그인**(Claude Code와 DeepSeek Harness)은 페이지를 변경한 턴이 끝날 때마다 검사를 자동으로 실행하는 훅(hook)을 추가합니다. 어느 쪽이든 에이전트는 assay가 찾은 내용을 보고하고, 요청하지 않는 한 그 결과 때문에 코드를 수정하지 않습니다.

```
/plugin marketplace add awss1i/assay
/plugin install assay@assay
```

**[skill과 플러그인의 동작 방식 →](https://github.com/awss1i/assay/blob/main/plugins/assay/README.ko.md)**

---

## <a id="benchmarks"></a>벤치마크

assay의 점수는 이 저장소에 있는 두 가지 페이지 세트로 매깁니다. 아래의 모든 숫자는 채점 스크립트가 기록합니다.

**AI가 작성한 페이지.** AI가 프롬프트 75개로 각각 세 번씩 작성한 작은 웹 앱 225개이며, 사람이 하나하나 열어서 직접 사용해 봤습니다.

assay는 고장 난 페이지 20개 중 15개에서 실제 버그를 찾았고, 정상 동작하는 페이지 205개 중 문제로 표시한 페이지는 0개입니다. [모든 페이지와 결과](https://github.com/awss1i/assay/blob/main/bench/README.md).

**의도적으로 심은 버그(planted bug)가 있는 페이지.** assay의 존재를 전혀 알지 못하는 별도의 에이전트가 정상 동작하는 앱 10개의 복사본에 각각 스스로 고른 버그를 5개씩 심고, 그 목록을 남겼습니다.

assay는 심은 버그 50개 중 12개를 찾았고, 원본 페이지 10개 중 문제로 표시한 페이지는 0개입니다. [모든 버그와 결과](https://github.com/awss1i/assay/blob/main/bench/planted/README.md).

---

## <a id="how-it-works"></a>동작 방식

assay는 다음 다섯 단계로 동작합니다.

1. 폴더를 localhost에서 서빙하고 Chromium에서 페이지를 엽니다.
2. 페이지의 컨트롤이 더 이상 바뀌지 않을 때까지 기다립니다.
3. 브라우저가 렌더링하는 모든 컨트롤을 나열합니다. 클릭할 수 있는 div, 드래그 핸들, 편집 가능한 영역도 포함합니다.
4. 이 컨트롤로 검사를 계획합니다. 모든 버튼을 한 번, 그리고 두 번 누르고, 입력란(field)에 빈 값, 평범한 텍스트, 아주 긴 텍스트, HTML이 섞인 텍스트를 입력하고, 모든 드롭다운을 바꾸고, 캔버스에 그리고, 양식(form)을 채워 제출하는 등의 검사입니다.
5. 각 검사를 새 탭에서 실행하고, 검사 전후의 페이지를 비교합니다.

assay는 페이지의 용도를 모르기 때문에, 아무것도 바꾸지 않는 버튼만으로는 실패로 보지 않습니다. 대신 페이지가 스스로 모순되는(the page contradicts itself) 곳을 보고합니다. 예를 들면 다음과 같습니다.

- 페이지에서 오류가 발생합니다.
- Undo가 처음 눌렀을 때는 아무것도 하지 않고, 두 번째로 눌렀을 때 동작합니다.
- 목록이 비어 있는데 항목 개수가 1로 표시됩니다.
- 항목을 추가하면 합계가 올라가지만, 항목을 삭제해도 합계가 내려가지 않습니다.
- 숫자가 있어야 할 자리에 `NaN`이 나타납니다.
- 페이지의 어떤 컨트롤을 사용해도 페이지가 전혀 반응하지 않습니다.

**[모든 규칙(rule) →](https://github.com/awss1i/assay/blob/main/docs/how-it-works.ko.md)**

---

## <a id="why"></a>왜 assay인가

Playwright와 Cypress는 누군가 작성한 테스트가 있어야 합니다. 시각적 회귀 테스트는 기준이 되는 스크린샷이 있어야 합니다. 모델에게 코드 리뷰를 맡기면 모델은 코드를 읽을 뿐 실행하지는 않습니다. assay는 미리 준비할 것 없이 코드를 직접 실행합니다.

|  | 테스트 작성 필요 | 베이스라인 필요 | 프로그램 실행 |
|---|---|---|---|
| Playwright / Cypress | 예 | 아니요 | 예, 작성한 부분만 |
| Percy / Chromatic | 아니요 | **예** | 스크린샷을 찍음 |
| 모델에게 리뷰 요청 | 아니요 | 아니요 | **아니요, 소스를 읽음** |
| **assay** | **아니요** | **아니요** | **예, 전부** |

---

## <a id="limits"></a>한계

- **의도는 검사할 수 없습니다.** 합계를 잘못 더하는 것처럼, 실행은 되지만 엉뚱한 일을 하는 페이지는 대개 통과합니다. 이런 부분을 검사하려면 Python에서 인수 기준(acceptance criteria)을 넘기세요.
- **웹 페이지만 검사합니다.** 로컬 폴더에서 서빙한 페이지를 한 번에 하나씩 검사합니다. 크롤링, 로그인, 실제 네트워크 호출은 하지 않습니다.
- **빌드 결과물만 검사합니다.** `npm install`이나 빌드를 대신 실행하지 않습니다. 소스 트리를 지정하면 먼저 무엇을 실행해야 하는지 알려 줍니다.
- **끝난 게임은 고장 난 것처럼 보일 수 있습니다.** 다시 시작할 방법 없이 끝난 게임은 반응하지 않으므로, 아무것도 반응하지 않는다고 보고될 수 있습니다.
- **속도.** 대부분의 페이지는 몇 초에서 1분 정도 걸립니다. 벤치마크 페이지에 페이지별 소요 시간과 측정에 쓴 머신이 나와 있습니다.

---

## <a id="contributing"></a>기여하기

버그와 오탐(false alarm)은 이슈로 알려 주시고, 변경 사항은 풀 리퀘스트로 보내 주세요. 질문이나 아이디어는 [Discussions](https://github.com/awss1i/assay/discussions)에서 나눠 주세요. 자세한 내용은 **[CONTRIBUTING.md](https://github.com/awss1i/assay/blob/main/CONTRIBUTING.md)** 문서를 참고하세요.

---

## <a id="licence"></a>라이선스

MIT.

---

이 문서는 [README.md](README.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
