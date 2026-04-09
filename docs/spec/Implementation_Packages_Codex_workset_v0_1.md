Implementation Packages / Codex workset

――――――――――――――――――――――――――――――――――――――――――

Документ №7B в комплекте документов торгового ядра

Версия	v0.1
Статус	Собрано по финально согласованному тексту
Текущий scope	Только Wave 1 / Minimal Core v1 implementation packages
Роль документа	Фиксирует package layer и правила сборки Codex workset первой реализации
Основание	Документы 1–7A комплекта и Technical Roadmap реализации

Документ открывает пакетный implementation-facing слой комплекта и описывает, как interface contracts первой реализации раскладываются на audit-friendly packages и как из них собирается Codex workset без выхода за границы Minimal Core v1.





1. Назначение документа

Документ «Implementation Packages / Codex workset» фиксирует implementation-facing слой, который следует непосредственно после документа 7A «Interface Contracts / Minimal Core v1» и переводит уже согласованные interface contracts в управляемую систему implementation packages. Если документ 7A отвечает на вопрос, какие интерфейсные швы существуют в первой реализации, то документ 7B отвечает на следующий вопрос: как эти швы раскладываются на рабочие пакеты реализации, в каком порядке они собираются и как из них формируется Codex workset для Minimal Core v1.

Назначение документа 7B уже и строже, чем у technical roadmap. Technical roadmap задаёт порядок инженерной сборки и зависимости между фазами, но сам по себе не раскладывает первую реализацию на audit-friendly рабочие пакеты. Из этого следует, что документ 7B работает только внутри phase-scoped среза Minimal Core v1: не как общий план реализации всего будущего ядра, а как управляемая разбивка именно первого vertical slice.

Документ 7B не создаёт новых доменных контрактов, не пересобирает governance-layer и не повторяет interface contracts 7A. Его задача другая: взять уже зафиксированные interface seams Minimal Core v1 и преобразовать их в такую package-map форму, при которой порядок реализации остаётся причинным, границы между пакетами не размываются, каждый пакет остаётся достаточно узким для аудита и Codex task не начинает незаметно пересекать несколько load-bearing seams сразу.

В этом документе слово «package» должно читаться не как папка в репозитории и не как удобный кусок кода по вкусу реализатора. Package здесь означает load-bearing единицу реализации, которая закрывает один или несколько already-agreed interface contracts, имеет собственный scope, dependency boundaries, done criteria, audit criteria и Codex task boundary.

Документ предназначен для архитектора реализации, аудитора Codex tasks и для следующего рабочего слоя после interface contracts. После его утверждения Minimal Core v1 должен иметь не только правильные interface seams, но и управляемую карту реализации, на которой уже можно строить package-by-package Codex workset без выхода за фазовую границу первой сборки.

2. Место документа в комплекте

Implementation Packages / Codex workset является документом №7B и следует непосредственно после документа 7A «Interface Contracts / Minimal Core v1». Такое положение в комплекте не является редакционным удобством. Оно отражает принципиальную логику перехода от conceptual layer к implementation layer.

Архитектурный roadmap ответил, каким должно быть ядро как система. Technical roadmap определил, в каком порядке это ядро собирается и какие способности реализуются первыми. Engineering Guardrails зафиксировал обязательные инженерные ограничения. Core Contracts закрепил canonical core truth model. Trading Governance добавил внешний policy-layer. Документ 7A затем определил, через какие interface seams собирается Minimal Core v1. Документ 7B появляется после этого и отвечает уже не на вопрос о смысле контрактов, а на вопрос о package decomposition первой реализации.

Из этого положения в комплекте вытекает критическая граница 7B. Он не заменяет собой technical roadmap: roadmap остаётся документом о фазах, зависимостях и done criteria на уровне сборки ядра в целом. 7B строится поверх него и использует его order of realization как обязательную опору, но остаётся package document. Точно так же 7B не заменяет собой 7A: interface contracts уже определили load-bearing seams первой реализации, и package layer не имеет права заново переопределять эти швы на более удобном языке.

Связь 7B с 7A должна читаться асимметрично. Документ 7A уже ответил, какие интерфейсные границы существуют. Документ 7B не имеет права заново спорить о том, существуют ли эти швы и где они проходят. Его задача уже строже: сгруппировать их в такие implementation packages, которые можно реализовывать, проверять и аудировать последовательно, не разрушая согласованную causal chain Minimal Core v1.

Итоговое место документа в комплекте таково: 7B является вторым implementation-facing документом после 7A и завершает переход от interface contracts к рабочей package map первой реализации. Он не канонизирует структуру репозитория, не заменяет roadmap и не создаёт новые domain contracts; он организует первую реализацию Minimal Core v1 в форме audit-friendly implementation packages and Codex workset.

3. Scope и phase boundary

3.1. Что входит в scope документа

В scope документа 7B входят только те implementation packages, которые нужны для сборки Minimal Core v1 как первого исполнимого vertical slice. Это не произвольное решение, а прямое следствие technical roadmap. В scope первой реализации уже входят: базовые доменные модели и normalised event flow; minimal MTF input seam для первой MTF-стратегии; Strategy Contract; Risk engine; Order Builder и Pre-execution Guard; Execution Boundary; fill / position / portfolio spine; State Store; Startup Reconciliation и формальный recovery contour первого запуска.

Для документа 7B этого достаточно сформулировать прямо: в его scope входят следующие package-зоны Minimal Core v1 — input and context foundation; strategy decision boundary; risk verdict boundary; order construction layer; execution boundary; fill-driven state spine; persistence and startup readiness. Эти package-зоны не произвольны: они следуют либо из Wave 1 block-set technical roadmap, либо из уже зафиксированных interface contracts 7A, либо из той causal chain, которую roadmap и architecture требуют для первого working contour.

3.2. Что не входит в scope документа

В документ 7B не входят implementation packages следующих фаз. Full TimeframeContext, Context Gate, explicit unknown-state model, periodic reconciliation, on-error reconciliation, broader source-of-truth policy и position-originated close routing contour относятся к следующему этапу. Они могут быть упомянуты только как future seams, чтобы первая реализация не зацементировала свою раннюю форму как окончательную архитектуру.

В 7B также не входят hardening tasks. Idempotent fill processing, atomic state persistence, structured logging, mock adapters, correctness tests и fault scenarios уже вынесены technical roadmap в отдельный hardening-layer. Поэтому документ 7B не должен превращаться ни в hardening backlog, ни в boundary-test plan.

Наконец, в scope 7B не входят multi-instrument readiness, multi-strategy readiness, multi-exchange abstraction, derivatives expansion и иные расширения beyond Minimal Core v1. Package layer 7B не должен раздуваться пакетами «на вырост», которые пока не имеют права считаться частью первого Codex workset.

3.3. Phase boundary документа

Критическая phase boundary документа 7B состоит в следующем: он описывает implementation packages только для первой реализации Minimal Core v1, но не имеет права превращать временную форму этой первой реализации в постоянный закон всего будущего ядра. Assembly-level compromises первой сборки допустимы, но не канонизируются как invariants ядра.

Из этой границы вытекает основной принцип package decomposition. Каждый package документа 7B должен описываться как phase-scoped единица реализации, а не как «естественная окончательная папка проекта». Package существует потому, что в текущем Minimal Core v1 есть конкретный load-bearing seam, который нужно реализовать и потом отдельно аудировать. Поэтому package layer 7B должен следовать interface seams 7A и order of realization technical roadmap, а не внутренней эстетике файловой структуры.

3.4. Критическая граница документа

Критическая граница 7B такова: документ описывает package layer первой реализации, но не подменяет собой ни domain layer, ни interface layer, ни governance, ни engineering hardening. Он не создаёт новые canonical objects, не переопределяет interface contracts 7A, не описывает полную reconciliation-family следующего этапа, не превращается в структуру репозитория и не задаёт точные class signatures.

Его задача одна: зафиксировать такие implementation packages, которые позволяют собрать Minimal Core v1 в правильном порядке, с правильными границами и с правильной пригодностью к аудиту и Codex execution.

3.5. Итог раздела

Scope документа 7B ограничен implementation packages Minimal Core v1 и строго следует фазовой логике technical roadmap. В него входят только те package-зоны, которые нужны для первого vertical slice: input/context foundation, strategy decision boundary, risk verdict boundary, order construction, execution boundary, fill-driven state spine, persistence and startup readiness. Package families следующего этапа, hardening-layer и более поздние расширения сюда не входят. Такая phase boundary делает 7B пригодным для первого Codex workset и одновременно не позволяет случайно превратить первую сборку в окончательную карту реализации всего будущего ядра.

