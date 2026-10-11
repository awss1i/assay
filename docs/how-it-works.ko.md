<!-- i18n-source: docs/how-it-works.md 5bf8fdf49caa9b6254f86f4d95b7b052a8547b2c -->

<h1 align="center">동작 방식</h1>

<p align="center"><a href="how-it-works.md">English</a> · <a href="how-it-works.zh-CN.md">简体中文</a> · <a href="how-it-works.ja.md">日本語</a> · <b>한국어</b> · <a href="how-it-works.ru.md">Русский</a></p>

---

<p align="center">assay는 실제 브라우저에서 페이지를 열고, 페이지의 모든 컨트롤(control)을 찾아, 미리
계획한 여러 검사(check)에서 하나씩 사용해 보고, 검사마다 검사 전후의 페이지를 비교합니다.
assay는 페이지의 용도를 모르기 때문에, 페이지가 스스로 모순될(the page contradicts itself)
때만 보고합니다. 예를 들어 페이지에서 오류가 발생하거나, 컨트롤이 한 번 늦게 반응하거나,
목록이 비어 있는데 개수가 1로 표시되는 경우입니다.</p>

<p align="center">이 문서의 앞부분은 실행이 어떻게 진행되는지 설명합니다. 뒷부분은 검사 종류별로
assay가 하는 일, 보고하는 내용과 출력하는 정확한 메시지, 그리고 일부러 보고하지 않는 경우와
그 이유를 다룹니다. 여기 나오는 모든 규칙(rule)은 <a href="../bench/README.md">벤치마크</a>로
측정했으며, 예외 대부분은 규칙을 더 넓게 적용한 버전이 정상 동작하는 페이지를 문제로
표시했기 때문에 생겼습니다.</p>

---

## <a id="contents"></a>목차

