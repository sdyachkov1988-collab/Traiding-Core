Interface Contracts / Minimal Core v1

Документ №7A в комплекте документов торгового ядра



Версия	v0.1
Статус	Собрано по финально согласованному тексту
Текущий scope	Только Wave 1 / Minimal Core v1 interface contracts
Роль документа	Фиксирует implementation-facing interface layer первой реализации
Основание	Документы 1–6 комплекта и Technical Roadmap реализации



Документ открывает implementation-facing слой комплекта и описывает только те интерфейсные швы, которые обязательны для первого исполнимого vertical slice Minimal Core v1. Будущие расширения видимы как reserved extension seams, но не канонизируются как обязательства первой реализации.





1. Назначение документа

Документ Interface Contracts / Minimal Core v1 фиксирует implementation-facing interface layer для первого реализуемого среза торгового ядра. Его задача — перевести уже утверждённые architectural, technical, engineering, domain, contract и governance-слои в форму таких интерфейсных границ, которые уже пригодны для непосредственной реализации и последующего разложения на implementation packages и Codex workset.

Документ не создаёт новую доменную модель и не переопределяет canonical core truth. Он появляется только после того, как комплект уже зафиксировал, что именно ядро обязано различать как signal, decision, risk verdict, order intent, order, fill, position, financial-state truth и reconciliation outcome, а также после того, как governance-layer уже определил policy-level правила допуска и ограничения торговли.

Technical Roadmap прямо задаёт, что сначала реализуется Minimal Core v1 как первый исполнимый vertical slice сделки, затем отдельно формализуются MTF + recovery + reconciliation semantics, и только после этого усиливается hardening-layer. Поэтому interface contracts первого implementation-facing документа описывают не всё будущее эталонное ядро сразу, а именно тот минимально достаточный срез, который уже признан первым обязательным этапом реализации.

При этом документ не превращает первую сборку в вечный стандарт ядра. Assembly-level компромиссы первой тестовой сборки допускаются, но не канонизируются как invariants ядра. Поэтому документ является phase-scoped: он достаточно конкретен для первой реализации и достаточно сдержан, чтобы не подменить будущие contract families их временными ранними суррогатами.

Главная роль документа состоит в том, чтобы зафиксировать не внутренние сущности ядра, а границы между уже согласованными слоями Minimal Core v1. Именно здесь должны стать формально проверяемыми такие швы, как normalized market input, strategy boundary, risk boundary, order construction boundary, execution boundary, fill-driven state spine, state store boundary и startup reconciliation boundary.

Документ предназначен для архитектора реализации, разработчика интерфейсного слоя, аудитора первой сборки и для следующего документа 7B, в котором implementation-facing слой будет разложен на implementation packages и Codex workset.

2. Место документа в комплекте

Interface Contracts / Minimal Core v1 является документом №7A и открывает implementation-facing слой комплекта документов торгового ядра. Его место не является произвольным: Core Contracts уже фиксирует, что после contract-level truth model становятся возможны implementation contracts и implementation packages, а Trading Governance завершает внешний policy-layer допуска и continuation control.

Архитектурный roadmap задаёт, каким должно быть ядро как система. Technical roadmap определяет, в каком порядке это ядро собирается и какие способности реализуются первыми. Engineering Guardrails фиксирует обязательные инженерные ограничения. Trading Domain Model раскрывает execution/data/recovery reality. Core Contracts закрепляет canonical core truth model. Trading Governance добавляет внешний policy-layer допуска и continuation control.

Только после этого возникает слой interface contracts, который уже не обсуждает, что означает Signal, Fill или Position, и не решает, разрешено ли системе торговать, а определяет, через какие формальные implementation-facing швы эти уже определённые слои будут собраны в Minimal Core v1.

Документ 7A не заменяет собой ни Technical Roadmap, ни Core Contracts. Technical Roadmap остаётся документом порядка реализации, зависимостей между шагами и done criteria; Core Contracts остаётся документом о canonical entities, truth layers, transitions и invariants. Документ 7A строится поверх обоих и остаётся отдельным implementation-facing документом.

Его связь с будущим 7B также прямая: если 7A определяет implementation-facing interface contracts для первого реализуемого среза, то следующий документ естественно должен разложить именно этот interface layer на implementation packages и Codex workset.

3. Scope и phase boundary

3.1. Что входит в scope документа

В scope документа №7A входят только те interface contracts, которые уже принадлежат Wave 1 / Minimal Core v1 по Technical Roadmap. В scope 7A входят следующие контракты:

• нормализованный входной контракт рыночного события;

• minimal MTF input seam для первой стратегии;

• Strategy Contract;

• Risk Contract;

• Order Builder Contract;

• Pre-execution Guard Contract как отдельный execution-facing шов;

• Execution Boundary Contract;

• Fill Processor / Position Engine / Portfolio Engine contracts как fill-driven spine;

• State Store Contract;

• Startup Reconciliation Boundary Contract.

Этот набор совпадает с block-set Minimal Core v1 и с Wave 1 technical sequence, где один MarketEvent должен пройти путь до обновления Position и PortfolioState, а состояние должно пережить рестарт и пройти startup reconciliation.

3.2. Что не входит в scope документа как first-class contracts

В документ №7A не входят как first-class interface contracts те contract families, которые Technical Roadmap явно относит к следующему этапу: полноценный TimeframeContext, Context Gate, единые политики выравнивания и свежести, развитая reconciliation-модель с periodic и on-error contours, explicit unknown-state model и зрелая protective/recovery semantics. В 7A они могут быть только reserved extension seams.

В 7A также не входят hardening-specific interfaces. Idempotent fill processing, atomic state persistence, structured logging, mock adapters, correctness tests и fault scenario tests относятся к hardening-layer и не должны превращаться здесь в отдельные interface contracts первой реализации.

Наконец, в scope 7A не входят multi-instrument readiness, multi-strategy readiness, multi-exchange abstraction, derivatives expansion и иные расширения beyond Minimal Core v1.

3.3. Phase boundary документа

Критическая phase boundary документа №7A состоит в следующем: здесь фиксируются implementation-facing interface contracts только для первой сборки Minimal Core v1, но сами эти интерфейсы не должны канонизировать временные ограничения первой сборки как постоянные invariants ядра.

Из этого следует практическое правило написания всех последующих разделов 7A. Каждый interface contract должен быть помечен по трём фазовым статусам:

• обязательно для Wave 1 / Minimal Core v1;