4. Формат описания каждого implementation package

4.1. Назначение единого формата

Документ №7B должен описывать implementation packages не как произвольный перечень работ разной глубины, а как строго повторяемую рабочую форму. Это нужно затем, чтобы каждый package можно было одинаково читать, реализовывать и аудировать, а package layer не распадался на смесь prose-описаний, локальных todo-list и скрытых предположений о том, что именно считается готовым.

4.2. Формат package layer не подменяет interface contracts и не превращается в структуру репозитория

Package format документа 7B не должен подменять собой interface contracts 7A. Документ 7A уже определил load-bearing seams первой реализации; документ 7B не имеет права заново переопределять их на более удобном языке пакетов. Его задача уже: сгруппировать согласованные interface contracts в audit-friendly implementation units.

Точно так же package format не должен превращать документ в описание файловой структуры. Implementation package определяется по load-bearing seam реализации, а не по папке, файлу или удобству импортов.

4.3. Обязательные элементы описания каждого implementation package

Для каждого implementation package документа №7B должны быть зафиксированы следующие обязательные элементы: роль пакета; какие interface contracts из 7A пакет закрывает; scope пакета; что не входит в пакет; upstream dependencies; downstream dependencies; done criteria; audit criteria; Codex task boundary.

Именно эта девятичастная схема должна применяться ко всем пакетам разделов 6–12.

4.4. Роль блока Scope / Out-of-scope

Из всех элементов package format особое значение имеет связка Scope / Out-of-scope. Scope нужен затем, чтобы пакет имел чёткую рабочую форму. Out-of-scope нужен затем, чтобы пакет не превратился в расплывчатую зону ответственности и не начал «для удобства» подтягивать future seams следующего этапа или hardening-specific work.

4.5. Роль dependency blocks

Package format должен отдельно фиксировать upstream и downstream dependencies, потому что package layer строится не как плоский список работ, а как causal order реализации Minimal Core v1. Dependency blocks защищают 7B от ложной параллельности и от соблазна начинать пакет раньше времени только потому, что часть кода можно написать заранее.

4.6. Роль done criteria и audit criteria

Каждый implementation package должен иметь не только done criteria, но и audit criteria. Done criteria отвечают на вопрос: когда пакет можно считать реализованным в достаточной степени для Minimal Core v1. Audit criteria отвечают на другой вопрос: можно ли подтвердить, что пакет реализован правильно по границам, а не просто работает локально.

4.7. Роль блока Codex task boundary

Документ 7B существует в том числе ради последующего перехода к Codex workset, поэтому каждый package должен иметь явный Codex task boundary. Уже на уровне package description должно быть понятно: можно ли реализовывать пакет одной задачей; нужно ли делить его на подзадачи; какая часть пакета должна считаться protected scope; какие соседние пакеты не должны быть затронуты этой задачей.

4.8. Единый формат не означает одинаковый объём всех пакетов

Хотя структура описания у всех packages одна, это не означает, что все пакеты должны иметь одинаковый объём текста или одинаковую реализационную массу. Единый формат означает одинаковую структуру чтения, а не одинаковое количество абзацев.

4.9. Итог раздела

Каждый implementation package документа 7B должен описываться по единой рабочей схеме. Такой формат не подменяет собой interface contracts, не превращается в структуру репозитория и не смешивает package layer с roadmap или hardening. Он делает package document пригодным для последовательного раскрытия Package A–G как управляемых единиц первой реализации Minimal Core v1.

5. Общие правила package layer

5.1. Package layer является фазовым слоем Minimal Core v1

Общие правила package layer должны читаться как правила первой реализации, а не как универсальная схема пакетизации всего будущего ядра. Package layer документа 7B обязан быть phase-scoped: он должен быть достаточно конкретным для первой реализации и достаточно сдержанным, чтобы не подтянуть в active package scope contract families следующего этапа.

5.2. Пакеты строятся по load-bearing seams, а не по папкам и файлам

Главное общее правило package layer состоит в том, что implementation packages определяются по несущим швам реализации, а не по структуре репозитория. Пакет существует потому, что в Minimal Core v1 есть отдельный load-bearing seam, который должен быть реализован и затем отдельно аудирован.

5.3. Package не подменяет собой interface contract

Документ 7A уже определил, какие interface contracts существуют в первой реализации. Следовательно, ни один package документа 7B не имеет права заново переопределять смысл этих швов на языке локального удобства. Package layer обязан опираться на interface layer, а не переписывать его.

5.4. Package должен быть достаточно узким для аудита и достаточно цельным для реализации

Каждый implementation package должен удерживать два требования одновременно: быть достаточно узким для честного аудита и достаточно цельным для meaningful implementation result. Если пакет слишком широк, он начнёт поглощать соседние seams. Если слишком мелок — перестанет быть meaningful unit of implementation.

5.5. Пакет не имеет права обходить уже согласованные зависимости

Package layer работает не с абстрактной архитектурой, а с реальной sequence of implementation. Поэтому пакет не имеет права стартовать так, будто его upstream dependencies уже не важны, и не имеет права выходить downstream в обход ещё неготового соседнего пакета.

5.6. Один package не должен незаметно поглощать другой

Package layer должен сохранять читаемость границ между пакетами. Если один пакет при реализации начинает брать на себя соседний seam, документ 7B теряет смысл. Это особенно критично между Strategy и Risk; между Risk и Order Construction; между Order Builder и Pre-execution Guard; между Execution Boundary и fill-driven state spine.

5.7. Package layer обязан сохранять fill-driven и execution-boundary дисциплину

Два load-bearing ограничения комплекта должны сохраняться и на уровне пакетов: execution must stay behind interface, а state spine must stay fill-driven. Ни один package не должен проектироваться так, будто execution adapter можно трогать из нескольких зон сразу или будто state spine можно сокращать, минуя Fill Processor, Position Engine или Portfolio Engine.

5.8. Package layer не подменяет собой hardening

Документ 7B не должен превращаться в скрытый hardening backlog. Он описывает только реализационные пакеты Minimal Core v1, а не следующий инженерный пакет укрепления системы.

5.9. Package layer должен быть пригоден для Codex workset

Пакет должен описываться так, чтобы по нему можно было сформировать либо одну задачу, либо небольшой набор подзадач без разрушения его внутренней границы. Это особенно важно для Package F и Package G.

5.10. Общие правила package layer не заменяют собой audit gates

Хотя package layer требует done criteria и audit criteria для каждого пакета, эти критерии не заменяют собой cross-package gates следующего раздела. У пакета есть собственная готовность. У перехода между пакетами есть собственное право начинаться или не начинаться.

5.11. Итог раздела

Package layer документа 7B является фазовым слоем Minimal Core v1 и подчиняется нескольким жёстким общим правилам: пакеты строятся по load-bearing seams, не подменяют interface contracts, не обходят зависимости, не молча поглощают соседние seams, сохраняют execution boundary и fill-driven spine, не превращаются в hardening backlog и остаются пригодными для Codex workset.

6. Package A — Input and Context Foundation

6.1. Роль пакета

Package A фиксирует первую load-bearing единицу реализации Minimal Core v1: входной и ранний контекстный фундамент, на котором затем строятся все downstream packages. Сначала ядро получает базовые доменные модели и normalised event flow, а затем — minimal MTF input seam для первой MTF-стратегии.

Роль этого пакета состоит в том, чтобы дать ядру два базовых implementation seams одновременно: единый нормализованный вход рыночного события и минимальный MTF-ready input seam для первой стратегии. Без этого Package B не имеет честного права начинаться, потому что Strategy Contract не может быть реализован без допустимого normalized market/context input, проходящего через ядро.

6.2. Какие interface contracts из 7A пакет закрывает

Package A закрывает раздел 6 документа 7A — Normalized Event Input Contract и раздел 7 документа 7A — Minimal MTF Input Seam Contract. Это делает его первым implementation package всего документа 7B.

6.3. Scope пакета

В scope Package A входят реализация единого normalized event input seam как первой strategy-facing входной формы ядра; реализация раннего MTF-ready seam для первой мультитаймфреймной стратегии; обеспечение того, что первая стратегия получает entry-timeframe basis и обязательные HTF inputs через ядро, а не через локальную сборку в strategy layer.