- [실행 과정](#how-a-run-goes)
  - [페이지 서빙](#serving-the-page)
  - [페이지 로딩 기다리기](#waiting-for-the-page-to-load)
  - [컨트롤 찾기](#finding-the-controls)
  - [검사 계획](#planning-the-checks)
  - [각 검사 실행](#running-each-check)
  - [통과, 실패, 검사하지 못함](#passed-failed-or-not-checked)
  - [발견 사항 묶기](#grouping-findings)
- [assay가 검사하는 항목](#what-assay-checks)
  - [페이지 열기](#opening-the-page)
  - [버튼과 링크 누르기](#pressing-buttons-and-links)
  - [입력란에 입력하기](#typing-into-fields)
  - [양식을 채워 제출하기](#filling-in-a-form-and-submitting-it)
  - [목록에 항목을 추가하고 삭제하기](#adding-items-to-a-list-and-removing-them)
  - [목록의 개수나 합계를 나타내는 숫자](#numbers-that-count-or-total-a-list)
  - [저장과 새로 고침](#saving-and-reloading)
  - [셀, 칩, 카드를 두 번 클릭하기](#clicking-cells-chips-and-cards-twice)
  - [서로 반대되는 버튼 쌍](#buttons-that-come-in-opposite-pairs)
  - [캔버스에 그리기](#drawing-on-a-canvas)
  - [그린 뒤 버튼 누르기](#pressing-a-button-after-drawing)
  - [게임과 애니메이션 캔버스](#games-and-animated-canvases)
  - [핸들과 행 드래그하기](#dragging-handles-and-rows)
  - [슬라이더, 체크박스, 드롭다운, 색상, 파일](#sliders-checkboxes-dropdowns-colours-and-files)
  - [탭과 펼칠 수 있는 섹션](#tabs-and-expandable-sections)
  - [마크업의 레이블과 라디오 버튼](#labels-and-radio-buttons-in-the-markup)
  - [플레이스홀더가 자기 패턴을 통과하지 못하는 입력란](#fields-whose-placeholder-fails-their-own-pattern)
  - [페이지에 나타나는 NaN, undefined, [object Object]](#nan-undefined-and-object-object-on-the-page)
  - [아무것도 반응하지 않는 페이지](#a-page-where-nothing-responds)
- [assay가 검사할 수 없는 것](#what-assay-cant-check)

---

## <a id="how-a-run-goes"></a>실행 과정

### <a id="serving-the-page"></a>페이지 서빙

assay는 파일을 직접 여는 대신 폴더를 localhost에서 서빙합니다. `file://`로 연 페이지는 JavaScript 모듈을 불러올 수 없기 때문입니다.

assay는 빌드를 절대 실행하지 않습니다. `npm install`은 의존성에 들어 있는 스크립트를 무엇이든 실행하는데, assay는 아직 아무도 검토하지 않은 코드를 위한 도구이기 때문입니다. 소스 트리를 지정하면 직접 실행해야 할 명령을 알려 줍니다.

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

### <a id="waiting-for-the-page-to-load"></a>페이지 로딩 기다리기

`load` 이벤트는 대부분의 프레임워크가 아무것도 그리기 전에 발생하므로, assay는 이 이벤트도, 고정된 대기 시간도 쓰지 않습니다. 페이지의 컨트롤이 더 이상 바뀌지 않을 때까지 기다립니다.

스피너만 보여 주는 페이지도 변화가 없는 상태이므로, 페이지에 조작할 수 있는 무언가가 생긴 뒤에야 변화가 멈춘 것을 준비 완료로 봅니다. 그렇지 않으면 *Loading…* 상태에서 멈춘 페이지가 컨트롤이 없는 완성된 페이지처럼 보일 것입니다.

---

### <a id="finding-the-controls"></a>컨트롤 찾기

assay는 브라우저가 렌더링하는 모든 버튼, 입력란(field), 드롭다운, 캔버스, 링크를 나열합니다. 각각에 대해 CSS 선택자, 레이블, 활성화 여부, 크기, 그리고 속한 양식(form)이나 컨테이너를 기록합니다.

assay는 HTML 소스가 아니라 렌더링된 페이지를 읽습니다. JavaScript로 만든 컨트롤도 포함하고, `display: none`, `visibility: hidden`, `opacity: 0`이나 크기 0으로 숨긴 컨트롤은 제외합니다.

HTML 태그로 드러나지 않는 컨트롤도 찾습니다.

| 컨트롤 | assay가 알아보는 방법 |
|---|---|
| 일반 div로 만든 그리드의 셀 | `cursor: pointer` |
| 정렬할 수 있는 표 헤더 | `th`의 `cursor: pointer` |
| 편집 가능한 영역 | `contenteditable` |
| 드래그 핸들이나 크기 조절 바 | `col-resize`, `move`, `grab` 또는 `draggable` |
| 숨긴 박스 위에 그린 별이나 스위치 | 라디오 버튼이나 체크박스는 숨겨져 있고 눈에 보이는 `label` |

JavaScript로 추가한 클릭 핸들러는 페이지에서 읽을 수 없으므로, 요소가 무언가를 한다는 단서는 마우스 커서뿐인 경우가 많습니다.

---

### <a id="planning-the-checks"></a>검사 계획

assay는 찾은 컨트롤로 검사 목록을 만듭니다. 각 검사는 하나 이상의 동작으로 이루어집니다. 버튼을 두 번 누르거나, 양식을 채운 뒤 전송 버튼을 누르는 식입니다. 검사의 모든 종류는 이 문서의 뒷부분에서 설명합니다.

페이지에 비슷해 보이는 컨트롤(그리드의 셀처럼 종류, 레이블, 크기가 같은 컨트롤)이 많으면, assay는 그중 최대 세 개만 사용합니다. 이때 앞의 세 개가 아니라 그룹 전체에 고르게 퍼진 세 개를 고릅니다. 이 규칙이 생기기 전에는 셀 256개짜리 그리드가 있는 한 페이지에서 검사 505개짜리 계획이 나왔고, 늘어난 검사는 모두 같은 내용을 보고했습니다.

---

### <a id="running-each-check"></a>각 검사 실행

각 검사는 새 탭에서, 방금 로드한 페이지로 시작합니다. assay는 검사 전후로 다음을 기록합니다.

- 각 캔버스에 칠해진 픽셀, 그 픽셀들의 중심, 평균 색상, 정확한 픽셀 해시
- 보이는 텍스트
- 모든 입력란의 내용과 각 박스의 체크 여부
- 페이지에 있는 요소의 개수
- 모든 요소의 스타일과 클래스를 담은 해시

WebGL 캔버스는 애니메이션 프레임 안에서 읽습니다. 다른 시점에 읽으려 하면 이미 내용이 지워진 뒤이기 때문입니다.

`alert`은 페이지가 반응한 것으로 칩니다. *Length must be mm:ss*(길이는 mm:ss 형식이어야 함)라는 알림 창은 페이지의 다른 부분이 전혀 바뀌지 않았더라도, 양식이 잘못된 입력을 올바르게 거부한 것입니다. `prompt`나 `confirm`은 페이지가 질문을 하는 것이므로 그 자체로는 반응으로 치지 않습니다. 반응으로 치는 것은 페이지가 그 답으로 하는 일입니다. assay는 prompt에는 적절한 값으로 답하고, confirm은 취소하지 않고 수락합니다. 취소하면 테스트하려는 기능까지 취소되기 때문입니다.

---

### <a id="passed-failed-or-not-checked"></a>통과, 실패, 검사하지 못함

검사는 아래 규칙 중 하나라도 어기면 실패하고, 그렇지 않으면 통과합니다. 아예 수행할 수 없었던 검사는 실패가 아니라 *not checked*(검사하지 못함)로 보고합니다.

예를 들어 생성된 계산기 하나는 자체 `eval` 함수를 정의하는데, 이 때문에 assay가 페이지를 읽는 방식이 망가집니다. assay는 다음과 같이 보고합니다.

```
assay couldn't read this page, because the page replaces a built-in function that assay relies on (such as `eval` or `Function`). That doesn't mean the page is broken
```

이 페이지는 검사하지 못한 것으로 보고되며, 계산기는 실제로 제대로 동작합니다.

예를 들어 *Press Space to start*(Space를 눌러 시작) 오버레이 뒤에 가려진 캔버스는 클릭할 수 없습니다. 이처럼 페이지가 검사의 동작 하나를 거부해도 나머지 동작은 계속 진행합니다. 이 이유로 검사가 실패하는 것은 어떤 동작도 수행하지 못했을 때뿐이며, 이때 메시지는 *couldn't*(할 수 없었음)으로 시작합니다.

비활성화된 컨트롤은 페이지가 "지금은 안 된다"고 말하는 것입니다. assay는 그 컨트롤이 비활성화되어 있었다는 사실을 기록하고, 반응이 없는 것을 페이지의 문제로 치지 않습니다. 25를 최댓값인 10으로 맞추고 `+`를 비활성화하는 수량 입력 상자는 의도대로 동작하는 것입니다.

---

### <a id="grouping-findings"></a>발견 사항 묶기

버그 하나 때문에 여러 검사가 실패하면, 첫 번째 실패에만 메시지가 표시되고 나머지는 첫 번째 실패를 가리킵니다.

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

요약 줄에는 그중 몇 개가 반복인지 표시됩니다.

```
18 cases planned, 18 carried out, 10 passed, 8 failed (7 of them repeat an earlier finding)
```

모든 실패는 그대로 나열되고 집계되며, 종료 코드도 바뀌지 않습니다. 묶기는 출력이 읽히는 방식만 바꿉니다.

두 실패는 다음 두 조건을 모두 만족할 때만 하나로 묶입니다.

- 두 실패가 같은 규칙을 같은 메시지로 어겼습니다. 메시지 안에 인용된 이름은 달라도 됩니다.
- 한 태그 바의 칩이나 한 그리드의 셀처럼, 같은 위치에 있는 같은 종류의 컨트롤에서 일어났습니다. 버튼처럼 이름이 있는 컨트롤은 이름도 같아야 하므로, Undo와 Redo는 절대 함께 묶이지 않습니다.

크래시는 오류 메시지가 같고 같은 코드 줄에서 발생했을 때만 묶입니다.

모든 검사가 로딩 중에 이미 오류가 발생한 페이지에서 실행되었다면, 아무것도 반응하지 않는다는 것처럼 페이지 전체에 대한 발견 사항(finding)에 그 사실이 함께 표시됩니다.

```
    ↳ the page threw an error while loading (C001), before anything was pressed
```

벤치마크 페이지의 모든 묶기 결과는 사람이 직접 작성한 정답표(answer key)인 [`bench/links.txt`](../bench/links.txt)와 대조해 확인합니다.

---

## <a id="what-assay-checks"></a>assay가 검사하는 항목

아래 각 섹션은 assay가 페이지에 하는 일, 보고하는 내용, 보고하지 않는 경우와 그 이유를 차례로 설명합니다. 검사 하나에 대한 발견 사항에는 `C001`, `C002` 같은 번호가 붙습니다. 어느 한 검사로는 드러나지 않는, 실행 전체에 대한 발견 사항에는 `F001`, `F002` 같은 번호가 붙고, 페이지 전체에 대한 두 가지 발견 사항(아무것도 반응하지 않음, 아무것도 그려지지 않음)은 `C000`입니다.

### <a id="opening-the-page"></a>페이지 열기

첫 번째 검사는 아무것도 누르지 않고 페이지를 열어 안정될 때까지 기다립니다.

로딩 중이든 이후의 어떤 검사 중이든 페이지에서 잡히지 않은 오류가 발생하면, assay는 브라우저의 오류 메시지를 그대로 담아 보고합니다.

```
C001 [FAILED] open the page and let it settle
    → the page threw an error and stopped running, Cannot read properties of null (reading 'addEventListener')
```

같은 오류를 만난 검사는 모두 그 오류를 보고하고, 반복된 보고는 첫 번째 보고 아래로 묶입니다.

페이지에 아무것도 표시되지 않으면 assay는 다음과 같이 보고합니다.

```
    → the page shows nothing at all (no text, no images and nothing drawn), so there's nothing to test
```

이 규칙은 컴포넌트가 `null`을 반환하던 React 앱 때문에 추가했습니다. 그 앱에는 컨트롤이 없었기 때문에 검사는 "open the page"(페이지 열기) 하나뿐이었고, 그 검사는 통과했습니다. 빈 페이지는 사용할 것이 아무것도 없을 때, 또는 반응을 기대하는 검사(양식 제출 등) 뒤에도 비어 있을 때만 보고합니다. 그리기 전까지는 빈 캔버스뿐인 그리기 도구는 로딩 직후 비어 있다는 이유로 보고하지 않습니다.

---

### <a id="pressing-buttons-and-links"></a>버튼과 링크 누르기

assay는 모든 버튼과 링크를 한 번 누르고, 그다음 두 번 연달아 누릅니다. 상태 관련 버그는 두 번째 Start, Undo 뒤의 Undo, 한쪽 방향으로만 전환되는 토글처럼 두 번째로 누를 때 드러나는 경우가 많기 때문입니다. 또 처음 세 버튼을 두 개씩 짝지어 양쪽 순서로 누릅니다(Undo 다음 Clear, Clear 다음 Undo). 페이지가 한쪽 순서는 제대로 처리하고 다른 쪽 순서는 잘못 처리할 수 있기 때문입니다.

이 검사들에서 assay는 페이지에서 발생한 오류만 보고합니다. 버튼이 무엇을 위한 것인지 알 수 없으므로, 버튼이 무언가를 바꾸기를 요구하지 않습니다. 선택 표시 없이 브러시 색만 바꾸는 색상 견본은 눈에 보이는 변화가 없지만 고장 난 것이 아닙니다. 이전 버전은 눈에 보이는 변화를 요구했는데, 그때는 정상 동작하는 그림 도구의 검사 21개 중 9개를 문제로 표시했습니다. 무슨 일이 일어났는지는 여전히 근거에 "the visible text is unchanged"(보이는 텍스트가 바뀌지 않음) 같은 형태로 기록되며, 실패로 기록되지 않을 뿐입니다.

그래도 아무 일도 하지 않는 버튼은 두 가지 경우에 잡아냅니다. 반대 동작을 하는 짝 버튼은 동작할 때([반대되는 버튼 쌍](#buttons-that-come-in-opposite-pairs) 참고), 그리고 페이지 전체에서 아무것도 반응하지 않을 때([아무것도 반응하지 않는 페이지](#a-page-where-nothing-responds) 참고)입니다.

---

### <a id="typing-into-fields"></a>입력란에 입력하기

assay는 모든 텍스트 입력란에 네 종류의 값을 입력합니다. 빈 값, 평범한 텍스트(`Sample item`), 300자짜리 문자열, 그리고 쉼표, 따옴표, HTML이 섞인 텍스트입니다. 숫자 입력란에는 빈 값과 숫자를 입력합니다. 날짜와 시간 입력란(`date`, `time`, `datetime-local`, `month`, `week`)에는 빈 값과 해당 타입에 맞는 유효한 값을 입력합니다. 입력한 뒤에는 입력란에서 포커스를 옮기므로, `change` 이벤트에 반응하는 페이지도 입력을 감지합니다.

이 검사들에서 assay는 페이지에서 발생한 오류만 보고합니다. 읽기 전용 입력란은 출력용이므로 입력하지 않습니다. 비밀번호 생성기는 생성한 답을 읽기 전용 입력란에 씁니다.

---

### <a id="filling-in-a-form-and-submitting-it"></a>양식을 채워 제출하기

같은 양식이나 컨테이너 안에서 뒤에 버튼이 있는 입력란마다, assay는 그 양식의 모든 입력란을 채운 뒤 버튼을 누릅니다. 누르기 전에 양식 안의 라디오 버튼 묶음마다 첫 번째 옵션을 고르고 드롭다운도 모두 바꿉니다. 평점이나 그룹 선택이 필수인 양식은 그 값 없이 전송을 거부하는 것이 옳기 때문입니다.

각 입력란에는 그 타입이 허용하는 값을 넣습니다. 이메일 입력란에는 이메일 주소, `tel` 입력란에는 전화번호, `url` 입력란에는 URL, 날짜 입력란에는 유효한 날짜를 넣습니다. 레이블은 그다음에 고려합니다. 그래서 *Phone*이라는 레이블이 붙은 텍스트 입력란에는 `555-0100`을, 플레이스홀더가 *mm:ss*인 입력란에는 `3:30`을 넣습니다.

assay가 무언가 바뀌기를 요구하는 검사는 이 종류뿐입니다. 입력을 받고 제출 버튼이 눌렸는데도 어디에도 변화가 없는 페이지는 입력을 받아들이지 않은 것입니다.

```
C007 [FAILED] type into Title, then press Add
    → nothing on the page changed at all
```

assay는 다음 경우에는 이를 보고하지 않습니다.

- **버튼이 그 입력란의 버튼이 아닌 경우.** 같은 양식이나 컨테이너에서 입력란 뒤에 오는 첫 번째 버튼만 누릅니다. 할 일 목록의 필터 버튼(All, Active, Done)은 입력한 내용을 무시하는 것이 맞는데, 입력란을 이런 버튼과 짝지었더니 정상 동작하는 목록 세 개를 문제로 표시했습니다. Enter로 항목을 추가하는 할 일 목록처럼 뒤에 버튼이 없는 입력란은 제출 검사를 아예 하지 않습니다.
- **입력란이 캔버스 페이지의 설정인 경우.** 캔버스가 있는 페이지에서 숫자나 날짜 입력란은 대개 브러시 크기 같은 설정이므로, 페이지가 반응하지 않아도 되며 대신 캔버스 검사가 판단합니다.
- **페이지가 알림 창으로 응답한 경우.** 잘못된 입력을 거부하는 양식이 그 예입니다.
- **버튼이 비활성화된 경우.**
- **끝난 게임처럼 페이지가 스스로 멈춘 경우.** 단, 페이지가 무엇을 누르라고 안내했다면 예외입니다([게임](#games-and-animated-canvases) 참고).

---

### <a id="adding-items-to-a-list-and-removing-them"></a>목록에 항목을 추가하고 삭제하기

할 일 목록은 처음 로드했을 때 입력 상자와 버튼 하나뿐입니다. 체크박스, 각 항목 옆의 Delete 버튼, 남은 항목 수는 항목이 생기기 전까지 존재하지 않습니다. 그래서 페이지에 양식이 있으면 assay는 양식을 채워 두 번 제출하고(두 번째에는 다른 값으로), 그 뒤에 새로 나타난 모든 컨트롤에 대해 검사를 계획합니다. 이 검사들은 모두 같은 두 항목을 추가하는 것으로 시작하므로, 검사 이름이 *with two saved*(두 항목을 저장한 상태)로 끝납니다. 서로 다른 항목이 두 개 필요한 이유는, 엉뚱한 항목을 지우는 Delete는 항목이 하나뿐일 때 그 문제를 드러낼 수 없기 때문입니다.

검사가 항목을 지웠는데 버튼을 누른 그 항목이 여전히 남아 있으면, assay는 다음과 같이 보고합니다.

```
C014 [FAILED] press Remove, with two saved
    → this removed a row, but not the one it belongs to, and 'Another item https://example.com/other' is still there
```

텍스트가 똑같은 항목들은 어느 것이 지워졌는지 알 수 없으므로 건너뜁니다.

실행이 끝나면 assay는 양식에 입력한 내용이 그 양식으로 만든 항목에 표시되는지도 확인합니다. 입력한 값 중 일부가 빠져 있으면 다음과 같이 보고합니다.

```
F001 [FAILED] values typed into a list show up in the new row
    → 'https://example.com/page' was typed in and accepted, but the new row in the list doesn't show it, first seen at C009
```

이 검사는 목록에만 적용합니다. 여기서 목록은 실행 도중 개수가 바뀐 모든 것을 뜻하며, 일반 표의 행도 포함합니다. 목록에 항목이 두 개 있을 때 확인하는데, 항목이 하나뿐이면 누적 합계가 입력한 금액과 같아서 합계를 보여 주는 행도 맞는 것처럼 보이기 때문입니다. assay는 다음 경우에는 이를 보고하지 않습니다.

- **양식이 목록이 아닌 경우.** *Account created*(계정이 생성됨)라고 표시하고 이메일도 비밀번호도 보여 주지 않는 가입 양식은 올바르게 동작하는 것이며, 비밀번호는 반드시 숨겨야 합니다.
- **입력한 값이 하나도 나타나지 않는 경우.** 입력한 내용을 전혀 보여 주지 않는 행은 입력란 하나가 빠진 것이 아니라, 목록이 전혀 다른 것을 보여 주는 것입니다.
- **페이지가 두 번째 항목을 거부한 경우.** 페이지가 받아들이지 않은 값은 사라진 것으로 치지 않습니다.

---

### <a id="numbers-that-count-or-total-a-list"></a>목록의 개수나 합계를 나타내는 숫자

실행하는 동안 assay는 페이지의 모든 숫자를 목록의 항목 수와 함께 읽고, 마지막에 둘을 비교합니다.

목록과 함께 1씩 오르내리는 숫자는 목록의 항목 수를 세는 것이므로, 목록이 비어 있으면 0이어야 합니다. 0이 아니면 assay는 다음과 같이 보고합니다.

```
F002 [FAILED] the count of items matches the list
    → a number on this page goes up and down by one with the list, so it counts the list, but it shows 1 when the list is empty. It's +1 off at every size
```

이 규칙은 두 가지 이상의 목록 크기에서 최소 세 번 읽은 값이 있어야 하고, 정수만 사용합니다. 소수는 개수가 아니라 측정값이나 금액이기 때문입니다. 일정한 양만큼 어긋나 있는 것만으로는 보고하지 않습니다. 고정 배송비를 더하는 장바구니는 내용물과 같은 폭으로 움직이며, 어느 크기에서든 올바릅니다. 목록이 비었을 때 0이 아닌 개수만 보고합니다.

항목을 추가할 때마다 바뀌는 숫자는 목록을 따라가는 것이므로, 항목을 지울 때도 바뀌어야 합니다. 한 번도 바뀌지 않으면 assay는 다음과 같이 보고합니다.

```
F003 [FAILED] a total that follows the list also goes down
    → a number on this page changed every time the list grew (4 times) but never when it shrank (2 times), so it stops following the list when items are removed
```

행을 삭제했을 때 합계를 다시 계산하지 않는 지출 관리 앱이 이런 경우입니다. 여기서는 금액도 대상에 포함합니다. 목록을 따라가야 하는 숫자 중 가장 흔한 것이 누적 합계이기 때문입니다. 목록이 늘어나는 것과 줄어드는 것을 모두 관찰했어야 하고, 숫자가 항목을 추가할 때마다 빠짐없이 바뀌었어야 합니다. 가끔만 바뀌는 숫자는 다른 무언가를 따라가는 것이기 때문입니다.

---

### <a id="saving-and-reloading"></a>저장과 새로 고침

항목 두 개를 추가한 뒤, assay는 페이지가 그 항목을 페이지 자체의 `localStorage`나 `sessionStorage`에 저장했는지 확인합니다. 저장했다면 페이지는 다음에도 항목이 남아 있을 것이라고 약속한 셈이므로, assay는 두 항목을 다시 추가하고 페이지를 새로 고친 뒤 항목이 여전히 표시되는지 확인합니다. 항목이 사라졌으면 다음과 같이 보고합니다.

```
C021 [FAILED] save two, reload, and they're still there
    → 'Sample item' and 'Another item' were saved in browser storage by the page, but are gone after reloading it
```

이 검사는 페이지가 값을 저장했고, 새로 고침 전에 그 값을 표시하고 있었을 때만 적용합니다. 아무것도 저장하지 않는 페이지에는 적용하지 않습니다.

---

### <a id="clicking-cells-chips-and-cards-twice"></a>셀, 칩, 카드를 두 번 클릭하기

버튼이 아닌 클릭 가능한 요소(그리드 셀, 태그 칩, 카드, 별)는 한 번 클릭하고, 그다음 두 번 연달아 클릭합니다. 또 첫 번째 요소를 클릭한 뒤 바로 옆 요소를 클릭합니다. 두 번 클릭하는 검사에서 assay는 페이지의 나머지 부분뿐 아니라 요소 자체도 지켜봅니다. 조작 대상이 그 요소이기 때문입니다.

요소가 첫 번째 클릭에는 바뀌지 않고 두 번째 클릭에 바뀌었다면 한 번 늦게 반응하는 것이므로, assay는 다음과 같이 보고합니다.

```
C011 [FAILED] click Mon 9:00 twice
    → when clicked twice, this didn't change on the first click and did on the second, so it reacts one press late
```

이 규칙으로 예약 표시 스타일이 반대로 적용되던 일정 관리 앱을 잡아냈습니다. 주변 페이지만이 아니라 요소 자체가 두 번째 클릭에서 바뀌었어야 합니다. 화면 키보드의 키는 자기 모양을 절대 바꾸지 않는데(누를 때마다 다른 곳에 있는 보드에 글자가 입력됩니다), 보드가 바뀐 것을 키가 바뀐 것으로 읽었더니 모든 키를 늦게 반응한다고 표시했습니다.

요소가 첫 번째 클릭에 바뀌고 두 번째 클릭에 원래대로 돌아왔는데 페이지의 나머지 부분은 돌아오지 않았다면, assay는 다음과 같이 보고합니다.

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
```

태그는 다시 꺼진 것처럼 보이는데 목록은 여전히 필터링된 상태로 남는 태그 필터가 이런 경우입니다. 두 번째 클릭이 요소 자체 말고는 아무것도 바꾸지 않았을 때만 보고합니다. 닫힐 때 안쪽 폴더까지 함께 닫는 트리 폴더는 두 번째 클릭에서 하위 항목과 행 수를 다시 그립니다. 이것은 페이지가 일부러 깔끔한 상태를 고른 것이므로 보고하지 않습니다. 라이트박스를 여는 썸네일처럼 두 번 클릭한 뒤에도 모양이 같은 요소도 보고하지 않습니다.

그 밖에는 이 클릭들도 버튼 누르기와 같은 방식으로 판단합니다. 오류만 보고합니다.

---

### <a id="buttons-that-come-in-opposite-pairs"></a>서로 반대되는 버튼 쌍

단독 버튼은 눈에 보이는 일을 하지 않아도 됩니다. 설명이 되지 않는 것은 서로 반대 동작을 하는 두 버튼을 두고, 한쪽은 누를 때마다 페이지를 바꾸는데 다른 쪽은 한 번도 바꾸지 않는 페이지입니다.

assay는 레이블로 쌍을 찾습니다. 두 레이블이 정확히 한 단어만 다르고, 그 단어가 서로 반대말(next와 previous, forward와 back, undo와 redo, up과 down, increase와 decrease, more와 less, plus와 minus, add와 remove 또는 delete, expand와 collapse)이면 쌍으로 봅니다. 또 assay는 버튼을 두 개씩 양쪽 순서로 누르므로, 반응이 없는 버튼은 짝 버튼 바로 뒤에, 즉 되돌릴 것이 있는 상태에서 눌리게 됩니다. 한쪽은 매번 페이지를 바꾸고 다른 쪽은 한 번도 바꾸지 않았다면 assay는 다음과 같이 보고합니다.

```
F001 [FAILED] Previous works as well as Next
    → Next changed the page, but Previous never did, even right after Next. As a pair, Previous should reverse what Next does
```

방금 로드한 슬라이드 덱에서 Previous는 아무것도 하지 않는 것이 맞습니다. 그래서 판단에 쓰는 것은 Next 바로 뒤에 누른 Previous입니다.

---

### <a id="drawing-on-a-canvas"></a>캔버스에 그리기

assay는 모든 캔버스에 대해 다음을 합니다.

- 흔한 그리드 크기에서 셀 경계를 피하도록 고른 네 지점을 클릭합니다.
- 비슷한 프로그램을 조작하는 방식으로 사용합니다. 두 번 클릭한 뒤 Space, 오른쪽 화살표와 아래쪽 화살표, Enter를 누르고 드래그합니다.
- 선을 하나 그린 뒤, 다른 곳에 선을 하나 더 그립니다.

첫 번째 선은 나타났는데 두 번째 선이 나타나지 않았다면 캔버스가 더 이상 그리기를 받아들이지 않는 것이므로, assay는 다음과 같이 보고합니다.

```
C019 [FAILED] draw on canvas, then draw somewhere else on it
    → the first line drawn on this canvas appeared, but a second line drawn elsewhere did not, so the canvas stopped accepting drawing
```

이를 보고하기 전에 두 번째 선은 여러 위치에서 시도합니다. 첫 번째 선을 무시한 캔버스는 이 검사 대상이 아닙니다. 차트는 드래그해도 그려지지 않으므로, 반응하지 않는다는 점 때문에 저절로 대상에서 빠집니다. 이 규칙은 선 하나만 그리고 그 뒤의 모든 선은 아무 표시 없이 무시하던 그림 앱을 잡아냈는데, 계획에 있는 다른 어떤 검사도 이 문제를 보지 못했습니다.

캔버스를 클릭했을 때 캔버스가 바뀌기를 요구하는 것은 페이지에 다른 사용할 것이 없을 때뿐입니다. 차트는 Add를 눌러야 그려지고, 튀는 공 캔버스는 공을 추가하기 전까지 비어 있습니다. 그래서 캔버스 자체에 반응을 요구했을 때는 정상 동작하는 페이지 네 개를 문제로 표시했습니다. 캔버스만 있는 페이지에서 캔버스를 사용했는데 캔버스가 바뀌지 않으면 assay는 다음과 같이 보고합니다.

```
    → the canvas this check clicked didn't change, even if other parts of the page did
```

그 뒤에도 캔버스에 아무것도 표시되지 않으면 다음과 같이 보고합니다.

```
    → 1 canvas still shows nothing after every step of this check
```

실행이 끝났을 때 어떤 캔버스도 단색 외에는 아무것도 보여 준 적이 없다면, assay는 페이지 전체에 대해 다음과 같이 보고합니다.

```
C000 [FAILED] something appears on the canvas
    → nothing ever appeared on this canvas. 12 checks used the page, and the canvas stayed one flat colour through all of them, so whatever the program draws isn't reaching the screen
```

이 규칙은 변환 때문에 모든 꼭짓점이 잘려 나간 WebGL 큐브 세 개를 잡아냈습니다. 캔버스는 한 가지 색으로 빈틈없이 칠해진 것으로 측정되었지만, 그 위에는 아무것도 없었습니다. 이 발견 사항은 최소 두 개의 검사가 페이지를 사용했고, 다른 검사는 하나도 실패하지 않았고, 페이지의 모든 컨트롤에 도달했을 때만 보고합니다. assay가 도달하지 못한 컨트롤이 바로 그리기를 시작하는 컨트롤일 수도 있기 때문입니다.

---

### <a id="pressing-a-button-after-drawing"></a>그린 뒤 버튼 누르기

캔버스가 있는 페이지의 모든 버튼에 대해, assay는 선 두 개를 그린 다음 버튼을 두 번 누릅니다. 두 번 모두 assay가 측정한 상태에서 누르므로, 첫 번째로 눌렀을 때 아무 변화가 없고 두 번째로 눌렀을 때 변화가 있었다면 그 버튼은 한 번씩 늦게 반응하는 것입니다.

```
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
```

변경 전이 아니라 변경 후의 상태를 저장하는 실행 취소 기록이 이런 모습을 보입니다. 첫 번째 Undo는 이미 화면에 있는 그림을 복원합니다. 선을 두 개 그리는 이유는, 기록에 선이 하나뿐이면 두 번 다 아무 일도 일어나지 않아 결함이 드러나지 않기 때문입니다. 방금 로드한 페이지가 아니라 그린 뒤에 검사하는 이유는, 작용할 대상이 없는 컨트롤은 반응하지 않는 것이 맞기 때문입니다.

두 번째 선이 아무것도 그리지 않았다면 이 검사는 대신 통과하며, 근거에는 다음과 같이 기록됩니다.

```
the second line drew nothing, so there was no second step to undo
```

올바른 Undo는 첫 번째로 눌렸을 때 그 빈 단계를 되돌리며, 이것은 한 번 늦는 것이 아닙니다. 예전에는 이 때문에 두 번째 획이 그려지지 않았던 정상 그림 도구가 Undo가 늦게 반응한다고 보고되었습니다. 두 번째 선이 그려지지 않았다면 캔버스 자체는 여전히 보고합니다([캔버스에 그리기](#drawing-on-a-canvas) 참고).

---

### <a id="games-and-animated-canvases"></a>게임과 애니메이션 캔버스

스스로 진행되는 게임처럼 캔버스가 저절로 움직이면, assay는 동작하기 전에 움직임이 멈추기를 기다립니다. 끝내 멈추지 않으면 캔버스의 변화가 assay의 동작 때문인지 알 수 없으므로, 그런 검사에서는 변화를 요구하지 않습니다.

벽에 부딪힌 스네이크 게임처럼 스스로 멈춘 프로그램은, 그 뒤에 누른 것을 무시해도 보고하지 않습니다. 게임이 정상적으로 동작하는 것이기 때문입니다. 예외는 무엇을 누르라고 안내하는 페이지입니다. *Press Space to restart*(Space를 눌러 다시 시작)라고 표시하는데 Space를 눌러도 아무것도 바뀌지 않으면, 페이지가 자신의 안내를 어긴 것이므로 assay는 다음과 같이 보고합니다.

```
    → the page says to press Space, but pressing Space changes nothing
```

다시 시작할 방법이 없는 끝난 게임은 여전히 고장 난 것처럼 보일 수 있으며, 이 점은 README의 한계 항목에 나와 있습니다.

---

### <a id="dragging-handles-and-rows"></a>핸들과 행 드래그하기

분할 창의 구분선이나 드래그로 순서를 바꾸는 행은 클릭해도 아무 일도 일어나지 않으므로, assay는 이들을 드래그합니다.

- 각 드래그 핸들(`col-resize`, `move`, `grab` 커서)을 드래그하고, 두 번째 검사에서는 두 번 드래그합니다. 두 번째 검사에서는 두 번째 드래그만 측정합니다. 구분선이 고장 나는 가장 흔한 방식이 한 번 움직인 뒤 다시는 잡히지 않는 것이고, 두 드래그를 함께 측정하면 첫 번째 드래그가 두 번째 드래그를 가리기 때문입니다.
- 각 `draggable` 행은 실제 HTML5 드래그 이벤트를 사용해 목록의 맨 끝으로 드래그합니다. 맨 끝으로 옮기는 이유는, 대부분의 목록이 대상 앞에 행을 놓기 때문에 행을 바로 옆 행 위에 놓으면 원래 자리로 돌아가고, 그 결과 드래그할 수 없는 목록처럼 보였기 때문입니다.

드래그는 페이지를 바꿀 것으로 기대합니다. 바꾸지 않으면 assay는 다음과 같이 보고합니다.

```
C012 [FAILED] drag the divider, then drag it again
    → nothing on the page changed at all
```

---

### <a id="sliders-checkboxes-dropdowns-colours-and-files"></a>슬라이더, 체크박스, 드롭다운, 색상, 파일

assay는 모든 슬라이더를 끝까지 옮기고, 모든 체크박스와 라디오 버튼을 선택하고, 모든 드롭다운에서 다른 옵션을 고르고, 모든 색상 선택기를 다른 색으로 바꾸고, 모든 파일 입력에 허용하는 형식의 작은 파일을 넣습니다.

이 검사들에서 assay는 버튼과 같은 이유로 페이지에서 발생한 오류만 보고합니다. 슬라이더나 체크박스가 무엇을 바꿔야 하는지 알 수 없기 때문입니다. 그래도 이 동작들은 페이지를 사용한 것으로 집계되며, [아무것도 반응하지 않음](#a-page-where-nothing-responds) 검사에는 이 집계가 필요합니다.

---

### <a id="tabs-and-expandable-sections"></a>탭과 펼칠 수 있는 섹션

모든 검사를 진행하는 동안 assay는 화면에 있는 각 탭과 섹션 헤더를 읽습니다. `aria-selected="true"`나 `aria-expanded="true"`로 표시된 컨트롤은 `aria-controls`에 지정된 패널이 표시되어 있다고 스크린 리더에 알리는 것입니다. 그 패널이 아예 렌더링되지 않았다면 페이지가 스스로 모순되는 것이므로, assay는 다음과 같이 보고합니다.

```
F001 [FAILED] the panel a selected tab or open section controls is shown
    → "Tab 2" is marked selected and controls the panel "panel-1", but that panel isn't shown, first seen at C004
```

비어 있는 패널도 페이지에 박스가 있으므로 표시된 것으로 칩니다. 브라우저가 아예 렌더링하지 않은 패널만 보고합니다.

---

### <a id="labels-and-radio-buttons-in-the-markup"></a>마크업의 레이블과 라디오 버튼

모든 검사를 진행하는 동안 assay는 레이블과 라디오 버튼이 어떻게 연결되어 있는지도 읽고, 페이지를 눈으로 봐서는 알 수 없는 세 가지 실수를 보고합니다.

- 한 그룹의 라디오 버튼 두 개가 같은 값을 가져서, 양식이 어느 쪽을 골랐는지 구분할 수 없는 경우.

  ```
  F002 [FAILED] labels and radio buttons are linked correctly
      → two radio buttons in the "option" group both have the value "2", so the form can't tell which of them was picked, first seen at C001
  ```

- 레이블의 `for`가 존재하지 않는 id를 가리키는 경우.

  ```
      → the label "Email" is linked to "emial", but nothing on the page has that id, first seen at C001
  ```

- 레이블 두 개가 같은 컨트롤에 연결되어, 두 번째 레이블이 원래 붙어야 했던 컨트롤에 레이블이 없는 경우.

  ```
      → two labels are both linked to "star4", so one of them was meant for another control, which is left without a label, first seen at C001
  ```

---

### <a id="fields-whose-placeholder-fails-their-own-pattern"></a>플레이스홀더가 자기 패턴을 통과하지 못하는 입력란

assay는 `pattern`과 플레이스홀더가 모두 있는 입력란을 전부 읽습니다. 입력란이 스스로 제시한 예시가 자신의 패턴을 통과하지 못하면 예시대로 입력한 사람은 그 입력란이 필수인 양식을 제출할 수 없습니다.

```
F001 [FAILED] the zip box accepts its own placeholder example
    → the placeholder shows "12345" as an example, but the pattern on this field, \d{5}, rejects it, so someone who types what the example shows can't submit a form that requires this field
```

이 규칙은 입력해서 찾는 것이 아니라 마크업에서 읽어 냅니다. 이 규칙을 만든 계기가 된 입력란이 검사가 도달하지 못하는 위저드의 뒷 단계에 있었기 때문입니다. 공백이 들어간 플레이스홀더는 *Enter five digits*(숫자 다섯 자리를 입력하세요)처럼 예시 값이 아니라 안내 문구이므로 건드리지 않습니다.

---

### <a id="nan-undefined-and-object-object-on-the-page"></a>페이지에 나타나는 NaN, undefined, [object Object]

모든 검사를 진행하는 동안 assay는 보이는 텍스트와 모든 입력란에서 `NaN`, `undefined`, `[object Object]`를 찾습니다. 이런 값을 일부러 보여 주는 페이지는 없습니다. 이런 값은 어떤 값이 설정되기 전에 사용되었거나, 숫자가 아닌 것으로 계산되었다는 뜻입니다. assay는 다음과 같이 보고합니다.

```
F001 [FAILED] no NaN, undefined or [object Object] on the page
    → the page shows `NaN` where a value should be, "Total: NaN". This usually means a value was used before it was set, or calculated from something that isn't a number, first seen at C008
```

assay 자신이 숫자가 아닌 값을 입력한 검사에서는 보고하지 않습니다. `Sample item`을 입력받은 온도 변환기가 `NaN`을 표시하는 것은 올바릅니다. 받은 질문에 대한 맞는 답이기 때문입니다. 여기서 빈 입력란은 숫자로 칩니다.

---

### <a id="a-page-where-nothing-responds"></a>아무것도 반응하지 않는 페이지

개별 검사는 버튼이 무언가를 하도록 요구하지 않기 때문에, 모든 버튼이 아무 데도 연결되지 않은 페이지라도 모든 검사를 통과하게 됩니다. 그래서 실행이 끝나면 assay는 같은 내용을 페이지 전체를 대상으로 확인합니다. 컨트롤을 사용했는데 페이지가 한 번도 바뀌지 않았다면 다음과 같이 보고합니다.

```
C000 [FAILED] something on the page responds when used
    → nothing on the page changed after any control was used. 14 checks used what the page offers and none of them changed it, so the controls don't seem to be connected to any code
```

이 규칙으로 Add 버튼 세 개가 아무 데도 연결되지 않은 칸반 보드를 잡아냈습니다. 이 발견 사항은 페이지 전체가 고장 났다고 판정하므로, 다음 조건을 모두 만족할 때만 보고합니다.

- 서로 다른 컨트롤을 두 개 이상 사용했습니다.
- 어떤 검사에서도 페이지의 어느 곳에서든 변화를 보지 못했습니다.
- assay가 페이지의 모든 컨트롤에 도달했습니다. 예전에 클릭 가능한 셀은 사용했지만 정렬 헤더에는 도달하지 못한 정렬 가능한 표가 이렇게 보고된 적이 있는데, 그 표는 정렬이 완벽하게 동작했습니다.
- 페이지를 다시 열고 1초도 안 되는 시간 대신 몇 초를 주는 과정을 세 번 반복해도 페이지가 여전히 아무것도 하지 않습니다. Retry를 누르면 2초짜리 로딩을 시작하는 페이지는 검사 하나에 주어지는 시간 안에서는 반응이 없는 것처럼 보입니다.

---

## <a id="what-assay-cant-check"></a>assay가 검사할 수 없는 것

assay는 컨트롤이 무엇을 해야 하는지 모르기 때문에, 합계를 잘못 더하는 것처럼 실행은 되지만 엉뚱한 일을 하는 페이지는 대개 통과합니다. 컨트롤이 해야 할 일을 검사하려면 인수 기준(acceptance criteria)을 작성해 Python에서 넘기세요. `check(folder, criteria=[...])`는 각자의 동작과 기대 결과를 가진 케이스를 받고, 그 기대 결과를 작성된 그대로 검사합니다.

---

이 문서는 [how-it-works.md](how-it-works.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