• reserved extension seam для Захода 2;

• не входит в первую реализацию.

Эта маркировка является рабочим инструментом удержания phase-scoped границы документа.

3.4. Критическая граница документа

Документ описывает implementation-facing layer между already-defined domain/contracts/policy layers и первой реализацией, но не подменяет собой ни canonical model, ни governance, ни Engineering Guardrails. Он не обсуждает заново доменный смысл Signal или Fill, не решает заново policy-вопросы trade admission и не раскрывает заново storage discipline, logging rules и fault handling mechanics. Он определяет только одно: через какие формальные интерфейсные швы собирается Minimal Core v1 и где проходят его phase boundaries.

3.5. Итог раздела

Scope документа №7A ограничен интерфейсными контрактами Minimal Core v1 и строго следует фазовой логике Technical Roadmap. Полноценные contract families следующего этапа и hardening-layer сюда не входят как first-class interfaces и допускаются лишь как reserved extension seams.

4. Формат описания каждого интерфейсного контракта

4.1. Назначение единого формата

Документ №7A должен описывать interface contracts не как произвольный набор разделов разной глубины, а как строго повторяемый implementation-facing формат. Это необходимо потому, что Technical Roadmap задаёт последовательность сборки и done criteria первой реализации, а сам документ №7A является phase-scoped слоем между conceptual package и будущим implementation package layer.

Единый формат нужен не ради редакционной симметрии, а для того, чтобы документ можно было использовать как рабочую основу для реализации, аудита и последующего перехода к 7B.

4.2. Формат не подменяет собой доменные и governance-слои

Единый формат описания интерфейсного контракта не должен превращать 7A в повтор Core Contracts или Trading Governance. Он фиксирует implementation-facing границы между уже согласованными слоями первой реализации.

4.3. Обязательные элементы описания каждого интерфейсного контракта

• Роль интерфейса — краткая формулировка того, какую функцию данный интерфейс выполняет внутри Minimal Core v1.

• Upstream / downstream граница — явное указание, от какого слоя интерфейс принимает вход и в какой следующий слой имеет право передавать результат.

• Минимальный обязательный input — input описывается на уровне доменных сущностей, а не как field-by-field schema; детали реализации принадлежат 7B.

• Минимальный обязательный output — output описывается на уровне допустимого результата и boundary meaning, а не как реализационная сериализация.

• Что интерфейс не имеет права знать или делать — обязательный отрицательный блок против leakage и смешения слоёв.

• Done / readiness criterion — краткий проверяемый критерий готовности интерфейса в рамках Minimal Core v1.

• Фазовый статус — обязательно для Wave 1 / reserved extension seam для Захода 2 / не входит в первую реализацию.

4.4. Роль блока «что интерфейс не имеет права знать или делать»

Отрицательный блок нужен как практический механизм защиты уже согласованных доменных швов от implementation leakage. Он удерживает separation of concerns и не позволяет стратегии, риску, execution boundary или persistence layer присваивать себе чужие обязанности.

4.5. Роль done / readiness criterion

Каждый интерфейсный контракт должен завершаться кратким done / readiness criterion. Документ 7A не должен описывать интерфейсы только на языке «что это такое»; он должен доходить до формулировки, когда этот контракт считается реально существующим и годным для первой реализации.

4.6. Фазовый статус как обязательная часть каждого контракта

Фазовый статус контракта является обязательным элементом формата, а не вспомогательной пометкой. Он показывает, что нужно реализовать прямо сейчас, что только оставлено как seam следующего этапа и что сознательно вынесено за пределы первой реализации.

4.7. Единый формат не означает одинаковую глубину всех контрактов

Единый формат означает одинаковую структуру чтения, а не одинаковое количество текста. Более нагруженные швы неизбежно будут подробнее простых входных контрактов.

4.8. Сводный перечень extension seams не заменяет phase marker внутри контракта

В разделах 6–14 seam-пометка даётся в контексте конкретного интерфейса, а в разделе 15 будет дан сводный список seam-ов без повторного раскрытия их смысла.

4.9. Итог раздела

Каждый интерфейсный контракт документа №7A описывается по единой phase-scoped схеме: роль, границы, минимальный input и output, отрицательный блок запретов, readiness criterion и фазовый статус.

5. Общие правила interface layer

5.1. Interface layer документа №7A является фазовым слоем Minimal Core v1

Все interface rules документа №7A действуют внутри phase-scoped границы Minimal Core v1 и не должны преждевременно канонизировать будущие расширения как уже обязательные интерфейсы первой сборки.

5.2. Никакой интерфейс не имеет права обходить архитектурные швы

Ни один контракт документа №7A не должен позволять перескакивать через already-agreed layer seams. Если интерфейс допускает такой обход, он невалиден уже на уровне 7A.

5.3. Interface contract не подменяет собой domain contract

Интерфейсный контракт является формой организационной границы реализации, но не новым источником доменного смысла. Если implementation-facing шов начинает переопределять, что такое Decision, OrderIntent, Fill или Position, он выходит за scope 7A и ломает связь с Core Contracts.

5.4. Execution существует только behind interface

Execution может существовать для ядра только через формальный boundary contract. Ни Strategy Contract, ни Risk Contract, ни Fill / Position / Portfolio spine не имеют права протаскивать внутрь себя сырой execution access или adapter-specific knowledge.

5.5. Владение состоянием не может расползаться между несколькими интерфейсами

Ни один интерфейс не должен быть спроектирован так, будто один и тот же state change может финализироваться в нескольких независимых местах. Ownership state changes должен оставаться единым и читаемым.

5.6. Interface layer обязан сохранять fill-driven spine Minimal Core v1

Direction of truth flow внутри state spine идёт от execution facts к Fill Processor, от Fill Processor к Position и от Position к PortfolioState. Нельзя проектировать интерфейс так, будто Position выводится напрямую из StrategyIntent, OrderIntent или status-only layer.

5.7. Adapter- и vendor-specific детали не должны протекать внутрь ядра

Нормализация внешних форматов должна происходить до входа в доменные швы Minimal Core v1. Интерфейсный контракт описывает допустимый доменный input/output шва, а не транспортный или vendor-specific payload.

5.8. Input и output интерфейса описываются на уровне доменных сущностей

Минимальный input и output каждого контракта описываются на уровне доменных сущностей, состояний и допустимых результатов, а не как полная field-by-field schema или реализационная сериализация.