Также в scope пакета входят closed-bar only и no-look-ahead semantics в минимально достаточном объёме первой реализации и формирование такого input/context foundation, который downstream Package B уже имеет право читать как допустимый strategy input.

6.4. Что не входит в пакет

В Package A не входят:

	полноценный TimeframeContext как зрелая contract family;

	ContextAssembler, Context Gate, BarAlignmentPolicy, ClosedBarPolicy и FreshnessPolicy как first-class contracts следующего этапа;

	periodic и on-error reconciliation;

	unknown-state family;

	strategy logic как таковая;

	risk verdict, order construction, execution boundary и downstream state spine;

	hardening-specific testability, observability и fault-injection work.

6.5. Upstream dependencies

Package A не имеет upstream dependency на другие implementation packages 7B, потому что он открывает package layer. Однако у него есть обязательные upstream constraints из already-agreed documents: он обязан следовать canonical domain meaning MarketEvent и раннего MTF input seam, архитектурной границе «сначала домен, потом адаптеры» и phase-scoped границе первой реализации.

Именно поэтому Package A стартует первым: все остальные пакеты зависят от результата его реализации, но сам он зависит только от уже согласованного комплекта, а не от соседних implementation packages.

6.6. Downstream dependencies

Результат Package A является обязательным upstream basis как минимум для Package B — Strategy Decision Boundary, потому что стратегия должна получать уже допустимый normalized market/context input через ядро.

Косвенно Package A открывает путь для всех downstream packages, потому что без первой strategy-facing границы невозможно честно собрать ни Risk, ни Order Construction, ни Execution, ни fill-driven spine.

6.7. Done criteria

Package A считается реализованным для Minimal Core v1, если:

	внешний market-data input проходит в ядро через единый normalized event seam;

	первая MTF-стратегия получает entry-timeframe basis и обязательные HTF inputs через ядро;

	strategy layer не вынужден локально собирать HTF admissibility;

	minimal input/context foundation уже достаточен для честного начала Package B;

	ранний MTF seam удерживает closed-bar only и no-look-ahead semantics в объёме, требуемом первой стратегии;

	package не раскрывает full TimeframeContext family раньше времени.

6.8. Audit criteria

Package A проходит аудит, если можно подтвердить:

	normalised input seam действительно существует как отдельный implementation seam, а не спрятан внутри strategy code;

	первая стратегия не собирает HTF context локально;

	input/context foundation не тащит в себя strategy logic, risk logic или execution concerns;

	пакет не маскирует full TimeframeContext и Context Gate под временную реализацию Wave 1;

	downstream Package B сможет использовать результат Package A без adapter-specific knowledge.

6.9. Codex task boundary

Package A может быть реализован либо одной задачей Codex, либо двумя тесно связанными подзадачами A1 / A2, где A1 закрывает normalized event input, а A2 — minimal MTF input seam поверх уже готового normalized input.

Даже при внутреннем делении boundary пакета остаётся единой: обе задачи принадлежат одному package scope, не затрагивают Strategy, Risk или следующий этап MTF family и завершаются единым package-level аудитом.

6.10. Итог раздела

Package A — это Input and Context Foundation первой реализации. Он закрывает два первых interface contracts из 7A, создаёт минимально достаточный strategy-facing input/context basis для всего остального vertical slice Minimal Core v1 и служит обязательным upstream foundation для Package B.

7. Package B — Strategy Decision Boundary

7.1. Роль пакета

Package B фиксирует следующую load-bearing единицу реализации Minimal Core v1: отдельный strategy-facing decision layer, который получает допустимый market/context input из ядра и возвращает только формальный strategy-side result первого decision step.

Роль этого пакета состоит в том, чтобы сделать strategy layer отдельной реализуемой boundary-зоной, а не размазанной логикой между input foundation, risk layer и runtime orchestration. Package B замыкает только один шов: превращение already-admissible input/context basis в StrategyIntent либо explicit no-action result.

7.2. Какие interface contracts из 7A пакет закрывает

Package B закрывает раздел 8 документа 7A — Strategy Contract. Он отвечает не за стратегии вообще, а за реализацию конкретного interface seam, уже согласованного в 7A.

7.3. Scope пакета

В scope Package B входят реализация strategy-facing boundary как отдельного слоя между input/context foundation и Risk Contract; приём допустимого normalized market/context input только через already-agreed upstream seams Package A; формирование formal StrategyIntent либо explicit no-action result.

Также в scope входит удержание separation between strategy decision logic и downstream risk/execution/state concerns и подготовка такого strategy-side result, который Package C уже имеет право читать как единственный допустимый upstream decision basis.

7.4. Что не входит в пакет

В Package B не входят:

	локальная сборка market/context input в обход Package A;

	RiskDecision и любой risk-layer admissibility verdict;

	order construction, Pre-execution Guard и execution boundary;

	fill, position, portfolio, persistence and startup reconciliation paths;

	regime-aware strategy orchestration, multi-strategy family и другие расширения beyond Minimal Core v1;

	full TimeframeContext family, Context Gate и иные context-admission contract families следующего этапа.

7.5. Upstream dependencies

Package B имеет одну обязательную upstream dependency: Package A — Input and Context Foundation. Без готового normalized event seam и без раннего MTF-ready seam первая стратегия не получает допустимого input/context basis через ядро.

Кроме того, Package B зависит от already-agreed boundary discipline документов 1–7A: стратегия должна читать только допустимый input, уже нормализованный ядром, не является source of truth для HTF admissibility и не зависит от adapter, state store и portfolio accounting.

7.6. Downstream dependencies

Результат Package B является обязательным upstream basis для Package C — Risk Verdict Boundary, потому что Risk Contract зависит только от StrategyIntent, instrument rules и PortfolioState и не должен получать implicit strategy approval вместо формального decision result.

Косвенно Package B открывает путь для всего последующего decision pipeline, но его ближайшая и единственная непосредственная downstream зависимость — именно Package C.

7.7. Done criteria

Package B считается реализованным для Minimal Core v1, если:

	strategy layer получает только допустимый normalized market/context input через ядро;

	strategy layer существует как отдельная decision boundary, а не как локальная логика внутри input layer или risk layer;

	output strategy layer формализован как StrategyIntent либо explicit no-action result;

	strategy layer не обращается напрямую к adapter, state store и portfolio accounting;

	первая MTF-стратегия проходит через этот boundary без локальной сборки context в strategy layer.

7.8. Audit criteria

Package B проходит аудит, если можно подтвердить:

	Strategy Decision Boundary реализован как отдельный package seam, а не растворён между input foundation и risk logic;

	strategy output действительно остаётся только на уровне StrategyIntent / no-action и не несёт risk/execution semantics;

	strategy layer не знает adapter-specific input format и не требует прямого доступа к persistence или portfolio paths;

	первая стратегия использует результат Package A как вход ядра, а не восстанавливает себе локальный обход input/context seams;

	Package C сможет принять output Package B без скрытых межслойных предположений.

7.9. Codex task boundary

Package B в нормальном случае должен быть одной задачей Codex, потому что он закрывает один load-bearing seam и не требует внутреннего дробления по типу Package F.

Его boundary должен быть protected: задача начинается только после готовности Package A и не должна затрагивать Risk, Order Construction, Execution Boundary и downstream state spine.

7.10. Итог раздела

Package B — это Strategy Decision Boundary Minimal Core v1. Он закрывает Strategy Contract из 7A, получает допустимый input/context basis только из Package A, формирует только StrategyIntent либо explicit no-action result и служит единственным непосредственным upstream основанием для Package C.

8. Package C — Risk Verdict Boundary

8.1. Роль пакета

Package C фиксирует следующую load-bearing единицу реализации Minimal Core v1: отдельный риск-слой как downstream verdict boundary между Strategy Decision Boundary и order construction layer.

Роль этого пакета состоит в том, чтобы сделать risk layer отдельной реализуемой boundary-зоной, а не неявной проверкой вокруг уже готового order action. Package C замыкает только один шов: превращение strategy-side decision result в formal RiskDecision.

8.2. Какие interface contracts из 7A пакет закрывает

Package C закрывает раздел 9 документа 7A — Risk Contract. Он отвечает именно за реализацию отдельной risk verdict boundary, уже согласованной в 7A.

8.3. Scope пакета

В scope Package C входят реализация отдельного risk boundary downstream от Strategy Contract; чтение StrategyIntent как единственного допустимого upstream decision basis; чтение instrument rules / instrument specs и актуального PortfolioState в том объёме, который нужен для risk-reading текущего contour.

