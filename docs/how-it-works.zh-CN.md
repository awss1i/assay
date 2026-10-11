<!-- i18n-source: docs/how-it-works.md 5bf8fdf49caa9b6254f86f4d95b7b052a8547b2c -->

<h1 align="center">工作原理</h1>

<p align="center"><a href="how-it-works.md">English</a> · <b>简体中文</b> · <a href="how-it-works.ja.md">日本語</a> · <a href="how-it-works.ko.md">한국어</a> · <a href="how-it-works.ru.md">Русский</a></p>

---

<p align="center">assay 在真实的浏览器中打开你的页面，找出页面上的每个控件（control），按一组规划好的检查（check）逐一使用这些控件，并在每项检查前后对比页面。assay 不知道你的页面是做什么用的，所以只在页面自相矛盾（the page contradicts itself）时才报告，比如页面抛出错误、某个控件的反应晚了一次、列表为空时计数却显示 1，等等。</p>

<p align="center">本页前半部分介绍一次运行的过程。后半部分逐一介绍每类检查：assay 做什么、报告什么以及输出的确切消息，还有它在什么情况下会刻意不报告、为什么。这里的每条规则（rule）都经过<a href="../bench/README.md">基准测试</a>（benchmark）的衡量，其中大多数例外之所以存在，是因为规则更宽泛的版本曾把正常工作的页面标记为有问题。</p>

---

## <a id="contents"></a>目录