5.9. Reserved seams должны быть видимыми, но не превращаться в first-class obligations

Reserved seams должны быть явно видимыми внутри конкретных контрактов, но не должны превращаться в обязательства первой реализации.

5.10. Общие правила interface layer не заменяют собой Engineering Guardrails

Документ №7A опирается на boundary discipline и state ownership rules, но не дублирует Engineering Guardrails и не раскрывает заново полный набор engineering mechanics.

5.11. Итог раздела

Interface layer документа №7A является фазовым слоем Minimal Core v1 и подчиняется жёстким общим правилам: никаких обходов швов, никакой подмены domain contracts, execution только через boundary, единый ownership состояния, fill-driven truth flow, отсутствие vendor leakage, доменный уровень описания input/output, видимые reserved seams и недопустимость дублирования Guardrails.

6. Normalized Event Input Contract

6.1. Роль интерфейса

Normalized Event Input Contract фиксирует первый implementation-facing шов Minimal Core v1: единый нормализованный вход рыночного события в ядро. Он переводит внешний рыночный вход в такую доменно признанную форму, с которой ядро уже имеет право работать дальше через Strategy Contract.

6.2. Upstream / downstream граница

Upstream boundary данного контракта — любой внешний источник market data, который ещё не является доменной сущностью ядра. Downstream boundary — только strategy-facing вход Minimal Core v1. Контракт передаёт вниз только нормализованный MarketEvent и не имеет права перепрыгивать сразу в Risk, Execution, Position или Portfolio paths.

6.3. Минимальный обязательный input

Вход обязан нести такой объём рыночной информации, который позволяет ядру различить instrument scope, temporal reference и тип нормализованного market-data input, достаточный для первого strategy-facing шага.

6.4. Минимальный обязательный output

Минимальный output — доменный MarketEvent, признанный допустимым входом для Strategy Contract в рамках Minimal Core v1. Этот output не является StrategyIntent и не должен включать скрытое стратегическое толкование события.

6.5. Что интерфейс не имеет права знать или делать

• знать strategy logic и принимать торговое решение вместо Strategy Contract;

• смешивать нормализацию события с risk evaluation, order construction, execution или portfolio accounting;

• обращаться к state store как к источнику стратегического или accounting-смысла;

• протаскивать vendor-specific или transport-specific payload внутрь ядра как будто это уже доменная форма события;

• подменять собой minimal MTF seam следующего шва.

6.6. Done / readiness criterion

Контракт считается готовым, если ядро принимает внешний market-data input через единый нормализующий шов, downstream strategy layer получает нормализованный MarketEvent как единственный допустимый вход первого strategy-facing шага, а Strategy Contract не зависит от adapter-specific формы входного события.

6.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: единый normalized event input seam, доменно признанный MarketEvent и отделение strategy layer от внешнего источника market data. Reserved extension seam для Захода 2: расширение event input boundary в сторону зрелого multi-timeframe context assembly. Не входит в первую реализацию: расширенные runtime event contours beyond Minimal Core v1.

6.8. Итог раздела

Normalized Event Input Contract открывает первый честный vertical slice Minimal Core v1 и делает возможным следующий интерфейсный контракт — Strategy Contract.

7. Minimal MTF Input Seam Contract

7.1. Роль интерфейса

Minimal MTF Input Seam Contract фиксирует ранний MTF-ready шов, через который первая мультитаймфреймная стратегия получает согласованные higher-timeframe inputs через ядро, а не собирает их локально внутри strategy layer.

7.2. Upstream / downstream граница

Upstream boundary данного контракта — уже существующий normalized event contour и canonical input row по entry timeframe. Downstream boundary — только Strategy Contract первой MTF-стратегии. Контракт не строит full contextual family для всего будущего ядра, а лишь даёт strategy layer согласованный ранний MTF-input, не требующий обхода ядра.

7.3. Минимальный обязательный input

Для Minimal Core v1 достаточно, чтобы ядро уже обладало каноническим входным рядом по entry timeframe, минимально необходимым HTF basis первой стратегии и признаком closed-bar-aware reading без look-ahead. Документ №7A не канонизирует здесь полный future MTF-layer и не требует поддержки произвольного набора higher timeframes; он фиксирует только тот минимальный upstream contextual basis, без которого первая MTF-стратегия не может быть честно проведена через Wave 1.

7.4. Минимальный обязательный output

Минимальный output — ранний согласованный MTF input, пригодный для передачи в Strategy Contract первой стратегии как strategy-facing contextual basis Minimal Core v1. Он ещё не является полной contract family TimeframeContext.

7.5. Что интерфейс не имеет права знать или делать

• подменять собой полноценный TimeframeContext как зрелую contract family;

• подменять собой будущий ContextAssembler, Context Gate, BarAlignmentPolicy, ClosedBarPolicy и FreshnessPolicy следующего этапа;

• позволять strategy layer самой определять допустимость HTF-баров или держать локальный strategy cache как source of truth;

• превращать временный derived HTF path первой сборки в постоянный invariant ядра;

• смешивать ранний MTF seam с risk, order construction, execution или state ownership.

7.6. Done / readiness criterion

Контракт считается готовым, если первая MTF-стратегия получает entry timeframe и обязательные HTF-входы через ядро, стратегия не собирает HTF-input локально и не определяет допустимость higher-timeframe inputs сама, а шов обеспечивает closed-bar only semantics и no-look-ahead boundary в минимально достаточном объёме первой стратегии и не притворяется полным TimeframeContext contract family.

7.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: ранний MTF-ready seam, доставка entry timeframe и обязательных HTF-входов через ядро, closed-bar only semantics и no-look-ahead boundary. Reserved extension seam для Захода 2: полноценный TimeframeContext, ContextAssembler, Context Gate, BarAlignmentPolicy, ClosedBarPolicy и FreshnessPolicy. Не входит в первую реализацию: полная contract family MTF-layer для всех будущих стратегий и контуров.

7.8. Итог раздела

Minimal MTF Input Seam Contract остаётся phase-scoped seam первой реализации, а не преждевременной канонизацией зрелого MTF-layer.

8. Strategy Contract

8.1. Роль интерфейса

Strategy Contract фиксирует формальную границу между strategy-facing market/context input и upstream strategy output, который в рамках текущего комплекта обозначается как StrategyIntent. Этот output ещё не несёт ни одобрения risk layer, ни исполнимой формы действия.

8.2. Upstream / downstream граница