Также в scope входит формирование formal RiskDecision как отдельного downstream verdict result и удержание границы между risk admissibility и последующим order construction.

8.4. Что не входит в пакет

В Package C не входят:

	strategy-side формирование Decision / StrategyIntent;

	OrderIntent и любой order construction logic;

	price/qty rounding, min_qty / min_notional и иная execution-facing admissibility, принадлежащая Pre-execution Guard;

	execution boundary и любые adapter-specific interactions;

	fill-driven state spine, persistence boundary и startup reconciliation;

	governance-level trade admission, environment restrictions и posture semantics;

	расширенные risk families следующих фаз: multi-strategy allocation, regime-aware risk orchestration, derivatives-ready risk policies.

8.5. Upstream dependencies

Package C имеет обязательную upstream dependency на Package B — Strategy Decision Boundary, потому что Risk Contract может стартовать только после появления formal StrategyIntent как upstream decision result.

Он также зависит от already-agreed boundary discipline: risk layer не формирует market-data input, не читает execution adapter напрямую и не мутирует позицию.

8.6. Downstream dependencies

Результат Package C является обязательным upstream basis для Package D — Order Construction Layer, потому что Order Builder имеет право строить OrderIntent только downstream от approved RiskDecision.

Косвенно Package C открывает путь для всех следующих execution-facing пакетов, поскольку без отдельного risk verdict causal chain Minimal Core v1 остаётся нарушенной.

8.7. Done criteria

Package C считается реализованным для Minimal Core v1, если:

	StrategyIntent проходит через отдельный risk boundary, а не попадает напрямую в order construction;

	risk layer использует только допустимый upstream basis: StrategyIntent, instrument rules и PortfolioState;

	результат risk layer формализован как отдельный RiskDecision;

	downstream Package D может читать этот результат как единственное допустимое основание для order construction;

	risk layer не зависит от execution adapter и не вмешивается в position / portfolio mutation paths.

8.8. Audit criteria

Package C проходит аудит, если можно подтвердить:

	Risk Verdict Boundary реализован как отдельный package seam, а не растворён внутри Strategy Contract или Order Builder;

	RiskDecision действительно остаётся отдельным verdict layer, а не превращается в скрытый OrderIntent;

	risk layer не выполняет execution-facing checks, принадлежащие Pre-execution Guard;

	risk layer не знает execution adapter и не вмешивается в downstream state ownership;

	Package D сможет начать свою работу без повторного risk-reading и без скрытых предположений о strategy-side admissibility.

8.9. Codex task boundary

Package C в нормальном случае должен быть одной задачей Codex, потому что он закрывает один load-bearing seam и не требует внутреннего разбиения.

Если для реализации потребуется внутренняя декомпозиция, она должна оставаться внутри одного package scope и не превращать Package C в смешанную задачу «strategy + risk + order construction».

8.10. Итог раздела

Package C — это Risk Verdict Boundary Minimal Core v1. Он закрывает Risk Contract из 7A, получает StrategyIntent from Package B как единственный допустимый upstream decision basis, формирует только formal RiskDecision и служит обязательным upstream основанием для Package D.

9. Package D — Order Construction Layer

9.1. Роль пакета

Package D фиксирует следующую load-bearing единицу реализации Minimal Core v1: order construction layer как связанный, но внутренне разделённый пакет между Risk Verdict Boundary и Execution Boundary.

Роль Package D состоит в том, чтобы реализовать один связанный execution-facing слой, но с жёстким внутренним разведением двух швов: builder строит OrderIntent из approved RiskDecision, а guard проверяет, остаётся ли уже построенный OrderIntent допустимым к переходу во внешний execution contour.

9.2. Какие interface contracts из 7A пакет закрывает

Package D закрывает раздел 10.1 документа 7A — Order Builder Contract и раздел 10.2 документа 7A — Pre-execution Guard Contract. Это означает, что пакет deliberately объединяет два соседних interface seams в одну implementation unit, но не сливает их смысл.

9.3. Scope пакета

В scope Package D входят реализация отдельного Order Builder boundary downstream от RiskDecision; формирование OrderIntent только из approved RiskDecision; реализация отдельного Pre-execution Guard как execution-facing gate между OrderIntent и внешним execution boundary.

Также в scope входят venue-facing checks в объёме, согласованном для Minimal Core v1: price/qty rounding по instrument spec, min_qty / min_notional, совместимость типа ордера с execution capabilities и формальный reject-state, если поручение после этих ограничений перестаёт быть исполнимым.

9.4. Что не входит в пакет

В Package D не входят:

	StrategyIntent и strategy-side decision logic;

	RiskDecision как upstream verdict layer;

	execution adapter и любая внешняя execution interaction;

	Fill Processor, Position Engine, Portfolio Engine, State Store и Startup Reconciliation;

	governance-level trade admission, restriction и posture semantics;

	сложные child orders, OCO, ladder exits и иные продвинутые execution policies за пределами minimal core v1;

	mature position-originated close routing contour следующего этапа.

Отдельно важно зафиксировать: в Package D не входит повторная risk-оценка уже одобренного решения. Execution-facing admissibility не должна маскироваться под «ещё один risk-слой».

9.5. Upstream dependencies

Package D имеет обязательную upstream dependency на Package C — Risk Verdict Boundary, потому что Order Builder строит OrderIntent только из approved RiskDecision.

Кроме того, он опирается на already-agreed boundary discipline: OrderIntent не равен Order; между OrderIntent и внешней order reality существует отдельная admission boundary; Pre-execution Guard появляется раньше передачи OrderIntent в execution boundary.

9.6. Downstream dependencies

Результат Package D является обязательным upstream basis для Package E — Execution Boundary, потому что execution boundary имеет право получать только уже построенный и прошедший execution-facing gate result.

Косвенно Package D открывает путь для всего fill-driven state spine, потому что без корректного order construction step causal chain Minimal Core v1 рвётся уже до внешнего execution contour.

9.7. Done criteria

Package D считается реализованным для Minimal Core v1, если:

	approved RiskDecision является единственным допустимым upstream basis для order construction;

	Order Builder существует как отдельный внутренний seam и формирует formal OrderIntent;

	Pre-execution Guard существует как отдельный execution-facing gate между OrderIntent и execution boundary;

	guard не пересчитывает risk verdict, а проверяет только downstream admissibility для перехода во внешний execution contour;

	ни одно поручение не уходит в Package E без прохождения через builder и guard;

	invalid OrderIntent получает формальный reject result до handoff во внешний execution boundary.

9.8. Audit criteria

Package D проходит аудит, если можно подтвердить:

	builder и guard действительно реализованы как два разных внутренних шва одного пакета, а не как неразмеченный смешанный слой;

	builder и guard остаются разными responsibility boundaries: builder не подменяет собой execution-facing admissibility и не вызывает guard как скрытую часть собственного смысла, а guard не строит OrderIntent и не принимает на себя role order-construction layer;

	OrderIntent не возникает напрямую из StrategyIntent или implicit strategy approval;

	guard не подменяет Risk Contract и не становится вторым risk-check;

	execution boundary не получает поручения в обход guard;

	пакет не тянет в себя execution adapter, downstream fill/state spine и governance semantics;

	Package E сможет принять результат Package D без повторного order construction или скрытого venue-admissibility logic.

9.9. Codex task boundary

Package D может быть реализован либо одной задачей Codex, если builder и guard сохраняют внутреннее разведение, но помещаются в один связный package scope, либо двумя тесно связанными подзадачами D1 / D2, где D1 закрывает Order Builder, а D2 закрывает Pre-execution Guard поверх уже готового OrderIntent path.

При этом boundary пакета остаётся единой: обе подзадачи принадлежат одному package scope, D2 не имеет права перетекать в Package E, а ни D1, ни D2 не должны тянуть в себя Risk layer или downstream execution/state spine.

9.10. Итог раздела

Package D — это Order Construction Layer Minimal Core v1. Он закрывает два interface contracts из 7A — Order Builder Contract и Pre-execution Guard Contract — и реализует их как один связанный package с жёстким внутренним разведением. Builder превращает approved RiskDecision в OrderIntent. Guard отдельно проверяет execution-facing admissibility этого OrderIntent перед handoff в Package E.

10. Package E — Execution Boundary

10.1. Роль пакета

Package E фиксирует одну из самых нагруженных единиц реализации Minimal Core v1: единственную формальную boundary-точку связи ядра с внешним execution adapter.