- [一次运行的过程](#how-a-run-goes)
  - [托管页面](#serving-the-page)
  - [等待页面加载](#waiting-for-the-page-to-load)
  - [查找控件](#finding-the-controls)
  - [规划检查](#planning-the-checks)
  - [运行每项检查](#running-each-check)
  - [通过、失败或未检查](#passed-failed-or-not-checked)
  - [合并问题](#grouping-findings)
- [assay 检查什么](#what-assay-checks)
  - [打开页面](#opening-the-page)
  - [按下按钮和链接](#pressing-buttons-and-links)
  - [在输入框中输入](#typing-into-fields)
  - [填写并提交表单](#filling-in-a-form-and-submitting-it)
  - [向列表添加条目和删除条目](#adding-items-to-a-list-and-removing-them)
  - [对列表计数或求和的数字](#numbers-that-count-or-total-a-list)
  - [保存与重新加载](#saving-and-reloading)
  - [连续两次点击单元格、标签和卡片](#clicking-cells-chips-and-cards-twice)
  - [成对出现的相反按钮](#buttons-that-come-in-opposite-pairs)
  - [在画布上绘制](#drawing-on-a-canvas)
  - [绘制后按下按钮](#pressing-a-button-after-drawing)
  - [游戏和动画画布](#games-and-animated-canvases)
  - [拖动手柄和行](#dragging-handles-and-rows)
  - [滑块、复选框、下拉框、颜色和文件](#sliders-checkboxes-dropdowns-colours-and-files)
  - [标签页和可展开区域](#tabs-and-expandable-sections)
  - [HTML 中的 label 和单选按钮](#labels-and-radio-buttons-in-the-markup)
  - [占位符不符合自身 pattern 的输入框](#fields-whose-placeholder-fails-their-own-pattern)
  - [页面上的 NaN、undefined 和 [object Object]](#nan-undefined-and-object-object-on-the-page)
  - [毫无响应的页面](#a-page-where-nothing-responds)
- [assay 无法检查什么](#what-assay-cant-check)

---

## <a id="how-a-run-goes"></a>一次运行的过程

### <a id="serving-the-page"></a>托管页面

assay 会在 localhost 上托管整个文件夹，而不是直接打开文件，因为通过 `file://` 打开的页面无法加载 JavaScript 模块。

assay 从不运行你的构建。`npm install` 会执行依赖中包含的任何脚本，而 assay 面向的正是还没有人审查过的代码。如果你把它指向源码目录，它会告诉你需要自己运行什么。

```console
$ assay ./my-vite-app
assay: index.html loads /src/main.jsx, which a browser can't run without a build step.
  Build it in your own shell, then check the output:
    npm install && npm run build && assay my-vite-app/dist
  assay won't run the build itself, because installing dependencies runs their setup scripts, and assay is for checking code nobody has read yet.
```

---

### <a id="waiting-for-the-page-to-load"></a>等待页面加载

`load` 事件会在大多数框架绘制任何内容之前触发，所以 assay 既不依赖这个事件，也不使用固定延时，而是等到页面上的控件不再变化。

只显示加载动画的页面同样是静止的，所以只有当页面上有可以交互的内容时，静止才算加载完成。否则，卡在 *Loading…*（加载中）的页面看起来就会像一个已经加载完、但没有任何控件的页面。

---

### <a id="finding-the-controls"></a>查找控件

assay 会列出浏览器渲染出的每个按钮、输入框、下拉框、画布（canvas）和链接，并记下每个控件的 CSS 选择器、名称、是否可用、尺寸，以及它所属的表单或容器。

assay 读取的是渲染后的页面，而不是 HTML 源码。由 JavaScript 创建的控件会被计入，而用 `display: none`、`visibility: hidden`、`opacity: 0` 隐藏或尺寸为零的控件则不会。

assay 还能找出没有对应 HTML 标签的控件：

| 控件 | assay 的识别方式 |
|---|---|
| 由普通 div 组成的网格中的单元格 | `cursor: pointer` |
| 可排序的表头 | `th` 上的 `cursor: pointer` |
| 可编辑区域 | `contenteditable` |
| 拖动手柄或调整大小的拖动条 | `col-resize`、`move`、`grab` 或 `draggable` |
| 画在隐藏框上方的星星或开关 | 一个可见的 `label`，它对应的单选按钮或复选框是隐藏的 |

用 JavaScript 添加的点击处理函数无法从页面上读取，所以鼠标指针的样式往往是判断一个元素有没有作用的唯一线索。

---

### <a id="planning-the-checks"></a>规划检查

assay 根据找到的控件生成一份检查清单。每项检查包含一个或多个操作，比如连按两次某个按钮，或者填写表单后按下提交它的按钮。本页后半部分会介绍每一类检查。

如果页面上有很多看起来相同的控件（类型、名称和尺寸都相同，比如网格中的单元格），assay 最多只使用其中三个，并且在整组中分散选取，而不是取前三个。在加入这条规则之前，一个带有 256 格网格的页面会生成包含 505 项检查的计划，而多出来的检查报告的都是同一件事。

---

### <a id="running-each-check"></a>运行每项检查

每项检查都在一个全新的标签页中运行，从刚加载完成的页面开始。在检查前后，assay 会记录：

- 每个画布上已绘制的像素、这些像素的中心位置、平均颜色，以及精确的像素哈希，
- 可见文本，
- 每个输入框的内容，以及每个复选框是否被勾选，
- 页面上的元素数量，
- 所有元素的样式和 class 的哈希值。

WebGL 画布要在动画帧内读取，因为等到其他代码有机会读取时，画布内容早已被清空。

`alert` 算作页面做出了响应。一个提示 *Length must be mm:ss*（时长必须为 mm:ss）的 alert，说明表单正确地拒绝了错误输入，即使页面上的其他内容都没有变化。`prompt` 或 `confirm` 是页面在提问，所以它本身不算响应，页面拿到回答后做了什么才算。assay 会给 prompt 填一个合理的值，并接受 confirm 而不是取消，因为取消会中止正在测试的功能。

---

### <a id="passed-failed-or-not-checked"></a>通过、失败或未检查

违反下文中的任意一条规则（rule），检查就会失败，否则就通过。完全无法执行的检查会被报告为 *not checked*（未检查），绝不会算作失败。

例如，某个生成的计算器定义了自己的 `eval` 函数，破坏了 assay 读取页面的方式。assay 报告如下。

```
assay couldn't read this page, because the page replaces a built-in function that assay relies on (such as `eval` or `Function`). That doesn't mean the page is broken
```

这个页面被报告为未检查，而这个计算器其实能正常工作。

如果页面拒绝了检查中的某个操作，比如画布被写着 *Press Space to start*（按空格键开始）的遮罩层挡住而无法点击，这项检查的其余部分仍会继续执行。只有当所有操作都无法完成时，这项检查才会因此失败，此时消息以 *couldn't*（无法）开头。

被禁用的控件，是页面在表示「现在不行」。assay 会记录这个控件被禁用，不会因为它没有反应而判页面有问题。一个数量输入框把 25 限制为最大值 10 并禁用 `+`，这正是预期的行为。

---

### <a id="grouping-findings"></a>合并问题

当一个 bug 导致多项检查失败时，第一项失败会显示消息，其余的则指回第一项。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
C005 [FAILED] click green twice
    ↳ same finding as C003
```

摘要行也会说明其中有多少是重复的。

```
18 cases planned, 18 carried out, 10 passed, 8 failed (7 of them repeat an earlier finding)
```

每一项失败仍会被列出并计数，退出码也不会改变。合并只改变输出的呈现方式。

只有同时满足以下两个条件，两项失败才会被合并：

- 它们违反了同一条规则，并且消息相同（消息中引用的名称除外）。
- 它们发生在同一位置的同一类控件上，比如同一个标签栏中的标签，或同一个网格中的单元格。对于有名称的控件（比如按钮），名称也必须相同，所以 Undo 和 Redo 永远不会被合并。

崩溃只有在错误消息相同、并且是从同一行代码抛出时才会被合并。

如果每项检查运行时，页面都已经在加载过程中抛出过错误，那么针对整个页面的问题（finding），比如页面毫无响应，会注明这一点。

```
    ↳ the page threw an error while loading (C001), before anything was pressed
```

基准测试页面上的每一次合并，都会与人工编写的标准答案（answer key）[`bench/links.txt`](../bench/links.txt) 进行核对。

---

## <a id="what-assay-checks"></a>assay 检查什么

下面每一节先说明 assay 对页面做了什么，再说明它报告什么，最后说明它在什么情况下不报告、为什么。针对单项检查的问题编号为 `C001`、`C002`，依此类推。针对整次运行、任何单项检查都无法单独发现的问题，编号为 `F001`、`F002`。两个针对整个页面的问题（毫无响应、什么都没有画出来）编号为 `C000`。

### <a id="opening-the-page"></a>打开页面

第一项检查只打开页面，等它稳定下来，不按下任何东西。

如果页面抛出未捕获的错误，无论是在加载时还是在之后的任何一项检查中，assay 都会连同浏览器自身的错误消息一起报告。

```
C001 [FAILED] open the page and let it settle
    → the page threw an error and stopped running, Cannot read properties of null (reading 'addEventListener')
```

每一项遇到同一错误的检查都会报告它，重复的报告会合并到第一项之下。

如果页面完全没有显示任何内容，assay 报告如下。

```
    → the page shows nothing at all (no text, no images and nothing drawn), so there's nothing to test
```

这条规则是为一个组件返回 `null` 的 React 应用加入的。那个应用没有任何控件，所以唯一的检查就是「open the page」（打开页面），而这项检查通过了。只有当空白页面没有任何可用的东西，或者一项预期会有响应的检查（比如提交表单）之后页面仍是空白时，才会报告空白页面。绘图工具在你开始绘制之前只是一块空画布，不会因为加载时空白而被报告。

---

### <a id="pressing-buttons-and-links"></a>按下按钮和链接

assay 会把每个按钮和链接各按一次，再连按两次，因为状态相关的 bug 常常在第二次按下时才暴露：第二次按 Start、Undo 之后再 Undo、只能单向切换的开关。assay 还会把前三个按钮两两组合，按两种顺序各按一遍（先 Undo 再 Clear，以及先 Clear 再 Undo），因为页面可能一种顺序正确、另一种顺序出错。

对于这些检查，assay 只报告页面抛出的错误。它不要求按钮必须改变什么，因为它无法知道按钮是做什么用的。一个色块在设置画笔颜色时如果不显示选中状态，就不会产生任何可见变化，但它并没有坏。早期版本曾要求必须有可见变化，结果在一个正常工作的绘图工具上把 21 项检查中的 9 项标记为失败。发生了什么仍会记录在证据中，比如「the visible text is unchanged」（可见文本没有变化）等，只是不算作失败。

一个从来没有任何作用的按钮，仍然可以通过两种方式被发现：一是它有一个能正常工作的相反按钮（见[成对出现的相反按钮](#buttons-that-come-in-opposite-pairs)），二是整个页面都毫无响应（见[毫无响应的页面](#a-page-where-nothing-responds)）。

---

### <a id="typing-into-fields"></a>在输入框中输入

assay 会向每个文本输入框输入四种值：空值、普通文本（`Sample item`）、300 个字符的字符串，以及包含逗号、引号和 HTML 的文本。数字输入框会收到空值和一个数字。日期和时间输入框（`date`、`time`、`datetime-local`、`month` 和 `week`）会收到空值和一个符合其类型的有效值。输入完成后，assay 会让输入框失去焦点，这样监听 `change` 事件的页面就能收到这个事件。

对于这些检查，assay 只报告页面抛出的错误。assay 从不向只读输入框输入内容，因为它们是用来输出的。比如密码生成器会把生成结果写进只读输入框。

---

### <a id="filling-in-a-form-and-submitting-it"></a>填写并提交表单

如果某个输入框后面、在同一个表单或容器中有一个按钮，assay 就会填写这个表单中的所有输入框，然后按下这个按钮。在按下之前，assay 还会在表单中每组单选按钮里选中第一项，并修改每个下拉框，因为一个要求填写评分或分组的表单，在缺少这些信息时拒绝提交是正确的。

每个输入框都会收到其类型能接受的值：email 输入框填电子邮件地址，`tel` 输入框填电话号码，`url` 输入框填 URL，日期输入框填有效日期。在此之后才会参考 label，所以 label 为 *Phone* 的文本输入框会收到 `555-0100`，占位符为 *mm:ss* 的输入框会收到 `3:30`。

这是 assay 唯一要求页面必须发生变化的一类检查。如果页面接收了输入的内容，提交按钮也被按下了，却没有任何地方发生变化，那它就没有接受这次输入。

```
C007 [FAILED] type into Title, then press Add
    → nothing on the page changed at all
```

以下情况下，assay 不会报告这个问题：

- **按钮不属于这个输入框。** assay 只会按下同一表单或容器中、位于输入框之后的第一个按钮。待办列表的筛选按钮（All、Active、Done）忽略输入内容是正确的，而把输入框和这些按钮配对，曾把三个正常的列表标记为失败。后面没有按钮的输入框，比如按 Enter 就添加条目的待办列表，根本不会进行提交检查。
- **输入框是画布页面上的设置项。** 在带有画布的页面上，数字或日期输入框通常是画笔粗细之类的设置，所以不要求页面做出响应，而是交给画布相关的检查来判断。
- **页面用 alert 做出了回应**，比如表单拒绝了错误的输入。
- **按钮被禁用。**
- **页面已经自行停止**，比如游戏已经结束，除非页面提示了要按什么（见[游戏](#games-and-animated-canvases)）。

---

### <a id="adding-items-to-a-list-and-removing-them"></a>向列表添加条目和删除条目

待办列表刚加载时只有一个输入框和一个按钮。复选框、每个条目旁边的 Delete 按钮以及剩余数量，都要等有了条目之后才会出现。所以当页面有表单时，assay 会填写并提交两次，第二次使用不同的值，然后为所有新出现的控件规划检查。这些检查都会先添加同样的两个条目，所以检查名称以 *with two saved*（已保存两个条目）结尾。之所以需要两个不同的条目，是因为当列表里只有一个条目时，删错条目的 Delete 无法暴露这个问题。

如果某项检查删除了一个条目，但被按下的那个条目仍然在列表中，assay 报告如下。

```
C014 [FAILED] press Remove, with two saved
    → this removed a row, but not the one it belongs to, and 'Another item https://example.com/other' is still there
```

文本完全相同的条目会被跳过，因为无法从中看出删掉的是哪一个。

运行结束时，assay 还会检查输入到表单中的内容是否出现在新创建的条目中。如果有部分输入的值没有出现，assay 报告如下。

```
F001 [FAILED] values typed into a list show up in the new row
    → 'https://example.com/page' was typed in and accepted, but the new row in the list doesn't show it, first seen at C009
```

这项检查只针对列表，即在运行过程中数量发生过变化的任何东西，包括普通表格的行。检查时列表中有两个条目，因为只有一个条目时，累计总额等于输入的金额，显示总额的行看起来也是正确的。以下情况下，assay 不会报告这个问题：

- **表单不是列表。** 注册表单显示 *Account created*（账户已创建），既不显示邮箱也不显示密码，这是正确的，而且密码本来就必须隐藏。
- **输入的值一个都没有出现。** 如果一行完全不显示输入的内容，说明这个列表显示的是完全不同的东西，而不是某个输入框的值丢失了。
- **页面拒绝了第二个条目。** 页面没有接受的值不算丢失。

---

### <a id="numbers-that-count-or-total-a-list"></a>对列表计数或求和的数字

在整个运行过程中，assay 会读取页面上的每个数字以及列表中的条目数量，并在最后进行比较。

如果一个数字随着列表增减而加减 1，它就是在为列表计数，所以列表为空时它必须显示为零。如果不是这样，assay 报告如下。

```
F002 [FAILED] the count of items matches the list
    → a number on this page goes up and down by one with the list, so it counts the list, but it shows 1 when the list is empty. It's +1 off at every size
```

这项检查至少需要在两种或更多列表长度下读取三次，而且只使用整数，因为小数表示的是测量值或金额，而不是数量。数字与列表长度之间存在固定偏差，本身并不会被报告。一个加收固定运费的购物车，金额随商品同步变化，在任何数量下都是正确的。只有列表为空时计数不为零，才会被报告。

如果一个数字在每次添加条目时都会变化，它就是在跟随列表，所以删除条目时它也应该变化。如果它从来不变，assay 报告如下。

```
F003 [FAILED] a total that follows the list also goes down
    → a number on this page changed every time the list grew (4 times) but never when it shrank (2 times), so it stops following the list when items are removed
```

这对应的是删除一行后没有重新计算总额的记账应用。这里允许使用金额，因为累计总额正是最常见的应该跟随列表变化的数字。前提是列表既被观察到增长过，也被观察到缩短过，并且这个数字在每一次添加时都发生了变化，因为只是有时变化的数字跟踪的是别的东西。

---

### <a id="saving-and-reloading"></a>保存与重新加载

添加两个条目之后，assay 会检查页面是否把它们写入了自己的 `localStorage` 或 `sessionStorage`。如果写入了，就表示页面承诺下次打开时它们仍在，所以 assay 会再次添加这两个条目，重新加载页面，并检查它们是否仍然显示。如果它们消失了，assay 报告如下。

```
C021 [FAILED] save two, reload, and they're still there
    → 'Sample item' and 'Another item' were saved in browser storage by the page, but are gone after reloading it
```

只有当页面既保存了这些值、又在重新加载之前显示着它们时，才会进行这项检查。从不保存任何内容的页面不会接受这项检查。

---

### <a id="clicking-cells-chips-and-cards-twice"></a>连续两次点击单元格、标签和卡片

不是按钮的可点击元素（网格单元格、标签、卡片、星星）会先被点击一次，再被连续点击两次，此外还会先点击第一个元素、再点击它旁边的元素。对于连续两次点击，assay 除了观察页面其他部分，还会观察这个元素本身，因为它就是被操作的对象。

如果元素在第一次点击时没有变化，第二次才变化，说明它的反应晚了一次点击，assay 报告如下。

```
C011 [FAILED] click Mon 9:00 twice
    → when clicked twice, this didn't change on the first click and did on the second, so it reacts one press late
```

这条规则发现过一个日程预约应用的问题，它的已预约样式是反的。这里要求元素本身在第二次点击时发生变化，而不只是它周围的页面。屏幕键盘上的按键从不改变自身外观（每按一次，就会在别处的面板上打出一个字母），把面板的变化当作按键的变化，曾把每个按键都标记为反应晚了一次。

如果元素在第一次点击时发生变化、第二次点击时恢复原样，但页面其他部分没有恢复，assay 报告如下。

```
C003 [FAILED] click blue twice
    → clicking this twice switched it back off, but the rest of the page didn't change back, so what the first click did is still in effect
```

这对应的是一个标签筛选器，标签看起来已经重新关闭，列表却仍处于筛选状态。只有当第二次点击除了元素本身之外没有改变任何东西时，才会报告这个问题。树形结构中的文件夹在折叠时会把内部的子文件夹一起折叠，于是第二次点击会重绘它的子项和行数，这是页面有意选择的整洁状态，所以不会被报告。两次点击后外观都不变的元素，比如打开灯箱的缩略图，也不会被报告。

除此之外，这些点击的判断方式与按下按钮相同，只报告错误。

---

### <a id="buttons-that-come-in-opposite-pairs"></a>成对出现的相反按钮

单独一个按钮可以没有任何可见效果。但如果页面提供了两个作用相反的按钮，其中一个每次都会改变页面，另一个却从不改变，这就说不通了。

assay 根据按钮上的文字找出成对的按钮。判断标准是两段文字只相差一个单词，并且这个单词是一组反义词（next 和 previous、forward 和 back、undo 和 redo、up 和 down、increase 和 decrease、more 和 less、plus 和 minus、add 和 remove 或 delete、expand 和 collapse）。assay 还会把按钮两两组合，按两种顺序各按一遍，这样没有反应的那个按钮就会在它的搭档之后立即被按下，此时它有东西可以撤回。如果其中一个每次都改变了页面，另一个却从来没有，assay 报告如下。

```
F001 [FAILED] Previous works as well as Next
    → Next changed the page, but Previous never did, even right after Next. As a pair, Previous should reverse what Next does
```

在刚加载的幻灯片中，按 Previous 没有反应是正确的，所以真正算数的是紧接在 Next 之后的那次按下。

---

### <a id="drawing-on-a-canvas"></a>在画布上绘制

对于每个画布，assay 会：

- 在四个点上点击它，这些点特意避开了常见网格尺寸下单元格的边缘，
- 按照这类程序通常的操作方式来使用它：先点击两次，再依次按空格键、右方向键和下方向键、Enter 键，最后拖动一次，
- 在上面画一条线，再在别处画另一条线。

如果第一条线出现了，第二条却没有，说明画布已经不再接受绘制，assay 报告如下。

```
C019 [FAILED] draw on canvas, then draw somewhere else on it
    → the first line drawn on this canvas appeared, but a second line drawn elsewhere did not, so the canvas stopped accepting drawing
```

在报告之前，assay 会在多个位置尝试画第二条线。如果画布连第一条线都没有响应，就根本不会进行这项检查。在图表上拖动不会画出任何东西，图表因为没有响应而自然不在检查范围之内。这条规则发现过一个绘图程序，它只能画一条线，之后的每条线都被悄悄忽略，而计划中的其他检查都发现不了这个问题。

只有当页面除了画布之外没有其他可用的东西时，才要求点击画布会改变它。图表要按下 Add 才会绘制，弹球画布在你添加小球之前是空的，所以要求画布本身做出响应，曾把四个正常的页面标记为失败。在只有一个画布的页面上，如果使用画布后画布没有变化，assay 报告如下。

```
    → the canvas this check clicked didn't change, even if other parts of the page did
```

如果之后画布上仍然什么都没有，assay 报告如下。

```
    → 1 canvas still shows nothing after every step of this check
```

运行结束时，如果没有任何画布显示过单一纯色以外的内容，assay 会针对整个页面报告。

```
C000 [FAILED] something appears on the canvas
    → nothing ever appeared on this canvas. 12 checks used the page, and the canvas stayed one flat colour through all of them, so whatever the program draws isn't reaching the screen
```

这条规则发现过三个 WebGL 立方体页面，它们的变换把所有顶点都裁剪掉了。测量结果显示画布被完全涂满，但只有一种颜色，上面什么都没有。只有当至少两项检查使用过页面、没有其他检查失败、并且页面上的每个控件都被操作到时，才会报告这个问题，因为 assay 没能操作到的控件可能正是开始绘制的那个。

---

### <a id="pressing-a-button-after-drawing"></a>绘制后按下按钮

对于带画布的页面上的每个按钮，assay 会先画两条线，然后连按两次这个按钮。两次按下都从 assay 测量过的状态开始，所以如果第一次按下没有效果、第二次才有，说明这个按钮落后了一次。

```
C016 [FAILED] draw on canvas twice, then press Undo twice
    → when pressed twice from the same starting point, this changed nothing on the first press and changed the page on the second, so it reacts one press late
```

如果撤销历史在每次修改之后（而不是之前）保存状态，就会出现这种情况。第一次 Undo 恢复的正是屏幕上已经显示的画面。这项检查需要两条线，因为历史中只有一条线时，两次按下都没有效果，问题就看不出来。这项检查在绘制之后进行，而不是在刚加载的页面上进行，因为没有操作对象的控件本来就不应该有反应。

如果第二条线什么都没画出来，这项检查就会通过，其证据中会写着这样一句。

```
the second line drew nothing, so there was no second step to undo
```

正确的 Undo 会把第一次按下用在那个空步骤上，这并不是落后一次。之前就有一个正常工作的绘图工具，因为第二笔没有画出来，被报告为 Undo 反应晚了一次。如果第二条线没有画出来，画布本身仍然会被报告（见[在画布上绘制](#drawing-on-a-canvas)）。

---

### <a id="games-and-animated-canvases"></a>游戏和动画画布

如果画布会自己播放动画，比如一个自动运行的游戏，assay 会等它停下来之后再操作。如果它一直不停，画布上的变化就无法归因于 assay 的任何操作，所以这些检查不要求发生变化。

已经自行停止的程序，比如撞墙后的贪吃蛇游戏，不会因为忽略之后的按键而被报告，因为这正是游戏在正常工作。例外情况是页面提示了要按什么。如果页面显示 *Press Space to restart*（按空格键重新开始），但按下空格键后什么都没变，说明页面违背了自己的提示，assay 报告如下。

```
    → the page says to press Space, but pressing Space changes nothing
```

没有重新开始功能的已结束游戏，仍然可能看起来像坏了，这一点列在 README 的局限说明中。

---

### <a id="dragging-handles-and-rows"></a>拖动手柄和行

分栏面板的分隔条和可拖动排序的行，点击时都不会有反应，所以 assay 会拖动它们：

- 每个拖动手柄（指针样式为 `col-resize`、`move` 或 `grab`）都会被拖动一次，并在第二项检查中被拖动两次。第二项检查只测量第二次拖动，因为分隔条最常见的故障就是移动一次之后再也抓不住，而如果把两次拖动放在一起测量，第一次拖动的效果就会掩盖第二次的问题。
- 每个 `draggable` 行都会被拖到所在列表的另一端，使用的是真实的 HTML5 拖放事件。之所以拖到另一端，是因为大多数列表会把行放在目标之前，所以把一行拖到相邻行上，它会回到原来的位置，看起来就像一个无法拖动的列表。

拖动应该会改变页面。如果没有改变，assay 报告如下。

```
C012 [FAILED] drag the divider, then drag it again
    → nothing on the page changed at all
```

---

### <a id="sliders-checkboxes-dropdowns-colours-and-files"></a>滑块、复选框、下拉框、颜色和文件

assay 会把每个滑块拖到最远的一端，勾选每个复选框和单选按钮，在每个下拉框中选择另一个选项，把每个取色器设为另一种颜色，并给每个文件输入框提供一个它所接受类型的小文件。

对于这些检查，assay 只报告页面抛出的错误，原因与按钮相同，它无法知道滑块或复选框应该改变什么。不过这些操作仍然算作使用了页面，[毫无响应](#a-page-where-nothing-responds)检查需要用到这一点。

---

### <a id="tabs-and-expandable-sections"></a>标签页和可展开区域

在每项检查中，assay 都会读取屏幕上的每个标签页和区域标题。标有 `aria-selected="true"` 或 `aria-expanded="true"` 的控件，是在告诉屏幕阅读器，它的 `aria-controls` 所指的面板正在显示。如果这个面板根本没有被渲染，页面就自相矛盾了，assay 报告如下。

```
F001 [FAILED] the panel a selected tab or open section controls is shown
    → "Tab 2" is marked selected and controls the panel "panel-1", but that panel isn't shown, first seen at C004
```

空面板仍然算作已显示，因为它在页面上占有一个盒子。只有浏览器完全没有渲染的面板才会被报告。

---

### <a id="labels-and-radio-buttons-in-the-markup"></a>HTML 中的 label 和单选按钮

在每项检查中，assay 还会读取 label 和单选按钮之间的关联方式，并报告三种光看页面发现不了的错误：

- 同一组中的两个单选按钮值相同，表单无法区分选中的是哪一个。

  ```
  F002 [FAILED] labels and radio buttons are linked correctly
      → two radio buttons in the "option" group both have the value "2", so the form can't tell which of them was picked, first seen at C001
  ```

- label 的 `for` 指向一个不存在的 id。

  ```
      → the label "Email" is linked to "emial", but nothing on the page has that id, first seen at C001
  ```

- 两个 label 关联到同一个控件，导致第二个 label 原本要关联的控件没有 label。

  ```
      → two labels are both linked to "star4", so one of them was meant for another control, which is left without a label, first seen at C001
  ```

---

### <a id="fields-whose-placeholder-fails-their-own-pattern"></a>占位符不符合自身 pattern 的输入框

assay 会读取所有同时带有 `pattern` 和占位符的输入框。如果输入框自己给出的示例都不符合它自己的 pattern，那么照着示例输入的人就无法提交需要这个输入框的表单。

```
F001 [FAILED] the zip box accepts its own placeholder example
    → the placeholder shows "12345" as an example, but the pattern on this field, \d{5}, rejects it, so someone who types what the example shows can't submit a form that requires this field
```

这个问题是从 HTML 中读出来的，而不是靠输入发现的，因为促成这条规则的那个输入框位于一个分步向导靠后的步骤中，检查根本到达不了。含有空格的占位符会被忽略，因为那是一句说明（*Enter five digits*，即输入五位数字），而不是示例值。

---

### <a id="nan-undefined-and-object-object-on-the-page"></a>页面上的 NaN、undefined 和 [object Object]

在每项检查中，assay 都会在可见文本和每个输入框中查找 `NaN`、`undefined` 和 `[object Object]`。没有哪个页面会有意显示这些内容。它们意味着某个值在赋值之前就被使用了，或者是用非数字的东西计算出来的。assay 报告如下。

```
F001 [FAILED] no NaN, undefined or [object Object] on the page
    → the page shows `NaN` where a value should be, "Total: NaN". This usually means a value was used before it was set, or calculated from something that isn't a number, first seen at C008
```

如果在某项检查中，是 assay 自己输入了非数字的内容，这项检查就不会报告这个问题。温度转换器收到 `Sample item` 后显示 `NaN` 是正确的，因为对于它被问到的问题，这就是正确答案。在这里，空输入框也算作数字。

---

### <a id="a-page-where-nothing-responds"></a>毫无响应的页面

由于单项检查不要求按钮必须产生效果，一个所有按钮都没有连接任何代码的页面会通过每一项检查。所以在运行结束时，assay 会针对整个页面提出这个问题。如果控件被使用过，而页面上什么都没变过，assay 报告如下。

```
C000 [FAILED] something on the page responds when used
    → nothing on the page changed after any control was used. 14 checks used what the page offers and none of them changed it, so the controls don't seem to be connected to any code
```

这条规则发现过一个看板应用，它的三个 Add 按钮都没有连接任何代码。由于这个问题等于判定整个页面有故障，所以只有同时满足以下条件时才会报告：

- 至少使用过两个不同的控件，
- 没有任何一项检查看到页面上的任何地方有变化，
- assay 操作到了页面上的每个控件。曾有一个可排序表格，它的可点击单元格被使用过，但排序表头没有被操作到，结果就被这样报告了，而它的排序功能完全正常。
- 重新打开页面并给它几秒钟而不是不到一秒的时间，这样重复三次后，页面仍然没有任何反应。如果一个页面的 Retry 会启动一个两秒的加载过程，那么在单项检查允许的时间内，它看起来就毫无反应。

---

## <a id="what-assay-cant-check"></a>assay 无法检查什么

assay 不知道一个控件应该做什么，所以能运行但做错了事的页面，比如总计算错的页面，通常都会通过检查。要检查控件应该做什么，请编写验收标准（acceptance criteria），并在 Python 中传入。`check(folder, criteria=[...])` 接受带有各自操作和预期结果的用例，并按所写的预期逐一检查。

---

本文是 [how-it-works.md](how-it-works.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