Upstream boundary Strategy Contract — это Normalized Event Input Contract и, для первой стратегии, Minimal MTF Input Seam Contract. Downstream boundary — только Risk Contract. Strategy Contract передаёт вниз только formal strategy output decision-layer и не имеет права перепрыгивать сразу в order construction, execution или state/accounting branches.

8.3. Минимальный обязательный input

Для Minimal Core v1 достаточно, чтобы strategy layer получал допустимый normalized market/context input текущего supported contour, instrument-scoped basis и temporal/contextual basis, уже признанный допустимым для Wave 1. Для первой MTF-стратегии это означает entry-timeframe basis и обязательные HTF-входы, доставленные через ядро.

8.4. Минимальный обязательный output

Минимальный output — StrategyIntent либо явное решение ничего не делать. Это formal strategy-side decision result, который downstream risk layer имеет право интерпретировать как upstream decision identity.

8.5. Что интерфейс не имеет права знать или делать

• обращаться напрямую к execution adapter, state store или portfolio accounting;

• формировать RiskDecision вместо Risk Contract;

• строить OrderIntent вместо Order Builder;

• читать fills, execution reports, position mutations или portfolio truth как часть собственной decision-logic;

• резервировать капитал, изменять позицию или инициировать execution-side action;

• локально определять admissibility HTF-баров и подменять собой minimal MTF seam;

• тащить в strategy logic vendor-specific input format как будто это доменная сущность ядра.

8.6. Done / readiness criterion

Strategy Contract считается готовым, если strategy layer получает только допустимый market/context input через ядро, возвращает StrategyIntent либо явное решение ничего не делать, не зависит напрямую от adapter layer, state store и portfolio accounting, а первая MTF-стратегия проходит через этот контракт без локальной сборки HTF admissibility.

8.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: formal strategy-facing boundary и strategy output в форме StrategyIntent либо явного решения ничего не делать. Reserved extension seam для Захода 2: стратегия поверх полноценного TimeframeContext и формальная интеграция с Context Gate. Не входит в первую реализацию: full strategy orchestration across multi-strategy contours и regime-aware strategy routing.

8.8. Итог раздела

Strategy Contract делает strategy layer формально отделённой decision boundary первой реализации и передаёт результат только в Risk Contract.

9. Risk Contract

9.1. Роль интерфейса

Risk Contract фиксирует формальную границу между strategy-side decision output и downstream risk verdict layer. Он существует затем, чтобы сделать risk layer самостоятельным implementation-facing швом, а не декоративной проверкой вокруг уже готового order action.

9.2. Upstream / downstream граница

Upstream boundary Risk Contract — только Strategy Contract и его formal output в виде StrategyIntent. Downstream boundary — только Order Construction layer, прежде всего Order Builder Contract. Risk Contract передаёт downstream только risk verdict и не строит OrderIntent сам.

9.3. Минимальный обязательный input

Для Minimal Core v1 достаточно, чтобы risk layer получал формальный StrategyIntent, instrument rules / instrument specs и актуальный PortfolioState как минимальную account/exposure basis текущего supported contour.

9.4. Минимальный обязательный output

Минимальный output — RiskDecision как отдельный formal risk verdict. Для 7A важно не перечисление вариантов verdict, а его смысл: это downstream-result risk layer, который Order Builder имеет право читать как единственное допустимое upstream основание для построения OrderIntent.

9.5. Что интерфейс не имеет права знать или делать

• формировать market-data input или strategy-context вместо upstream layers;

• обращаться к execution adapter или vendor-specific execution API;

• строить OrderIntent вместо Order Builder;

• выполнять rounding, min_qty / min_notional и иную pre-execution admissibility проверку вместо Pre-execution Guard;

• изменять позицию, портфель или state store напрямую;

• подменять собой governance-layer и решать вопрос environment/policy admission торговли;

• смешивать risk verdict с execution-ready action.

9.6. Done / readiness criterion

Risk Contract считается готовым, если StrategyIntent проходит через отдельный risk boundary, risk layer использует только допустимый upstream basis, RiskDecision формализован как отдельный результат, а downstream Order Builder опирается только на approved RiskDecision.

9.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Risk Contract между Strategy Contract и Order Construction layer, formal RiskDecision и запрет прямого перехода StrategyIntent в OrderIntent. Reserved extension seam для Захода 2: более зрелая связь risk verdict с full TimeframeContext и mature recovery / reconciliation semantics. Не входит в первую реализацию: multi-strategy risk allocation family, regime-aware risk orchestration и derivatives-ready risk policies.

9.8. Итог раздела

Risk Contract отделяет strategy-side decision output от downstream order construction и делает RiskDecision самостоятельным verdict admissibility.

10. Order Construction Contracts

Order Construction layer Minimal Core v1 состоит из двух разных implementation-facing швов. Order Builder Contract превращает approved RiskDecision в formal OrderIntent. Pre-execution Guard Contract отдельно проверяет execution-facing admissibility этого OrderIntent перед handoff во внешний execution boundary. Pre-execution Guard не является вторым risk-check.

10.1. Order Builder Contract

10.1.1. Роль интерфейса

Order Builder Contract преобразует approved RiskDecision в OrderIntent как первый execution-facing внутренний объект ядра. Он отделяет risk verdict от параметров исполнения и не отправляет действие на биржу.

10.1.2. Upstream / downstream граница

Upstream boundary Order Builder Contract — только Risk Contract и его formal output в виде approved RiskDecision. Ни Signal в одиночку, ни неявное предположение о допустимости не являются достаточным основанием для OrderIntent. Downstream boundary Order Builder Contract — только Pre-execution Guard Contract.

10.1.3. Минимальный обязательный input

Минимальный input включает approved RiskDecision, instrument specs и execution capabilities в объёме, достаточном для построения исполнимой формы действия.

10.1.4. Минимальный обязательный output

Минимальный output — OrderIntent как formal execution-facing internal object, пригодный для downstream проверки на execution admissibility.

10.1.5. Что интерфейс не имеет права знать или делать

• принимать risk verdict вместо Risk Contract;

• обращаться напрямую к execution adapter или создавать внешний Order;

• подтверждать venue-validity, rounding admissibility или final execution constraints вместо Pre-execution Guard;

• читать observed order state, fills, Position или PortfolioState как будто они принадлежат order construction step;

• подменять собой governance-layer и решать вопрос trade admission;

• трактовать implicit strategy approval как достаточное основание для OrderIntent.