Роль Package E состоит в том, чтобы сделать execution interaction одним строго контролируемым seam, а не распылённым доступом к внешнему миру из нескольких внутренних слоёв. Он принимает только уже допущенный downstream result из Package D, выпускает наружу formal execution interaction и возвращает внутрь ядра только нормализованный execution-side result.

10.2. Какие interface contracts из 7A пакет закрывает

Package E закрывает раздел 11 документа 7A — Execution Boundary Contract. Он отвечает именно за реализацию единственного formal execution boundary первой реализации.

10.3. Scope пакета

В scope Package E входят реализация единственной formal boundary-точки связи ядра с execution adapter; приём только уже допущенного downstream result из Package D; outbound handoff во внешний execution contour только через один contract boundary; inbound normalisation execution-side responses до уровня ExecutionReport / Fill-side result, пригодного для downstream Fill Processor.

Также в scope входят удержание fill-driven causal chain и обеспечение того, что adapter может быть заменён без переписывания доменной логики strategy / risk / state spine.

10.4. Что не входит в пакет

В Package E не входят:

	StrategyIntent и strategy-side decision logic;

	RiskDecision и любая risk-level admissibility;

	Order Builder и Pre-execution Guard как order construction layer;

	Fill Processor, Position Engine, Portfolio Engine, State Store и Startup Reconciliation;

	governance-level admission, restriction и posture semantics;

	periodic / on-error reconciliation и recovery-sensitive execution family следующего этапа;

	multi-exchange abstraction и расширенные execution capability families beyond Minimal Core v1;

	hardening-specific boundary tests, mock/failure-injection family и industrial boundary observability.

10.5. Upstream dependencies

Package E имеет обязательную upstream dependency на Package D — Order Construction Layer, потому что execution boundary имеет право получать только уже построенный и прошедший Pre-execution Guard result.

Кроме того, он опирается на already-agreed boundary discipline: execution существует только behind interface; OrderIntent не равен внешнему Order; вход во внешний execution contour возможен только через отдельную admission boundary.

10.6. Downstream dependencies

Результат Package E является обязательным upstream basis для Package F — Fill-Driven State Spine, потому что Fill Processor имеет право получать только нормализованный execution-side result, а не сырой adapter payload.

Косвенно Package E открывает путь для всего downstream state path, потому что без корректного execution boundary не существует честного перехода к fill-driven position and portfolio truth.

10.7. Done criteria

Package E считается реализованным для Minimal Core v1, если:

	в ядре существует одна и только одна formal boundary-точка связи с execution adapter;

	никакой внутренний слой Minimal Core v1 не обращается к execution adapter в обход Package E;

	outbound execution interaction стартует только после Package D и не требует повторного order construction внутри boundary;

	inbound execution-side responses нормализуются до уровня ExecutionReport / Fill-side result before downstream handoff;

	downstream Package F получает уже нормализованный execution-side result без vendor-specific knowledge;

	замена adapter не требует переписывания strategy logic, risk layer и fill-driven spine.

10.8. Audit criteria

Package E проходит аудит, если можно подтвердить:

	Execution Boundary действительно является единственной точкой связи ядра с внешним execution adapter;

	ни Strategy, ни Risk, ни Order Construction, ни Fill / Position / Portfolio layers не имеют параллельного доступа к execution adapter;

	boundary contract не содержит strategy logic, risk logic или portfolio/accounting logic;

	в ядро не протекает сырой vendor-specific payload как будто это уже доменная сущность;

	downstream Package F получает нормализованный execution-side result и не вынужден сам интерпретировать transport-level details;

	Package E не мутирует PositionState, PortfolioState или persistence boundary напрямую.

10.9. Codex task boundary

Package E в нормальном случае должен быть одной задачей Codex, потому что он закрывает один load-bearing seam и не должен дробиться без сильной причины.

Его boundary должен быть protected: задача начинается только после готовности Package D, не должна затрагивать downstream state spine beyond formal handoff и не должна расширяться до full recovery/reconciliation execution family следующего этапа.

10.10. Итог раздела

Package E — это Execution Boundary Minimal Core v1. Он закрывает Execution Boundary Contract из 7A, принимает только already-admitted result из Package D, остаётся единственной допустимой точкой связи ядра с внешним execution adapter, возвращает внутрь ядра только нормализованный execution-side result и служит обязательным upstream основанием для Package F.

11. Package F — Fill-Driven State Spine

11.1. Роль пакета

Package F фиксирует самый широкий и один из самых нагруженных implementation packages Minimal Core v1: центральный downstream state spine, через который execution-side truth превращается во внутреннюю truth-chain позиции и портфеля.

Роль Package F состоит в том, чтобы реализовать один связанный fill-driven spine, но с жёстким внутренним порядком трёх downstream layers: F1 — Fill Processor, F2 — Position Engine, F3 — Portfolio Engine. Этот пакет deliberately остаётся одним логическим package, потому что все три слоя образуют одну причинную цепочку state mutation.

11.2. Какие interface contracts из 7A пакет закрывает

Package F закрывает раздел 12.1 документа 7A — Fill Processor Contract, раздел 12.2 — Position Engine Contract и раздел 12.3 — Portfolio Engine Contract. На package level это один state spine; на internal seam level это три разных owner-managed boundaries.

11.3. Scope пакета

В scope Package F входят реализация downstream path от нормализованного execution-side result к processed fill basis; реализация downstream position mutation только через Fill Processor; реализация downstream portfolio/accounting aggregation только после обновления позиции.

Также в scope входят удержание единого truth flow «Execution Boundary → Fill Processor → Position Engine → Portfolio Engine», подготовка такого aggregate state result, который Package G уже имеет право читать как persistence/startup basis, и реализация внутренних переходов F1 → F2 → F3 с явными acceptance conditions между слоями.

11.4. Что не входит в пакет

В Package F не входят:

	StrategyIntent, RiskDecision, OrderIntent и order construction logic;

	execution adapter и любой внешний execution interaction beyond already-normalized handoff from Package E;

	persistence boundary как таковая;

	startup reconciliation и вся более широкая reconciliation family;

	governance-level admission, restriction, posture and resume semantics;

	hardening-specific idempotency family, replay/fault-injection family и industrial observability layer;

	mature position-originated close routing contour следующего этапа;

	broader unknown-state family как first-class contract layer.

11.5. Upstream dependencies

Package F имеет обязательную upstream dependency на Package E — Execution Boundary, потому что Fill Processor имеет право получать только уже нормализованный execution-side result, а не сырой adapter payload.

Кроме того, пакет зависит от already-agreed state ownership discipline: состояние обновляется по факту исполнения; fill truth предшествует position truth; position truth предшествует portfolio truth; владение изменениями состояния не расползается между несколькими местами.

11.6. Downstream dependencies

Результат Package F является обязательным upstream basis для Package G — Persistence and Startup Readiness, потому что State Store имеет право читать только уже сформированный downstream state result, а не отдельно execution facts, позицию и портфель в разорванном виде.

Косвенно Package F открывает путь для startup readiness всей первой реализации, потому что без готового fill-driven state spine persistence boundary и startup reconciliation не имеют честного state object для restore path.

11.7. Done criteria

Package F считается реализованным для Minimal Core v1, если:

	execution-side result from Package E попадает в отдельный Fill Processor seam;

	PositionState изменяется только downstream от Fill Processor;

	PortfolioState агрегируется только downstream от Position Engine;

	ни один слой пакета не обходит внутренний порядок F1 → F2 → F3;

	итоговый state result уже достаточен для Package G как persistence/startup basis;

	state ownership остаётся читаемым: Fill Processor владеет только fill-processing step, Position Engine — только position mutation step, Portfolio Engine — только portfolio aggregation step.

Отдельно для внутреннего порядка пакета должны существовать такие acceptance conditions:

	F1 acceptance: есть processed fill basis, который Position Engine может читать без vendor-specific interpretation;

	F2 acceptance: есть updated PositionState, который Portfolio Engine может читать как уже оформленный downstream position result Minimal Core v1; этот result является derived / working position state первой реализации и не притворяется reconciled truth следующего этапа;

	F3 acceptance: есть updated PortfolioState, пригодный для downstream persistence boundary.

11.8. Audit criteria

Package F проходит аудит, если можно подтвердить:

	fill-driven spine реализован именно как три последовательно связанных внутренних слоя, а не как один неразмеченный state-updater;

	Fill Processor не мутирует PositionState и PortfolioState как final owner;

	Position Engine не выводит позицию напрямую из StrategyIntent, RiskDecision, OrderIntent или сырого execution payload;

	Portfolio Engine не пересчитывает позицию заново и не читает execution adapter напрямую;

	внутри пакета нет множественных независимых owners одного и того же класса состояния;

	Package G сможет принять результат Package F как уже согласованный downstream state result, а не как набор несвязанных фрагментов.

11.9. Codex task boundary

Package F остаётся одним логическим implementation package, но может быть разбит внутри Codex workset на несколько задач: F1 — Fill Processor, F2 — Position Engine, F3 — Portfolio Engine.

Это внутреннее разбиение допустимо только при соблюдении трёх правил: порядок обязателен; внутренние acceptance criteria обязательны; package boundary остаётся единой. В нормальном случае Package F может быть дан Codex либо как один workset с внутренними milestone gates, либо как три последовательно аудируемые подзадачи.

11.10. Итог раздела

Package F — это Fill-Driven State Spine Minimal Core v1. Он закрывает три interface contracts из 7A и реализует их как один связанный state package с жёстким внутренним порядком F1 → F2 → F3. Он получает только нормализованный execution-side result из Package E, проводит его через fill-driven truth flow и формирует downstream state result, пригодный для Package G.

12. Package G — Persistence and Startup Readiness

12.1. Роль пакета

Package G фиксирует последнюю load-bearing единицу реализации Minimal Core v1: замыкающий пакет persistence boundary и startup-ready restore/reconcile path. Его роль состоит в том, чтобы завершить первый vertical slice не просто фактом наличия state spine, а способностью ядра сохранить минимально достаточное внутреннее состояние, восстановить его после рестарта и пройти формальный startup-scoped reconcile step перед продолжением работы.

12.2. Какие interface contracts из 7A пакет закрывает

Package G закрывает раздел 13 документа 7A — State Store Contract и раздел 14 документа 7A — Startup Reconciliation Boundary Contract. Он deliberately объединяет два соседних interface seams в одну implementation unit, но с жёстким внутренним разведением G1 — State Store и G2 — Startup Reconciliation.

12.3. Scope пакета

В scope Package G входят реализация отдельного persistence boundary downstream от fill-driven state spine; сохранение минимально достаточного внутреннего состояния Minimal Core v1; restore path после рестарта на основе сохранённого state result; реализация отдельного startup-scoped reconciliation step после restore path.

Также в scope входят формирование такого startup outcome, который уже позволяет честно решать, достигнуто ли startup-ready состояние первого runtime contour, и удержание внутреннего порядка G1 → G2 с явной зависимостью Startup Reconciliation от уже существующего State Store.

12.4. Что не входит в пакет

В Package G не входят:

	fill-driven state mutation как таковая — это уже завершённая responsibility Package F;

	strategy, risk, order construction и execution boundary;

	periodic reconciliation;

	on-error reconciliation;

	более широкий Recovery Coordinator runtime contour;

	full source-of-truth policy family следующего этапа;

	governance-level решение о торговом допуске после startup reconciliation;

	hardening-specific storage discipline, locking family, replay / fault-injection families и industrial observability;

	multi-* и derivatives expansions beyond Minimal Core v1.

12.5. Upstream dependencies

Package G имеет обязательную upstream dependency на Package F — Fill-Driven State Spine, потому что State Store имеет право сохранять только уже сформированный downstream state result, а не разрозненные fragments execution / position / portfolio picture.

Кроме того, пакет зависит от already-agreed state ownership и storage discipline: state persistence не подменяет собой Position / Portfolio layer, storage boundary не создаёт новую доменную truth layer, а State Store должен предшествовать Startup Reconciliation.

12.6. Downstream dependencies

Package G является последним активным implementation package Minimal Core v1. Его непосредственная downstream зависимость — не следующий package, а end-to-end acceptance slice всей первой реализации.

Результат Package G является обязательным upstream basis для end-to-end acceptance Minimal Core v1, для package-level audit completion всего 7B и для возможной следующей фазы только после подтверждения, что vertical slice переживает рестарт и не теряет формальный startup-ready contour.

12.7. Done criteria

Package G считается реализованным для Minimal Core v1, если:

	после Package F существует отдельный State Store boundary, сохраняющий минимально достаточное внутреннее состояние;

	restore path после рестарта читает сохранённый state result как последнюю согласованную state version;

	Startup Reconciliation существует как отдельный formal step после restore path;

	startup reconciliation встроен в lifecycle запуска, а не остаётся ручной догадкой вне ядра;

	система может вернуть согласованный startup snapshot ордеров, позиции и портфеля либо формальный startup outcome, показывающий, что такая согласованность не достигнута;

	package удерживает внутренний порядок G1 → G2 и не пытается запускать startup reconciliation раньше готовности persistence boundary.

Отдельно для внутреннего порядка пакета должны существовать такие acceptance conditions:

 startup reconcile step читает не произвольную догадку о состоянии, а минимальный startup basis: restored state from State Store и тот startup-scope external/readable basis, который уже допустим для Minimal Core v1 при проверке orders / position / portfolio picture на старте;

	G1 acceptance: есть restore-readable state result, который startup path может читать как последнюю согласованную state version;

	G2 acceptance: есть отдельный startup-scoped reconcile step, который возвращает отдельный formal startup outcome/result object, различимый как минимум на уровне startup-ready vs not-startup-ready classes, и не растворяется в неявном «запуск вроде удался»;

12.8. Audit criteria

Package G проходит аудит, если можно подтвердить:

	State Store реализован как отдельный persistence boundary, а не как ещё один business layer;

	сохранённое состояние не распадается на несвязанные fragments, которые restore path не может читать как единую state version;

	Startup Reconciliation реализован как отдельный startup-only boundary, а не как скрытый placeholder полной reconciliation-family;

	periodic и on-error reconciliation не были незаметно втянуты в active scope пакета;

	startup reconcile outcome не трактуется автоматически как разрешение на normal trading flow;

	Package G не мутирует Position / Portfolio truth в обход already-agreed downstream state layers;

	end-to-end acceptance может проверить реальный restart/recovery contour, а не только наличие persistence code.

Иными словами, аудит Package G проверяет не просто наличие сохранения в хранилище, а сохранность всей завершающей логики vertical slice: состояние переживает рестарт, restore path читаем, startup reconciliation существует как отдельная формальная граница, а startup readiness не маскируется молчанием.

12.9. Codex task boundary

Package G остаётся одним логическим implementation package, но может быть разбит внутри Codex workset на две связанные задачи: G1 — State Store и G2 — Startup Reconciliation.

Это внутреннее разбиение допустимо только при соблюдении трёх правил: порядок обязателен; внутренняя зависимость явная; package boundary остаётся единой. В нормальном случае Package G может быть дан Codex либо как один workset с внутренними milestone gates, либо как две последовательно аудируемые подзадачи.

12.10. Итог раздела

Package G — это Persistence and Startup Readiness Minimal Core v1. Он закрывает два interface contracts из 7A — State Store Contract и Startup Reconciliation Boundary Contract — и реализует их как один связанный package с жёстким внутренним порядком G1 → G2. State Store сохраняет минимально достаточный downstream state result и делает его restore-readable, а Startup Reconciliation затем выполняет только startup-scoped reconcile step и возвращает формальный startup outcome.

13. Cross-package dependency order

13.1. Назначение раздела

Настоящий раздел фиксирует обязательный порядок реализации пакетов Minimal Core v1. Его задача уже и строже, чем у package-local dependencies внутри разделов 6–12: здесь задаётся единая package sequence всего первого vertical slice, без которой документ 7B потерял бы смысл как управляемая карта реализации.

13.2. Порядок реализации пакетов не является вопросом удобства

Cross-package dependency order не должен читаться как редакционная рекомендация или удобный способ работы. Он выводится из already-agreed causal chain Minimal Core v1. Порядок A → B → C → D → E → F → G является производным от contract and pipeline order уже завершённого комплекта, а не от локального удобства реализации или структуры репозитория.

13.3. Канонический порядок пакетов Minimal Core v1

Обязательный порядок реализации пакетов документа 7B таков: A → B → C → D → E → F → G.

Этот порядок не является приблизительным. Он отражает причинную последовательность первого vertical slice: сначала ядро получает допустимый input/context basis, затем формирует decision, затем получает risk verdict, затем строит execution-facing action, затем проходит boundary внешнего исполнения, затем переводит execution facts в state truth и только после этого получает persistence and startup survivability contour.