10.1.6. Done / readiness criterion

Order Builder Contract считается готовым, если approved RiskDecision является единственным допустимым upstream basis для построения OrderIntent, Strategy и Risk не могут обходить этот шов, а downstream Pre-execution Guard получает уже formal OrderIntent.

10.1.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Order Builder Contract и формирование OrderIntent только из approved RiskDecision. Reserved extension seam для Захода 2: более зрелое включение position-originated close intents и recovery/reconciliation-sensitive routing. Не входит в первую реализацию: complex child-order families, OCO, ladder exits и иные продвинутые execution policies.

10.1.8. Итог подраздела

Order Builder Contract превращает approved RiskDecision в formal OrderIntent и тем самым отделяет risk verdict от execution-facing internal action.

10.2. Pre-execution Guard Contract

10.2.1. Роль интерфейса

Pre-execution Guard Contract фиксирует отдельный execution-facing gate layer между OrderIntent и внешним execution boundary. Он проверяет price/qty rounding, min_qty / min_notional, совместимость типа ордера с execution capabilities и формальный reject-state, если поручение перестаёт быть исполнимым. Это не второй risk-check.

10.2.2. Upstream / downstream граница

Upstream boundary Pre-execution Guard Contract — только Order Builder Contract и его formal output в виде OrderIntent. Downstream boundary — только Execution Boundary Contract / Execution Coordinator. Ни одно поручение не уходит в execution layer без этого gate.

10.2.3. Минимальный обязательный input

Минимальный input включает formal OrderIntent, instrument specs, execution capabilities и актуальные execution constraints в том объёме, который нужен для venue-facing admissibility check.

10.2.4. Минимальный обязательный output

Минимальный output — execution-admissibility result текущего OrderIntent: либо поручение остаётся допустимым для перехода во внешний execution boundary, либо получает formal reject-state как execution-facing invalid action.

10.2.5. Что интерфейс не имеет права знать или делать

• заново принимать стратегическое решение или пересчитывать рыночный режим;

• заменять собой Risk Contract и повторно оценивать trade admissibility на risk-layer уровне;

• самостоятельно определять rounding policy; rounding rule задаётся instrument spec, execution capability profile или already-agreed execution constraint policy, а Guard только применяет её как execution-facing admissibility boundary;

• строить OrderIntent вместо Order Builder;

• обращаться напрямую к Position, PortfolioState или governance-layer как к источнику решения о том, торговать ли вообще;

• подменять собой Execution Boundary Contract и отправлять действие наружу без следующего formal handoff;

• трактовать venue-facing invalidation как новый доменный decision-layer verdict.

10.2.6. Done / readiness criterion

Pre-execution Guard Contract считается готовым, если ни одно OrderIntent не передаётся во внешний execution boundary без отдельного Guard, Guard проверяет execution-facing admissibility, invalid OrderIntent получает formal reject result и не проходит дальше.

10.2.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Pre-execution Guard Contract, execution-facing admissibility check между OrderIntent и execution boundary, rounding, min_qty / min_notional, order-type compatibility и formal reject-state. Reserved extension seam для Захода 2: более зрелое включение close-routing contours и recovery/reconciliation-sensitive paths. Не входит в первую реализацию: сложные venue-policy families и hardening-specific safety and test interfaces.

10.2.8. Итог подраздела

Pre-execution Guard Contract является обязательным execution-facing gate layer между OrderIntent и внешним execution boundary. Его задача — проверить, остаётся ли уже сформированное внутреннее поручение downstream valid при текущих instrument/venue constraints, и либо допустить его к следующему handoff, либо остановить formal reject result before execution.

10.3. Итог раздела

Order Construction layer сохраняет правильную causal chain: StrategyIntent → RiskDecision → OrderIntent → Pre-execution Guard → Execution Boundary.

11. Execution Boundary Contract

11.1. Роль интерфейса

Execution Boundary Contract фиксирует единственную допустимую boundary-точку связи ядра с внешним execution adapter. Он отделяет внутреннюю доменную causal chain от внешней execution reality, не разрушая уже зафиксированные швы.

11.2. Upstream / downstream граница

Upstream boundary Execution Boundary Contract — только Pre-execution Guard Contract и его execution-admissible результат. Downstream boundary — внешний execution adapter и затем обратно в ядро только через нормализованные ExecutionReport / Fill facts, а не через сырой vendor payload.

11.3. Минимальный обязательный input

Для Minimal Core v1 достаточно, чтобы Execution Boundary Contract получал execution-admissible OrderIntent как единственную допустимую internal action form, instrument specs / execution capabilities в необходимом объёме и formal execution-side context, достаточный для передачи действия во внешний contour.

11.4. Минимальный обязательный output

Минимальный output — нормализованный execution-side result, пригодный для downstream fill-driven spine: ExecutionReport / execution-side status update и Fill fact или набор facts, если execution reality уже выразилась в этой форме.

11.5. Что интерфейс не имеет права знать или делать

• содержать strategy logic, risk logic или portfolio/accounting logic;

• принимать решение о trade admission вместо governance-layer;

• подменять собой Order Builder или Pre-execution Guard;

• выпускать наружу действие, не прошедшее formal execution-facing gate;

• возвращать в ядро сырой vendor-specific payload как будто это уже доменная сущность;

• напрямую мутировать Position, PortfolioState или state store;

• давать нескольким внутренним модулям параллельный некоординированный доступ к execution adapter.

11.6. Done / readiness criterion

Execution Boundary Contract считается готовым, если в ядре существует одна и только одна formal boundary-точка связи с execution adapter, никакой внутренний слой не обращается к execution adapter в обход этого контракта, а Fill Processor, Position Engine и Portfolio Engine могут строиться downstream без vendor-specific knowledge.

11.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: единый Execution Boundary Contract и Execution Coordinator как единственная точка связи ядра с execution adapter. Reserved extension seam для Захода 2: более зрелое поведение boundary under recovery / reconciliation-sensitive contours, интеграция с position-originated close routing и explicit unknown-state family. Не входит в первую реализацию: hardening-specific boundary test interfaces, mock/failure-injection family и multi-exchange abstraction.

11.8. Итог раздела

Execution Boundary Contract делает возможной честную causal chain OrderIntent → execution boundary → ExecutionReport / Fill → Fill Processor → Position → PortfolioState и защищает первую реализацию от расползания execution semantics по внутренним слоям ядра.

12. Fill / Position / Portfolio Spine Contracts