13.4. Почему Package A должен быть первым

Package A должен быть первым, потому что он создаёт первый допустимый upstream basis для всей остальной системы: normalized event input seam и ранний MTF-ready seam для первой стратегии. Без Package A downstream decision boundary не имеет легитимного input/context foundation.

13.5. Почему Package B не может стартовать раньше A

Package B не может честно стартовать раньше Package A, потому что Strategy Contract получает только already-admissible normalized market/context input из ядра. Если strategy layer начинает реализовываться до input/context foundation, возникает почти неизбежный обход: стратегия либо начинает локально собирать context, либо требует adapter-specific input напрямую. Поэтому B начинается только после принятия A.

13.6. Почему Package C не может стартовать раньше B

Package C не может честно стартовать раньше Package B, потому что RiskDecision является downstream-verdict относительно уже сформированного StrategyIntent. Следовательно, пакет risk layer не может быть первым самостоятельным центром реализации; он всегда зависит от уже существующего formal strategy-side result. Поэтому C начинается только после принятия B.

13.7. Почему Package D не может стартовать раньше C

Package D не может честно стартовать раньше Package C, потому что Order Builder строит OrderIntent только из approved RiskDecision, а Pre-execution Guard появляется уже downstream от order construction. Пакетный порядок не допускает логики «сначала сделаем order placement, а риск потом подключим». Поэтому D начинается только после принятия C.

13.8. Почему Package E не может стартовать раньше D

Package E не может честно стартовать раньше Package D, потому что Execution Boundary имеет право получать только уже построенный и прошедший execution-facing gate result. Ни одно поручение не уходит в execution layer без Pre-execution Guard. Поэтому E начинается только после принятия D.

13.9. Почему Package F не может стартовать раньше E

Package F не может честно стартовать раньше Package E, потому что fill-driven state spine начинается только после формального execution boundary и его нормализованного execution-side result. Поэтому F начинается только после принятия E.

13.10. Почему Package G не может стартовать раньше F

Package G не может честно стартовать раньше Package F, потому что persistence boundary и startup readiness имеют смысл только тогда, когда already-executed state spine существует как согласованный downstream result. Поэтому G начинается только после принятия F.

13.11. Внутренний порядок внутри Package F и Package G подчинён общему порядку

Cross-package dependency order учитывает и внутренний порядок внутри составных packages: внутри F сохраняется F1 → F2 → F3, а внутри G сохраняется G1 → G2. Внутренние подпоследовательности не отменяют общего порядка A → B → C → D → E → F → G, а раскрывают его критические внутренние шаги.

13.12. Cross-package dependency order не подменяет собой acceptance gates

Настоящий раздел задаёт именно порядок зависимости, а не условия допуска следующего пакета к старту во всех деталях. Он отвечает на вопрос: какой пакет может идти после какого. Следующий раздел отвечает на другой вопрос: при каких package-level условиях следующий пакет вообще имеет право начинаться.

13.13. Итог раздела

Cross-package dependency order Minimal Core v1 является жёстким и выводится прямо из already-agreed roadmap and interface seams. Канонический порядок пакетов — A → B → C → D → E → F → G. Ни один downstream package не имеет права честно стартовать раньше своего обязательного upstream basis.

14. Cross-package acceptance and audit gates

14.1. Назначение раздела

Настоящий раздел фиксирует межпакетный gate layer первой реализации. Его задача не в том, чтобы повторить package-local done criteria из разделов 6–12, а в том, чтобы определить: при каких условиях следующий package вообще имеет право начинаться.

14.2. Межпакетный gate не равен done criteria пакета

Done criteria пакета отвечают на вопрос: реализован ли данный package как собственный seam. Cross-package gate отвечает на другой вопрос: можно ли на основании этого результата запускать следующий package без нарушения causal chain и без обхода интерфейсных швов. Поэтому межпакетный gate должен читаться как отдельный слой допуска к следующему шагу реализации.

14.3. Gate A → B

Package B имеет право начинаться только после того, как Package A дал ядру формально допустимый input/context foundation. Для старта B должны быть приняты следующие условия: normalised event input seam существует как отдельная boundary; ранний MTF-ready seam даёт первой стратегии entry-timeframe basis и обязательные HTF inputs через ядро; strategy layer не вынужден локально собирать context и не получает adapter-specific input напрямую; Package A не маскирует full TimeframeContext family под временную реализацию Wave 1.

14.4. Gate B → C

Package C имеет право начинаться только после того, как Package B дал формальный strategy-side result первого decision step. Для старта C должны быть приняты следующие условия: Strategy Contract реализован как отдельный decision boundary; output strategy layer формализован как StrategyIntent либо явное no-action decision; strategy layer не тянет в себя risk semantics и не выдаёт скрытый order-ready result; первая стратегия проходит через boundary без обхода input/context seams.

14.5. Gate C → D

Package D имеет право начинаться только после того, как Package C дал отдельный и формально читаемый risk verdict. Для старта D должны быть приняты следующие условия: RiskDecision существует как самостоятельный downstream verdict layer; strategy approval не используется как скрытая замена risk verdict; risk layer не тянет в себя order construction; downstream order construction может опираться только на approved RiskDecision как на единственное допустимое risk basis.

14.6. Gate D → E

Package E имеет право начинаться только после того, как Package D завершил оба своих внутренних шва: Order Builder и Pre-execution Guard. Для старта E должны быть приняты следующие условия: OrderIntent строится только downstream от approved RiskDecision; Order Builder и Pre-execution Guard существуют как два разных внутренних шва одного package; guard не является вторым risk-check, а выполняет только execution-facing admissibility; ни одно поручение не уходит дальше по pipeline без builder и guard; invalid OrderIntent получает formal reject result до handoff во внешний execution contour.

14.7. Gate E → F

Package F имеет право начинаться только после того, как Package E реализовал единственную formal execution boundary и нормализованный inbound/outbound execution flow. Для старта F должны быть приняты следующие условия: существует одна и только одна formal boundary-точка связи ядра с execution adapter; никакой другой внутренний слой ядра не имеет параллельного доступа к execution adapter; outbound execution interaction стартует только после builder/guard step; inbound execution-side responses нормализуются до уровня ExecutionReport / Fill-side result before downstream handoff; Fill Processor может получать уже нормализованный execution-side result без transport-level и vendor-specific knowledge.

14.8. Gate F → G

Package G имеет право начинаться только после того, как Package F довёл state spine до уже оформленного downstream result. Для старта G должны быть приняты следующие условия: fill-driven spine реализован как три последовательно связанных внутренних слоя F1 → F2 → F3; Fill Processor, Position Engine и Portfolio Engine не размывают ownership друг друга; итогом Package F является не набор несвязанных fragments, а согласованный downstream state result; execution truth уже переведена в fill truth, затем в position truth и затем в portfolio truth; persistence boundary может читать результат F как already-formed state version.

14.9. Gate G → End-to-end acceptance slice

После Package G следующий шаг — уже не новый package, а end-to-end acceptance slice технического roadmap. Для допуска к этому финальному шагу должны быть приняты следующие условия: State Store реализован как отдельный persistence boundary; restore path после рестарта читает сохранённый result как последнюю согласованную state version; Startup Reconciliation существует как отдельный startup-only reconcile boundary; startup reconcile outcome не подменяется молчаливым предположением, что запуск удался; vertical slice теперь способен не только провести execution truth через state spine, но и пережить restart/recovery contour.

14.10. Внутренние gates Package F и Package G не заменяют межпакетные gates

Package F и Package G уже имеют собственные внутренние последовательности — F1 → F2 → F3 и G1 → G2. Но эти internal acceptance conditions не отменяют межпакетные gates данного раздела. Internal gates отвечают за то, чтобы составной package мог безопасно делиться на подзадачи. Cross-package gates отвечают за то, чтобы следующий package вообще имел право стартовать.

14.11. Gate layer должен быть явным

Как и в других implementation-facing документах комплекта, межпакетный gate не должен оставаться неявным. Для каждого перехода A → B, B → C, C → D, D → E, E → F, F → G и G → End-to-end acceptance должен существовать читаемый package-level verdict: upstream basis принят или не принят.

14.12. Итог раздела

Cross-package acceptance and audit gates образуют отдельный layer между package descriptions и фактическим стартом следующего пакета. Они не повторяют локальные done criteria пакетов, а отвечают на вопрос, при каких условиях следующий package имеет право начинаться.

15. Codex workset assembly rules

15.1. Назначение раздела

Настоящий раздел фиксирует, как implementation packages документа 7B превращаются в Codex workset без разрушения package boundaries, interface seams и phase-scoped границы Minimal Core v1. Его задача — описать, как выдавать реализационные задачи так, чтобы Codex работал по package layer, а не поперёк него.

15.2. Базовая единица workset по умолчанию — implementation package

По умолчанию один implementation package должен читаться как одна базовая единица Codex workset. Только так сохраняется связка: interface contract → implementation package → Codex task.

15.3. Один workset не должен пересекать несколько package boundaries без явного основания

Главное правило этого раздела состоит в том, что одна задача Codex не должна по умолчанию пересекать несколько implementation packages. Если задача одновременно трогает, например, Strategy Boundary, Risk Boundary и Order Construction, она перестаёт быть audit-friendly и начинает размывать package map.

15.4. Cross-package gates обязательны и для Codex workset

Codex workset должен следовать не только package order, но и cross-package acceptance and audit gates предыдущего раздела. Workset B не стартует до принятия gate A → B; workset C не стартует до принятия gate B → C; и так далее до G → End-to-end acceptance.

15.5. Каждый workset обязан иметь protected scope

Каждая задача Codex, собранная из package layer, должна иметь protected scope. Это означает, что в формулировке задачи должны быть явно перечислены: какой package закрывается; какие sections 7A являются его contract basis; какие sections 7B задают его package scope; что прямо считается out-of-scope для данной задачи.

15.6. Формат ссылки workset на документы комплекта

Каждый Codex workset должен опираться как минимум на три слоя комплекта: на соответствующий interface contract из 7A; на соответствующий implementation package из 7B; на нужные load-bearing ограничения из technical roadmap, если без них нельзя удержать правильный order or dependency reading.

Это правило нужно затем, чтобы задача Codex не жила в вакууме. Она должна быть не «сделай модуль X», а «закрой package Y, реализуя seam Z, не выходя за границу Minimal Core v1 и не нарушая порядок пакетов».

15.7. Допустимое внутреннее разбиение package-а

По умолчанию package должен быть одной задачей Codex. Но 7B прямо допускает ограничённые случаи, когда один логический package может быть разбит на несколько внутренних workset-ов. Такое разбиение допустимо только при соблюдении двух условий: внутренние части пакета already recognised в самом 7B как последовательные внутренние seams; между ними существуют явные internal acceptance criteria.

15.8. Особое правило для Package F

Package F является единственным пакетом, для которого внутреннее разбиение должно считаться не исключением, а предусмотренной рабочей формой. Codex workset для Package F должен собираться только в двух допустимых режимах: либо как один общий workset с внутренними milestone gates, либо как три последовательно принимаемые задачи F1 → F2 → F3.

15.9. Особое правило для Package G

Package G тоже допускает внутреннее разбиение, но только в виде строго упорядоченной пары G1 — State Store и G2 — Startup Reconciliation. Здесь правило ещё жёстче: G2 не просто идёт после G1, а не имеет права даже частично симулировать его работу.

15.10. End-to-end acceptance не является ещё одним package

После завершения G workset следующий шаг — не новый implementation package и не «Package H», а end-to-end acceptance slice Minimal Core v1. Финальный Codex workset после G должен читаться как acceptance-oriented task layer, а не как ещё один implementation package.

15.11. Итог раздела

Codex workset должен собираться по implementation packages, а не поперёк них. Базовой единицей workset по умолчанию является один package. Пересечение package boundaries одной задачей не допускается без явного основания. Internal splitting допустим только там, где он уже признан самим package layer и поддержан явными acceptance criteria.

16. Что сознательно не входит в 7B

16.1. Пакеты следующего этапа реализации

Документ 7B сознательно не включает implementation packages следующего этапа после Minimal Core v1. Full TimeframeContext family, Context Gate, explicit unknown-state family, periodic reconciliation, on-error reconciliation, broader Recovery Coordinator boundary и зрелая source-of-truth runtime family допустимы только как future seams, но не как active package scope.

16.2. Hardening-layer

Документ 7B сознательно не включает hardening tasks и hardening-specific implementation packages. Idempotent fill processing, atomic state persistence, structured logging, mock adapters, correctness tests, fault scenarios и другие инженерные работы следующего уровня уже вынесены technical roadmap в отдельный hardening-layer. Следовательно, 7B не является ни hardening-планом, ни boundary-test спецификацией.

16.3. Структура репозитория и кодовая раскладка

Документ 7B сознательно не задаёт структуру папок, файлов, модулей, импортов, naming conventions, class signatures и других элементов project scaffolding. Package в этом документе означает load-bearing единицу реализации, а не будущую папку в репозитории.

16.4. Расширения beyond Minimal Core v1

Документ 7B сознательно не включает multi-instrument readiness, multi-strategy readiness, multi-exchange abstraction, derivatives expansion и иные расширения beyond Minimal Core v1.

16.5. Полный план Codex work beyond package layer

Документ 7B сознательно не превращается в подробный backlog всех будущих задач Codex вне package map. Он задаёт правила сборки workset из already-defined packages, но не заменяет собой отдельные task briefs и не формирует workset следующего этапа заранее.

16.6. Итог раздела

7B сознательно ограничен package layer Minimal Core v1. Он не включает пакеты следующего этапа, не тянет в себя hardening-layer, не задаёт файловую структуру, не описывает расширения beyond Minimal Core v1 и не превращается в полный backlog всех будущих задач.

17. Итоговые invariants 7B

Итоговые invariants данного документа фиксируют не новую архитектуру ядра и не новый contract layer, а жёсткие ограничения package layer Minimal Core v1. Technical roadmap уже задал phase-scoped порядок первой реализации, а 7A уже зафиксировал interface seams этой реализации. Следовательно, 7B обязан удерживать именно ту границу, при которой реализация раскладывается на пакеты работ, но не разрушает ни roadmap order, ни interface layer, ни phase boundary первого vertical slice.

17.1. Пакетный слой является фазовым

Пакеты 7B относятся только к Minimal Core v1 и не описывают всю будущую реализацию ядра сразу.

17.2. Пакеты следуют interface seams

Каждый implementation package должен быть производным от already-agreed interface contracts 7A, а не заменять их своей локальной логикой.

17.3. Пакеты строятся по load-bearing seams

Package map определяется по несущим швам реализации, а не по папкам, файлам или удобству структуры репозитория.

17.4. Package order обязателен

Канонический порядок A → B → C → D → E → F → G не является рекомендацией; он обязателен как производный от technical roadmap и causal chain первой реализации.

17.5. Downstream package не стартует без принятого upstream basis

Ни один следующий пакет не имеет права честно начинаться, пока не принят межпакетный gate предыдущего перехода.

17.6. Package-local readiness не равен next-package admission

Готовность пакета и право начать следующий пакет являются разными слоями управления реализацией и не должны смешиваться.

17.7. Один package не должен молча поглощать соседний

Пакет не имеет права незаметно расширяться до соседнего seam даже тогда, когда это выглядит технически удобным.

17.8. Execution boundary сохраняет единственность и на package level

Execution world входит в ядро только через Package E; никакой другой package не должен получать параллельный доступ к execution adapter.

17.9. Fill-driven spine сохраняет ownership discipline и на package level

Execution truth становится fill truth, затем position truth, затем portfolio truth, и ownership этого пути не расползается между несколькими packages или внутренними слоями.

17.10. Package F и G допускают внутреннее разбиение, но не теряют пакетную целостность

F1 / F2 / F3 и G1 / G2 являются допустимыми внутренними workset-формами, но не превращают Package F и Package G в несколько независимых packages.

17.11. Codex workset собирается по пакетам

Базовой единицей workset по умолчанию является implementation package, а не случайный набор файлов или функций.

17.12. Каждый workset обязан иметь protected scope

Codex task должен явно знать, какой package он закрывает, на какие sections 7A и 7B он опирается и что считается out-of-scope.

17.13. После G идёт не новый package, а acceptance slice

Package G замыкает package layer Minimal Core v1; следующий шаг — end-to-end acceptance slice, а не ещё один implementation package.

17.14. Итог раздела

Итоговая формула 7B такова: первая реализация обязана иметь не только правильные interface seams, но и жёсткую package map, в которой каждый пакет следует contract boundaries, каждый следующий шаг допускается только после принятия upstream basis, а Codex workset остаётся производным от package layer, а не разрушает его.