Fill / Position / Portfolio Spine образует обязательную downstream последовательность Minimal Core v1. Direction of truth flow идёт от execution facts к fill processing, от fill processing к позиции и от позиции к портфельному состоянию; ownership state changes не расползается.

12.1. Fill Processor Contract

12.1.1. Роль интерфейса

Fill Processor Contract принимает нормализованный execution-side result и переводит его в fill-driven внутреннюю основу для дальнейшего изменения позиции.

12.1.2. Upstream / downstream граница

Upstream boundary Fill Processor Contract — только Execution Boundary Contract и его нормализованный execution-side result. Downstream boundary — только Position Engine Contract.

12.1.3. Минимальный обязательный input

Минимальный input — нормализованный execution-side result, fill facts или execution facts, достаточные для чтения количества, цены и execution-side изменения, а также order / instrument lineage basis.

12.1.4. Минимальный обязательный output

Минимальный output — processed fill basis, пригодный для downstream Position Engine. Это не готовый PositionState, а достаточный внутренний result для downstream position impact reading.

12.1.5. Что интерфейс не имеет права знать или делать

• выводить позицию напрямую из StrategyIntent, RiskDecision или OrderIntent, минуя execution facts;

• принимать на себя ownership PositionState или PortfolioState;

• заниматься strategy logic, risk logic или governance reading;

• обращаться к execution adapter в обход Execution Boundary;

• подменять собой State Store и финализировать persistence boundary;

• считать status-only picture достаточной заменой fill truth там, где downstream state change должен опираться на execution facts.

12.1.6. Done / readiness criterion

Fill Processor Contract считается готовым, если downstream position path получает execution-fact basis только через отдельный Fill Processor, processed fill result достаточен для downstream position mutation without vendor-specific interpretation, а Position Engine не нуждается в догадке о том, какое execution-side событие считать источником изменения позиции.

12.1.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Fill Processor Contract и downstream path от Execution Boundary к Position Engine только через fill-processing слой. Reserved extension seam для Захода 2: связь fill processing с explicit unknown-state family и reconciliation-sensitive contours. Не входит в первую реализацию: hardening-specific idempotency contract family и replay / duplicate / fault-injection family.

12.1.8. Итог подраздела

Fill Processor Contract является первым downstream execution-fact швом Minimal Core v1 и открывает fill-driven truth flow внутри state spine.

12.2. Position Engine Contract

12.2.1. Роль интерфейса

Position Engine Contract принимает processed fill basis и строит или изменяет PositionState как агрегированное состояние торговой позиции.

12.2.2. Upstream / downstream граница

Upstream boundary Position Engine Contract — только Fill Processor Contract и его processed fill basis. Downstream boundary — только Portfolio Engine Contract и те downstream consumers, которые имеют право читать already-updated position state.

12.2.3. Минимальный обязательный input

Минимальный input включает processed fill basis, текущий relevant position state и instrument / strategy lineage basis, достаточный для отнесения execution impact к правильной позиции.

12.2.4. Минимальный обязательный output

Минимальный output — обновлённый PositionState как formal downstream position result, пригодный для Portfolio Engine.

12.2.5. Что интерфейс не имеет права знать или делать

• получать position truth напрямую из StrategyIntent, RiskDecision, OrderIntent или status-only execution picture;

• обращаться к execution adapter в обход upstream boundaries;

• подменять собой Portfolio Engine и считать portfolio/accounting effects окончательно сформированными;

• подменять собой State Store и финализировать persistence boundary;

• принимать governance decisions о trade admission или posture;

• распылять ownership позиции между несколькими модулями ядра.

12.2.6. Done / readiness criterion

Position Engine Contract считается готовым, если позиция изменяется только downstream от Fill Processor, PositionState существует как отдельный слой, а downstream Portfolio Engine получает уже обновлённую модель позиции.

12.2.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Position Engine Contract и downstream position mutation только от Fill Processor. Reserved extension seam для Захода 2: mature position-originated close routing contour, recovery / reconciliation-sensitive position reading и explicit interaction с unknown-position family. Не входит в первую реализацию: derivatives-ready position semantics, multi-strategy position ownership family и расширенные protective-management contract families.

12.2.8. Итог подраздела

Position Engine Contract является центральным owner-managed downstream слоем position truth. Он получает processed fill basis, формирует обновлённый PositionState и не подменяет собой ни Fill Processor, ни Portfolio Engine.

12.3. Portfolio Engine Contract

12.3.1. Роль интерфейса

Portfolio Engine Contract принимает already-updated PositionState и строит PortfolioState / portfolio accounting picture как агрегированный финансовый слой Minimal Core v1.

12.3.2. Upstream / downstream граница

Upstream boundary Portfolio Engine Contract — только Position Engine Contract и его updated PositionState. Downstream boundary — только State Store Contract и те downstream consumers, которые имеют право читать агрегированный PortfolioState.

12.3.3. Минимальный обязательный input

Минимальный input включает updated PositionState, relevant portfolio/account basis и execution-derived financial impact в том объёме, в котором он уже инкапсулирован в downstream position result.

12.3.4. Минимальный обязательный output

Минимальный output — обновлённый PortfolioState как агрегированный portfolio/accounting result downstream state spine.

12.3.5. Что интерфейс не имеет права знать или делать

• строить portfolio truth напрямую из StrategyIntent, RiskDecision, OrderIntent или сырого execution payload;

• подменять собой Position Engine и вычислять позицию заново;

• обращаться напрямую к execution adapter;

• подменять собой State Store и финализировать persistence mechanics вместо следующего boundary;

• принимать policy-level governance decisions;

• допускать множественные независимые portfolio truths в разных местах ядра.

12.3.6. Done / readiness criterion

Portfolio Engine Contract считается готовым, если portfolio/accounting layer получает input только downstream от Position Engine, PortfolioState существует как отдельный агрегированный result, а State Store может читать уже оформленный portfolio-level output после position update.

12.3.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный Portfolio Engine Contract и downstream aggregation только после Position Engine. Reserved extension seam для Захода 2: связь с reconciliation-sensitive portfolio reading, startup / periodic / on-error reconciliation family и broader source-of-truth policy. Не входит в первую реализацию: multi-strategy portfolio allocation family, derivatives-ready collateral / margin semantics и industrial accounting observability interfaces.

12.3.8. Итог подраздела

Portfolio Engine Contract является последним owner-managed financial layer внутри fill-driven spine Minimal Core v1.

12.4. Итог раздела

Fill / Position / Portfolio Spine Contracts образуют обязательную downstream последовательность Minimal Core v1: Execution Boundary → Fill Processor → Position Engine → Portfolio Engine → State Store.

13. State Store Contract

13.1. Роль интерфейса

State Store Contract фиксирует persistence boundary Minimal Core v1. Его роль уже и строже, чем у fill-driven spine contracts: он не создаёт новый business layer и не интерпретирует execution facts, позицию или портфель заново.

13.2. Upstream / downstream граница

Upstream boundary State Store Contract — только уже завершённый downstream spine Minimal Core v1, прежде всего updated PortfolioState и связанный с ним согласованный state result текущего contour. Downstream boundary — только Startup Reconciliation Boundary Contract и restore path запуска. State Store не должен вести произвольный downstream fan-out в business layers.

13.3. Минимальный обязательный input

Минимальный input — уже обновлённый PositionState и PortfolioState, такая форма связанного state result, которая достаточна для последующего restore path, и state revision / snapshot basis в минимальном объёме, нужном для воспроизводимого чтения состояния после рестарта.

13.4. Минимальный обязательный output

Минимальный output — воспроизводимый сохранённый state result, который startup path имеет право читать как последнюю согласованную версию minimal core state.

13.5. Что интерфейс не имеет права знать или делать

• становиться ещё одним business layer поверх Position Engine или Portfolio Engine;

• заново пересчитывать позицию, портфель или execution truth;

• обращаться к execution adapter как к обычной части runtime-flow вне restore/reconciliation boundary;

• подменять собой Startup Reconciliation и принимать решение о том, согласовано ли восстановленное состояние с внешним миром;

• принимать strategy, risk или governance decisions;

• допускать несколько независимых persistence truths для одного и того же класса состояния.

13.6. Done / readiness criterion

State Store Contract считается готовым, если после завершения fill-driven spine существует отдельная formal persistence boundary, ядро способно сохранить минимально достаточное внутреннее состояние, restore path может читать сохранённый result как последнюю согласованную state version, а Startup Reconciliation получает отдельный downstream boundary.

13.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный State Store Contract как persistence boundary и restore-readable state result для startup path. Reserved extension seam для Захода 2: более зрелая связь State Store с periodic / on-error reconciliation contours и source-of-truth integration. Не входит в первую реализацию: hardening-specific storage discipline, industrial locking / coordination semantics и broader audit / replay storage families.

13.8. Итог раздела

State Store Contract является persistence boundary Minimal Core v1, а не ещё одним business layer, и подготавливает следующий шов — Startup Reconciliation Boundary Contract.

14. Startup Reconciliation Boundary Contract

14.1. Роль интерфейса

Startup Reconciliation Boundary Contract фиксирует границу начальной сверки состояния при запуске. Он встроен в lifecycle запуска и нужен для того, чтобы система возвращала согласованный snapshot ордеров, позиции и портфеля на старте или формальный startup outcome, показывающий, что такая согласованность не достигнута.

14.2. Upstream / downstream граница

Upstream boundary Startup Reconciliation Boundary Contract — только State Store Contract и restore path запуска. Downstream boundary — только готовность первого runtime contour к продолжению работы в том объёме, который допустим для Minimal Core v1. Startup reconcile outcome не равен автоматическому допуску к торговле.

14.3. Минимальный обязательный input

Минимальный input — восстановленный minimal core state из State Store, startup scope сверки, достаточный для чтения ордеров, позиции и портфеля на старте, и минимальный внешний или восстановительный basis, необходимый для определения, не противоречит ли стартовая локальная картина самой себе и допустимому startup contour.

14.4. Минимальный обязательный output

Минимальный output — формальный startup reconciliation result, достаточный для downstream startup decision о согласованности или несогласованности восстановленного состояния. На уровне 7A этот result должен как минимум различать четыре outcome classes:

• completed_consistent;

• completed_corrected;

• failed_cannot_reconcile;

• timeout / insufficient_startup_result.

Документ 7A не превращает эти classes в governance decision, но требует, чтобы startup boundary не растворял их в одном неразличимом “startup прошёл / не прошёл”.

14.5. Что интерфейс не имеет права знать или делать

• подменять собой State Store и выполнять роль persistence layer;

• превращаться в полную reconciliation-family зрелого ядра;

• запускать periodic или on-error reconciliation как будто они уже first-class contracts первой реализации;

• мутировать PositionState или PortfolioState в обход уже согласованных downstream state layers;

• принимать strategy, risk, execution или governance decisions вместо соседних слоёв;

• считать факт завершения стартовой сверки автоматическим разрешением на normal trading flow.

14.6. Done / readiness criterion

Startup Reconciliation Boundary Contract считается готовым, если после restore path существует отдельный formal startup reconciliation step, этот step встроен в lifecycle запуска, система способна вернуть либо согласованный startup snapshot ордеров, позиции и портфеля, либо один из различимых formal startup outcomes, а первый runtime contour не начинает работу так, будто startup reconciliation вовсе не существовал. Startup reconcile outcome остаётся startup-boundary result и не превращается автоматически в governance permission for trading.

14.7. Фазовый статус контракта

Обязательно для Wave 1 / Minimal Core v1: отдельный startup-scoped reconcile step после restore path и формальный startup outcome. Reserved extension seam для Захода 2: periodic reconciliation, on-error reconciliation, Recovery Coordinator boundary и reconciliation as a normal operating loop. Не входит в первую реализацию: полная reconciliation-family зрелого ядра, scheduler/timer driven contours и hardening-specific reconciliation test interfaces.

14.8. Итог раздела

Startup Reconciliation Boundary Contract замыкает первую implementation-facing цепочку Minimal Core v1 и не подменяет собой ни persistence layer, ни полную reconciliation-family, ни governance decision о торговом допуске.

15. Сводный перечень reserved extension seams для Захода 2

Настоящий раздел не раскрывает заново смысл future contract families и не повторяет содержание разделов 6–14. Его задача — собрать в одном месте те extension seams, которые были отмечены внутри конкретных Wave 1 interface contracts как зарезервированные для Захода 2.

15.1. Full TimeframeContext contract family

Reserved seam, already marked in: Раздел 7 — Minimal MTF Input Seam Contract.

15.2. ContextAssembler / BarAlignmentPolicy / ClosedBarPolicy / FreshnessPolicy

Reserved seam, already marked in: Раздел 7 — Minimal MTF Input Seam Contract.

15.3. Context Gate

Reserved seam, already marked in: Разделы 7 и 8 — Minimal MTF Input Seam Contract; Strategy Contract.

15.4. Full unknown-state contract family

Reserved seam, already marked in: Разделы 9, 11, 12.1 и 12.2 — Risk Contract; Execution Boundary Contract; Fill Processor Contract; Position Engine Contract.

15.5. Periodic reconciliation

Reserved seam, already marked in: Разделы 13 и 14 — State Store Contract; Startup Reconciliation Boundary Contract.

15.6. On-error reconciliation

Reserved seam, already marked in: Разделы 13 и 14 — State Store Contract; Startup Reconciliation Boundary Contract.

15.7. Recovery Coordinator boundary как более широкий runtime contract

Reserved seam, already marked in: Раздел 14 — Startup Reconciliation Boundary Contract.

15.8. Source-of-truth policy как более широкая runtime contract family

Reserved seam, already marked in: Разделы 13 и 14 — State Store Contract; Startup Reconciliation Boundary Contract.

15.9. Position-originated close routing contour

Reserved seam, already marked in: Разделы 10.1, 10.2 и 12.2 — Order Builder Contract; Pre-execution Guard Contract; Position Engine Contract.

15.10. Regime layer and strategy orchestration

Reserved seam, already visible only at architectural level. Wave 1 interface layer сознательно не включает MarketRegime, StrategySelector и regime-aware routing как first-class contracts первой реализации, но этот future seam должен оставаться видимым как отдельное направление следующего этапа.

15.11. Recovery / reconciliation-sensitive behavior across execution and state spine

Reserved seam, already marked in: Разделы 10.1, 10.2, 11, 12.1, 12.2 и 12.3. Wave 1 сознательно не разворачивает эти seam-ы в полную recovery-sensitive contract family; они остаются видимыми, но отложенными.

15.12. Итог раздела

Reserved extension seams Захода 2 уже помечены внутри конкретных Wave 1 contracts, а здесь сведены в единый компактный перечень без повторного раскрытия их смысла.

16. Что сознательно не входит в 7A

16.1. Полные contract families следующего этапа

Документ №7A сознательно не включает как first-class interface contracts полноценный TimeframeContext, Context Gate, полную unknown-state family, periodic reconciliation, on-error reconciliation, более широкий Recovery Coordinator boundary и зрелую source-of-truth policy.

16.2. Hardening-specific interfaces

7A не является ни hardening-планом, ни boundary-test спецификацией. Idempotent fill processing, atomic state persistence, structured logging, mock adapters, correctness tests и fault scenario tests относятся к hardening-layer, а не к Minimal Core v1 interface layer.

16.3. Расширения beyond Minimal Core v1

Документ №7A сознательно не включает multi-instrument readiness, multi-strategy readiness, multi-exchange abstraction, derivatives expansion и иные расширения beyond Minimal Core v1.

16.4. Полевая схема реализации и транспортные детали

Документ №7A не является field-by-field schema document, API reference или transport contract specification. Input и output каждого интерфейса описываются на уровне доменных сущностей, допустимых state results и boundary meanings.

16.5. Структура репозитория, кодогенерация и naming conventions

Документ №7A не определяет структуру папок, имена файлов, конкретные имена классов, сигнатуры методов, правила импорта и иные формы прямой кодогенерации. Его роль — зафиксировать швы реализации, а не превратить интерфейсный документ в проектный scaffolding.

16.6. Итог раздела

7A сознательно ограничен интерфейсными контрактами Minimal Core v1 и не включает полные contract families следующего этапа, hardening-specific interfaces, multi-* и derivatives expansions, schema-level спецификации и структуру кода.

17. Итоговые invariants 7A

Итоговые invariants данного документа фиксируют жёсткие ограничения phase-scoped interface layer Minimal Core v1: достаточно для первой реализации, но без преждевременной канонизации временной формы первой сборки.

17.1. Интерфейсный слой является фазовым

Интерфейсные контракты 7A относятся только к Minimal Core v1 и не описывают всё будущее ядро сразу.

17.2. Один vertical slice должен быть полностью проходим

Контракты 7A должны быть достаточны для одного полного vertical slice: от нормализованного рыночного входа до persistence boundary и startup reconciliation.

17.3. Никаких обходов архитектурных швов

Ни один интерфейс 7A не имеет права допускать перескок через already-agreed layer seams ради локального удобства реализации.

17.4. Interface contract не подменяет domain contract

Интерфейсный контракт организует реализацию шва, но не переопределяет canonical entities, truth layers и их смысл.

17.5. Execution существует только через единую boundary-точку

Execution Coordinator / Execution Boundary остаётся единственной допустимой точкой связи ядра с внешним execution adapter.

17.6. Fill-driven spine обязателен

Direction of truth flow внутри state spine не может быть нарушен: execution facts идут в Fill Processor, затем в Position Engine, затем в Portfolio Engine, и только после этого — в persistence boundary.

17.7. Владение состоянием не расползается

Ни один класс состояния не должен иметь нескольких независимых владельцев внутри Wave 1 interface layer.

17.8. State Store не является business layer

Persistence boundary сохраняет и восстанавливает state result, но не создаёт новый бизнес-слой поверх Fill / Position / Portfolio spine.

17.9. Startup reconciliation ограничен startup scope

В 7A допускается только startup reconciliation boundary; periodic и on-error reconciliation не являются first-class contracts первой реализации.

17.10. Input и output описываются на доменном уровне

Контракты 7A фиксируют минимальный допустимый input/output на уровне доменных сущностей и state results, а не как полные схемы реализации.

17.11. Reserved seams должны быть видимы

Контрактные seam-ы следующего этапа должны быть явно помечены внутри конкретных Wave 1 contracts и сведены в отдельный сводный перечень.

17.12. Reserved seams не становятся обязательствами Wave 1

Видимость future seams не означает, что они уже входят в обязательный объём первой реализации.

17.13. 7A не заменяет 7B

Документ 7A фиксирует interface layer, но не превращается в implementation package plan, кодогенерацию или структуру репозитория; это задача следующего слоя.

17.14. Итог раздела

Первая реализация обязана иметь полный и читаемый набор interface contracts для Minimal Core v1, но не имеет права ни обходить согласованные швы, ни подменять domain/policy layers, ни преждевременно канонизировать будущие расширения как обязательства Wave 1.
