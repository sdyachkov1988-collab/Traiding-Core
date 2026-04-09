ТЕХНИЧЕСКИЙ ROADMAP РЕАЛИЗАЦИИ

торгового ядра

Рабочая редакция v0.9

Документ фиксирует техническую последовательность сборки Minimal Core v1, затем MTF + recovery + reconciliation-контура и завершает текущую редакцию согласованным hardening-пакетом как третьим этапом реализации. Редакция v0.9 закрывает последние редакционные замечания technical roadmap как документа и подготавливает документ к финальному freeze-аудиту.

Статус документа	Рабочая редакция v0.9 — устранены последние редакционные замечания technical roadmap как документа; версия подготовлена к финальному freeze-аудиту
Основание	Архитектурный roadmap торгового ядра v1.7
Ключевая граница	Assembly-level компромиссы первой тестовой сборки допускаются, но не канонизируются как invariants ядра и не подменяют доменные контракты roadmap
Текущий объём	Minimal Core v1 implementation plan; MTF + recovery + reconciliation plan; Hardening plan включён и структурно выровнен



1. Назначение документа

Технический roadmap реализации переводит утверждённую архитектурную модель торгового ядра в последовательность инженерных заходов. Документ задаёт порядок сборки модулей, зависимости между шагами и критерии готовности без ухода в код конкретной реализации.

Данный документ не заменяет архитектурный roadmap, не подменяет Engineering Guardrails и не описывает политику эксплуатации торгового бота. Его задача — показать, что именно реализуется первым, что появляется только после прохождения архитектурных ворот и по каким признакам текущая стадия считается завершённой.

В текущей редакции отдельно зафиксировано, что первая исполняемая стратегия для первых тестов является мультитаймфреймной. Поэтому roadmap не может трактовать Minimal Core v1 как чисто single-timeframe-only baseline. Одновременно документ сознательно не превращает временные решения первой сборки, включая возможный derived HTF path, в постоянные правила ядра.

2. Границы текущей редакции

Текущая редакция документа включает согласованные Заходы 1, 2 и 3. Hardening plan больше не является зарезервированным блоком и входит в полноценный состав текущей версии технического roadmap.

2.1. Scope текущей редакции

Входит	Не входит
Базовые доменные модели и нормализованный event flow	Multi-instrument readiness
Minimal MTF input seam для первой MTF-стратегии	Multi-strategy readiness
Strategy contract, Risk engine, Order builder и Pre-execution Guard	Regime-aware routing и orchestration
Execution boundary, Fill / Position / Portfolio spine	Multi-exchange abstraction
State store, startup reconciliation и формальный recovery contour	Derivatives expansion
Hardening пакеты correctness / state safety / observability / testability	Governance и эксплуатационные политики



3. Состав документа

№	Заход	Статус	Содержимое
1	Minimal Core v1 implementation plan	Согласован	Уточнён как MTF-first baseline без канонизации временных assembly-компромиссов
2	MTF + recovery + reconciliation plan	Согласован	Уточнены ownership TimeframeContext, source-of-truth policy и protective semantics
3	Hardening plan	Согласован	Структурно выровнен; уточнены итоговые criteria, зависимости и границы hardening-этапа



3.1. Маппинг заходов на фазы архитектурного roadmap v1.7

Ниже зафиксирован явный маппинг между техническими заходами текущего документа и фазами архитектурного roadmap v1.7. Это исключает расхождение двух документов и показывает, какую архитектурную фазу реализует каждый заход.

Заход техроадмапа	Архитектурная фаза v1.7	Смысл соответствия
Заход 1	Фаза 1 (Minimal core v1) + минимальный ранний вход в Фазу 1.5 для первой стратегии	Собирается первый исполнимый vertical slice сделки, состояние переживает рестарт, а минимальный MTF-ready seam вводится только в объёме, необходимом первой стратегии, без полной формализации MTF-контуров.
Заход 2	Фаза 1.5 (Multi-timeframe readiness) и формализация recovery / reconciliation semantics перед hardening	MTF становится формальной способностью ядра; вводятся Context Gate, unknown states, source-of-truth policy и штатные режимы reconciliation.
Заход 3	Фаза 2 (Hardening execution и state)	Укрепляются корректность обработки execution-фактов, атомарность состояния, наблюдаемость и контролируемая тестовая граница.

4. Заход 1 — Minimal Core v1 implementation plan

4.1. Назначение захода

Цель Захода 1 — определить техническую последовательность реализации Minimal Core v1 как минимально достаточного рабочего контура торгового ядра. В текущей редакции этот контур собирается как baseline для первой исполняемой стратегии, которая требует MTF support уже на раннем этапе.

Речь идёт не о полном production-hardening и не о зрелом MTF/recovery-контуре. На этом шаге строится первый исполнимый сквозной срез, достаточный для проведения первых тестов стратегии через полный жизненный цикл сделки.

В рамках захода фиксируются:

• какие модули реализуются первыми;

• в каком порядке они собираются;

• какие зависимости существуют между шагами;

• какие done criteria подтверждают завершение Minimal Core v1.

4.2. Реализация по волнам

4.2.1. Волна 1A — Domain foundation

Сначала реализуется доменный фундамент ядра. На этом шаге фиксируются базовые сущности, их идентичность, статусы и минимальные обязательные поля, необходимые для прохождения полного жизненного цикла сделки.

Состав волны	Done criteria
Instrument MarketEvent StrategyIntent RiskDecision OrderIntent ExecutionReport Fill Position PortfolioState	• Базовые сущности определены как отдельные контракты. • У сущностей есть собственная идентичность и системные оси происхождения. • Базовые статусы и status enums формально определены для сущностей, у которых lifecycle зависит от переходов состояния. • Нет смешения intent, execution и accounting-смыслов внутри одной модели.



4.2.2. Волна 1B — Event normalization and strategy entry point

После доменного фундамента реализуется нормализованный входной контур ядра. Ядро должно уметь принимать рыночное событие в едином формате и передавать его в strategy layer без зависимости от конкретной биржи или формата внешнего источника данных.

Состав	Цель	Done criteria
Event layer Типизация базовых входных событий Strategy contract	Единый вход в ядро; отделение стратегии от источника market data; переход от MarketEvent к StrategyIntent.	Ядро принимает нормализованный MarketEvent; strategy layer возвращает StrategyIntent либо явное решение ничего не делать; стратегия не обращается напрямую к adapter, state store или portfolio accounting.



4.2.3. Волна 1C — Minimal MTF input seam

Поскольку первая тестируемая стратегия является мультитаймфреймной, уже на этом этапе ядро должно получить минимально необходимый MTF-ready seam. Речь идёт не о полной формализации TimeframeContext, а о раннем шве, который позволяет первой стратегии читать согласованные HTF-входы через ядро, а не собирать их локально внутри strategy layer.

Если текущая тестовая сборка использует derived HTF path из доступного базового ряда данных, такой путь допускается как assembly-level implementation choice. Он не закрепляется как постоянный закон ядра и не ограничивает будущее расширение на другие рынки и другие контуры данных.

Для Wave 1 данный seam фиксируется в минимально достаточном объёме первой стратегии: entry-timeframe canonical input row, один согласованный HTF basis или иной минимально необходимый HTF input, closed-bar only semantics и no-look-ahead boundary. Если обязательный HTF input недоступен или не подтверждён как допустимый для чтения, стратегия не должна восстанавливать его локально и не должна получать implicit admission через обход ядра.

Состав	Цель	Done criteria
Канонический входной ряд по entry timeframe Минимальная доставка обязательных HTF-входов Closed-bar only semantics No-look-ahead boundary	Дать первой MTF-стратегии минимально достаточный входной шов без преждевременной канонизации полного MTF-контура.	Первая стратегия получает entry timeframe и обязательные HTF input через ядро; стратегия не определяет локально допустимость HTF-баров и не восстанавливает HTF basis в обход ядра; минимальный MTF input seam работает поверх нормализованного входного контура и не требует обхода ядра из strategy layer; Full TimeframeContext, ContextAssembler, BarAlignmentPolicy, ClosedBarPolicy и FreshnessPolicy как зрелая contract family ещё не считаются частью Захода 1.



4.2.4. Волна 1D — Decision pipeline

После появления StrategyIntent реализуется цепочка доменных решений между стратегией и исполнением. На этом шаге ядро должно уметь проверить намерение через риск-слой, преобразовать его в исполнимое торговое поручение и отдельно подтвердить его исполнимость непосредственно перед отправкой во внешний execution boundary.

Состав	Цель	Done criteria
Risk engine Order builder Pre-execution Guard	Отделить стратегическое решение от допустимости сделки, от параметров исполнения и от финальной предисполнительной проверки venue constraints.	StrategyIntent проходит через отдельный RiskDecision; sizing и лимиты определяются risk layer; OrderIntent формируется только из одобренного решения; ни одно поручение не уходит в execution layer без Pre-execution Guard.



Pre-execution Guard в текущей редакции отвечает за price/qty rounding по instrument spec, min_qty / min_notional, совместимость типа ордера с execution capabilities и формальный reject-state, если поручение после округления и ограничений перестаёт быть исполнимым.

4.2.5. Волна 1E — Execution and fill-driven accounting spine

После появления валидного OrderIntent реализуется центральный рабочий позвоночник ядра: execution boundary, обработка факта исполнения, позиционный и портфельный учёт.

Состав	Цель	Done criteria
Execution contract Execution Coordinator boundary Fill Processor Position Engine Portfolio Engine	Формализовать единственную точку связи ядра с execution adapter и перевести ядро на fill-driven обновление состояния.	Execution идёт через единый контракт; Position обновляется по Fill / ExecutionReport фактам; PortfolioState обновляется после изменения позиции; Position Engine на этом шаге ведёт позиционное состояние, но ещё не вводит отдельный position-originated close-routing контур — он формализуется в Заходе 2.



4.2.6. Волна 1F — State survivability

После сборки рабочего торгового контура реализуется минимальная способность ядра переживать рестарт и восстанавливать своё состояние.

Состав	Цель	Done criteria
State Store Startup Reconciliation	Сохранить минимально достаточное внутреннее состояние и встроить начальную сверку в lifecycle запуска.	Ядро восстанавливает минимальное состояние после рестарта; startup reconciliation встроен в запуск; система возвращает согласованный snapshot ордеров, позиции и портфеля на старте и по запросу диагностики.



4.2.7. Волна 1G — End-to-end acceptance slice

Финальным шагом реализуется сквозная acceptance-сборка, подтверждающая, что Minimal Core v1 собран как единый рабочий контур, а не как набор разрозненных модулей.

Состав	Цель	Done criteria
Happy-path сделки Restart/recovery acceptance Проверка execution boundary Проверка separation of concerns	Подтвердить, что минимальный торговый контур действительно собран как единый доменный процесс и уже способен провести первую MTF-стратегию через рабочий vertical slice.	Один MarketEvent проходит путь до обновления позиции и портфеля; первая MTF-стратегия использует ядро как источник согласованных входов; замена adapter не требует переписывания strategy logic; после рестарта ядро восстанавливает состояние и проходит startup reconciliation.



4.3. Граница Захода 1

Заход 1 завершает сборку первого исполнимого сквозного среза для первой мультитаймфреймной стратегии, но ещё не формализует MTF как зрелую архитектурную способность ядра. На этом этапе допускается ограниченный MTF-ready seam, достаточный для первого тестового контура.

Полноценная модель TimeframeContext, единые политики выравнивания и свежести, Context Gate, развитая reconciliation-модель, explicit unknown states и зрелая protective/recovery semantics относятся к Заходу 2.

4.4. Зависимости между шагами

Порядок реализации не является произвольным. Каждый шаг открывает возможность для следующего и задаёт обязательную опору для последующих модулей.

• Core models являются фундаментом для всех остальных шагов.

• Event layer не реализуется раньше, чем зафиксированы базовые доменные сущности.

• Волна 1C не реализуется раньше Волны 1B, потому что Minimal MTF input seam опирается на уже существующий нормализованный входной контур и не подменяет будущий зрелый TimeframeContext.

• Strategy contract не должен зависеть от execution, fills, persistence и адаптерной логики.

• Risk engine зависит от StrategyIntent, instrument rules и PortfolioState, но не от adapter layer.

• Order builder зависит только от approved RiskDecision и execution constraints.

• Pre-execution Guard появляется раньше передачи OrderIntent в execution boundary.

• Execution contract должен появиться раньше Fill Processor, потому что именно он задаёт формальную execution boundary.

• Fill Processor должен быть введён раньше Position Engine, потому что позиция изменяется по фактам исполнения, а не по намерению.

• Position Engine должен быть введён раньше Portfolio Engine, потому что портфельный учёт опирается на уже обновлённую модель позиции.

• State Store должен появиться раньше Startup Reconciliation.

• End-to-end acceptance допустим только после сборки полного минимального контура.

4.5. Итоговые done criteria Minimal Core v1

• Существует единый сквозной lifecycle: MarketEvent → StrategyIntent → RiskDecision → OrderIntent → ExecutionReport / Fill → Position → PortfolioState.

• Strategy, Risk, Order construction, Pre-execution Guard, Execution, Fill Processing, Position Management и Portfolio Accounting существуют как разные технические и доменные слои.

• Обновление позиции и портфеля происходит по факту исполнения, а не по факту появления сигнала.

• Execution adapter подключается через единый execution boundary, а не через прямые вызовы из внутренних модулей ядра.

• Минимальное состояние ядра сохраняется и переживает рестарт процесса.

• На старте системы выполняется startup reconciliation как обязательная часть запуска.

• Первая MTF-стратегия может пройти через Minimal Core v1 без вынужденной локальной сборки HTF-контекста внутри strategy layer.

• На выходе Захода 1 формально существуют исполнимый Minimal Core v1 contour, startup reconciliation и ранний MTF input seam, тогда как полноценный TimeframeContext, Context Gate, periodic/on-error reconciliation, explicit unknown-state family и protective close loop / position-originated close routing contour ещё отсутствуют как first-class capabilities первой реализации.

4.6. Что сознательно откладывается на следующие заходы

Заход 1 должен закончиться до начала углубления архитектуры в сторону зрелого MTF-контура, расширенной recovery-модели и hardening-пакета.

• полноценный TimeframeContext и Context Gate;

• полная reconciliation-family как зрелая модель режимов сверки (periodic, on-error и более широкий runtime contour поверх уже существующего startup reconciliation);

• unknown states;

• protective close loop;

• idempotent fill processing hardening;

• atomic state persistence rules;

• structured logging;

• mock adapters;

• correctness tests;

• fault scenario tests.

5. Заход 2 — MTF + recovery + reconciliation plan

5.1. Назначение захода

Заход 2 собирает воспроизводимый контекстный и recovery-контур, который стоит между Minimal Core v1 и отдельным hardening-пакетом. Его задача — формально ввести multi-timeframe semantics, admission through Context Gate, штатную reconciliation-модель, explicit unknown states и protective close loop.

На этом шаге MTF становится не частной поддержкой первой стратегии, а формально определённой способностью ядра. Одновременно recovery и reconciliation перестают быть только аварийной реакцией и превращаются в нормальный сервисный контур системы.

5.2. Базовые решения текущей редакции

В текущей редакции базовым техническим решением считается instrument-scoped canonical timeframe store, поверх которого стратегия получает согласованный read-only TimeframeContext. Источник HTF-представлений в первой сборке может быть либо прямым потоком старших таймфреймов, либо производным представлением из доступного базового ряда, если такой путь допустим текущим контуром данных.

Минимальный технический контракт TimeframeContext в рамках техроадмапа включает: context_id, instrument_id, entry_timeframe, timeframe_set, сведения о последних допустимых closed bars по каждому таймфрейму, обязательному для текущего strategy/context contract, freshness / readiness flags и ссылку на действующую alignment policy. Детальная field-level спецификация может уточняться далее, но этот минимум должен быть формально определён уже на этапе Захода 2.

Для ордеров, fills, балансов и факта внешнего исполнения источником истины считается внешняя площадка. Для локально восстанавливаемых market-data представлений и производного TimeframeContext источником истины считается canonical instrument-scoped data layer. Для позиции как торгово значимого внешнего состояния источником истины считается внешний execution state; локальная Position-модель обязана согласовываться с ним через reconciliation, а при критическом противоречии новые торговые действия блокируются до explicit reconcile / safe-mode outcome.

5.3. Граница Захода 2

Заход 2 завершает перевод MTF и recovery/reconciliation semantics из частных решений первой сборки в формально определённые способности ядра. На выходе этого захода система должна иметь явный TimeframeContext, Context Gate, warmup/readiness policy, unknown state model, source-of-truth policy и штатные режимы reconciliation. При этом Заход 2 ещё не внедряет hardening execution/state и не подменяет Engineering Guardrails; hardening-механизмы передаются в Заход 3 как следующий отдельный шаг.

5.4. Реализация по волнам

5.4.1. Волна 2A — MTF foundation

Сначала реализуется multi-timeframe foundation ядра. На этом шаге MTF-контур выносится из локальной логики стратегий в формальные доменные контракты и политики.

Состав	Цель	Done criteria
TimeframeContext ContextAssembler BarAlignmentPolicy ClosedBarPolicy FreshnessPolicy TimeframeSyncEvent	Сделать MTF-контур частью ядра, формально определить допустимость HTF/LTF данных и убрать плавающую трактовку closed bars и freshness.	MTF-стратегия получает готовый TimeframeContext от ядра; доступность данных определяется формальными политиками; одинаковый набор входных баров даёт одинаковый контекст; выбор HTF-path остаётся assembly-level choice, а не invariant ядра.



5.4.2. Волна 2B — Trading admission through Context Gate

После формализации TimeframeContext вводится единый входной барьер перед стратегией. Context Gate принимает решение о допуске, переносе или отклонении цикла на основании полноты и допустимости контекста. Порог warmup задаётся как формальное требование контракта контекста / стратегии и исполняется ядром, а не локальной логикой стратегии.

Состав	Цель	Done criteria
Context Gate Reject / defer reasons Session / maintenance / gap checks Warmup and readiness checks	Не пускать стратегию на неполном или устаревшем контексте и сделать отказ в обработке формальным решением ядра.	Context Gate может явно допустить, отложить или отклонить торговый цикл; причины решения фиксируются как часть доменной логики; gate проверяет closed-bar availability, отсутствие look-ahead, допустимость удерживаемого HTF-значения и формально заданный warmup threshold. До достижения warmup trade admission не разрешается.



5.4.3. Волна 2C — Unknown states and safe recovery semantics

После появления базового MTF-контекста и входного gate ядро должно формально признать неопределённость как отдельную категорию состояния. Сначала определяется, какие unknown / stale / incomplete states допустимы как отдельные классы, какие действия они блокируют и в какие failure-path система переводится до начала автоматической сверки.

Состав	Цель	Done criteria
Unknown order state Unknown position state Stale context Incomplete external confirmation Safe-mode / freeze semantics	Запретить ложную уверенность и определить, какие состояния считаются неизвестными, какие действия они блокируют и в какой failure-path система обязана перейти до сверки.	Unknown states распознаются явно; доменная модель не подменяет их нормальными статусами; до reconcile outcome система использует формализованные freeze / safe-mode / read-only semantics.



5.4.4. Волна 2D — Reconciliation as a normal operating loop

После формализации unknown states reconciliation превращается из редкого аварийного сценария в штатный сервисный контур. Здесь отдельно фиксируются режимы startup / periodic / on-error, Recovery Coordinator boundary, триггеры запуска, доменный вход результата сверки и поведение системы, если reconcile outcome конфликтует с активным торговым состоянием.

Для целей данного roadmap важно различать не только режимы запуска reconciliation, но и ownership запуска: startup reconciliation относится к lifecycle старта системы, periodic reconciliation может инициироваться scheduler/timer contour, а on-error reconciliation запускается только при явно распознанном failure / ambiguity signal. Подробная policy-интерпретация reconcile outcome относится к Trading Governance, а не к данному документу.

Состав	Цель	Done criteria
Startup reconciliation Periodic reconciliation On-error reconciliation Recovery Coordinator boundary Source-of-truth policy	Развести режимы сверки по назначению, определить триггеры Recovery Coordinator, доменный интерфейс reconcile outcome и поведение системы при конфликте результата сверки с активным торговым состоянием.	Reconciliation существует как три режима одной способности ядра; Recovery Coordinator запускается по старту, scheduler/timer, error-signal или операторской команде; reconcile outcome входит в систему через доменные контракты; при конфликте с активным торговым состоянием новые действия блокируются до явного resolve path.



5.4.5. Волна 2E — Position-originated close routing contour

На этом шаге формализуется routing-контур для close intent, который возникает в position-management слое. Речь идёт не о частной торговой механике конкретной стратегии, а о доменном маршруте Position Engine → Order Builder → Pre-execution Guard → Execution Coordinator и о правилах обработки невозможности исполнения такого intent.

Важно явно зафиксировать фазовую границу: данный contour не относится к Minimal Core v1 и появляется только после завершения Захода 1 как часть более зрелой recovery/protective semantics. Его введение не означает, что Wave 1 уже обязан поддерживать fully formalized protective close loop.

Если такой close intent не проходит Pre-execution Guard, система не должна оставлять ложное ощущение защищённости. Reject или inability-to-execute в этом контуре переводятся в явный reject / reconcile / safe-mode путь согласно правилам текущей сборки.

Состав	Цель	Done criteria
Position-originated close intent rules Маршрут Position Engine → Order Builder → Pre-execution Guard → Execution Coordinator Связь с Portfolio / reconciliation semantics	Зафиксировать routing contour для close intent из position-management слоя без повторного strategy-entry цикла и без описания частной торговой механики конкретной стратегии.	Position Engine может инициировать close intent независимо от нового entry-сигнала; маршрут проходит через штатные доменные швы; Pre-execution Guard проверяет venue-validity и не допускает silent failure; reject такого intent переводится в явный reject / reconcile / safe-mode path.



5.5. Зависимости между шагами

Заход 2 не является автономным стартом с нуля. Он строится поверх уже собранного Minimal Core v1 и подготавливает систему к последующему hardening-пакету.

• Заход 2 не стартует, пока Minimal Core v1 не собран и startup reconciliation уже работает предсказуемо.

• TimeframeContext и его политики должны быть введены раньше Context Gate, потому что gate не может валидировать неформализованный контекст.

• Context Gate должен появиться раньше, чем стратегия начнёт считаться MTF-ready на архитектурном уровне.

• Periodic и on-error reconciliation не вводятся без формального Recovery Coordinator boundary.

• Source-of-truth policy должен быть зафиксирован до широкого использования reconciliation результатов в runtime-логике.

• Unknown state model должен быть описан раньше, чем reconciliation / Recovery Coordinator начнут принимать решения по конфликтным состояниям.

• Position-originated close routing contour опирается на уже работающие Position Engine, Order Builder, Pre-execution Guard, Execution Coordinator и Portfolio Engine.

• Hardening Захода 3 не должен начинаться, пока TimeframeContext, ClosedBarPolicy и FreshnessPolicy не стали воспроизводимыми внутри ядра.

5.6. Итоговые done criteria Захода 2

• MTF-стратегия получает единый воспроизводимый TimeframeContext от ядра.

• Доступность HTF/LTF данных определяется формальными политиками ядра, а не локальной логикой стратегии.

• Context Gate может явно допустить, отложить или отклонить торговый цикл по формализованным причинам.

• Reconciliation существует как три режима одной способности ядра: startup / periodic / on-error.

• По классам состояния явно определён источник истины, и система не пытается скрыто “мирить” конфликтующие модели без формальной политики.

• Unknown states распознаются явно и не маскируются под нормальные статусы.

• Position-management слой может передать close intent в штатный order / execution path без обхода доменных швов и без silent failure при невозможности исполнения.

• Формально определены TimeframeContext, Context Gate, unknown state model, source-of-truth policy и штатные режимы reconciliation; для каждого из этих блоков существует отдельный проверяемый readiness-результат.

5.7. Что передаётся в Заход 3

На выходе Захода 2 в следующий этап передаются именно те механизмы, которые относятся уже не к формализации MTF/recovery semantics, а к инженерному hardening-слою:

• idempotent fill processing;

• atomic state persistence;

• structured logging;

• mock adapters;

• correctness tests;

• fault scenario tests.

6. Заход 3 — Hardening plan

6.1. Назначение захода

Hardening plan переводит ядро из состояния функционально собранного контура в состояние инженерно укреплённой системы. На этом шаге усиливаются correctness, устойчивость состояния, наблюдаемость и проверяемость ядра, чтобы дальнейшее масштабирование не происходило поверх хрупкой execution/state-модели.

В рамках захода фиксируются:

• какие hardening-механизмы вводятся;

• в каком порядке они появляются;

• какие зависимости между ними обязательны;

• по каким done criteria подтверждается инженерная устойчивость ядра.

6.2. Границы захода

Данный заход не подменяет следующие фазы roadmap и не превращается в multi-instrument или multi-strategy expansion. Его область — correctness of execution facts, state safety, observability и testability на уже собранной модели Minimal Core v1 и формализованном MTF/recovery/reconciliation-контуре.

6.3. Реализация по волнам

6.3.1. Волна 3A — Correctness of execution facts

Сначала усиливается корректность обработки execution-фактов. На этом шаге вводится idempotent fill processing, защита от повторной доставки одного и того же execution report, безопасная повторная обработка partial fills и гарантии того, что один и тот же факт исполнения не изменяет позицию и портфель повторно.

Состав	Цель	Done criteria
Idempotent fill processing Duplicate execution report handling Partial-fill reprocessing safety	Не допустить повторного изменения позиции, портфеля и истории ордера при повторной доставке одного и того же execution-факта.	Повторный приём одного и того же fill / execution report не мутирует состояние повторно; identity обработанного события отслеживается формально; duplicate и partial paths обрабатываются детерминированно.

6.3.2. Волна 3B — State safety

После стабилизации execution-фактов усиливается модель хранения состояния. На этом шаге вводится atomic state persistence, дисциплина snapshot/write и формальная граница согласованности между orders, processed events, position state и portfolio state, чтобы система не оставалась в частично записанном состоянии после сбоя.

Состав	Цель	Done criteria
Atomic state persistence Write / commit discipline Consistency boundary между order / position / portfolio / processed events	Убрать риск частично записанного состояния и гарантировать восстановление только из согласованного snapshot.	Состояние либо фиксируется как согласованный набор сущностей, либо не считается записанным; после рестарта система не читает полуобновлённый state; restore path определён формально.

6.3.3. Волна 3C — Observability

Далее вводится наблюдаемость как штатная инженерная способность ядра. Structured logging должен охватывать жизненный цикл intent / order / fill / position / reconciliation, а минимальный контракт structured log обязан включать timestamp, event_type, entity_id или lineage-id, decision/outcome и reason.

Состав	Цель	Done criteria
Structured logging Reason fields Lineage / correlation identifiers Logging of reconcile and failure transitions	Сделать жизненный цикл сделки и recovery-сценарии диагностируемыми без чтения хаотичных текстовых логов.	Каждое значимое решение логируется структурированно; минимальный контракт лога включает timestamp, event_type, entity_id или lineage-id, decision / outcome и reason; переходы в reject / reconcile / safe-mode также логируются.

6.3.4. Волна 3D — Controllable test boundary

После появления structured observability формируется контролируемая тестовая граница. Mock adapters и mock execution boundary позволяют изолированно проверять ядро без реальной биржи, воспроизводить детерминированные ответы адаптера и вводить управляемые failure-инъекции без разрушения доменной модели.

Состав	Цель	Done criteria
Mock adapters Mock execution boundary Deterministic responses Failure-injection hooks	Дать ядру контролируемую внешнюю границу для инженерных тестов без зависимости от реальной площадки.	Тестовая граница умеет воспроизводить accept / reject / partial / timeout / state-mismatch сценарии; ответы детерминированы; основная часть hardening-тестов запускается без реальной биржи.

6.3.5. Волна 3E — Correctness tests

Далее строится слой correctness tests. Он должен подтверждать не просто факт работы контура, а правильный смысл вычислений, тайминга, округления, recovery-переходов, protective conflict semantics и сопоставимость режимов исполнения.

Состав	Цель	Done criteria
Correctness test suites Contract checks for context / timing / sizing / routing Verification of supported execution contours	Подтвердить, что ядро не только работает, но и делает это с правильным смыслом доменных переходов и ограничений.	Обязательные корзины корректности проходят на поддерживаемых контурах; контракты контекста, timing, sizing и close-routing проверяются отдельно от fault testing.
Корзина проверок	Что должно подтверждаться
Market data and MTF correctness	Корректность HTF-path для текущей сборки; если используется derived HTF path — корректность ресэмплинга, closed-bar semantics, отсутствие look-ahead, допустимость удерживаемого HTF-значения и warmup.
Signal timing correctness	Сигнал фиксируется только после допустимого факта готовности контекста; стратегия не узнаёт данные раньше положенного; entry и execution timing имеют одинаковый смысл на поддерживаемых контурах исполнения.
Context delivery correctness	Проверяется, что done criteria Волны 2A исполняются на уровне доставки контекста: ядро передаёт стратегии только допустимый closed-bar-aware контекст, а alignment, freshness и readiness semantics не зависят от локальной логики конкретной стратегии.
Sizing and venue-constraint correctness	Capital & sizing correctness, округление qty/price, instrument precision, min_qty, min_notional и execution constraints проверяются до отправки ордера и не смешиваются с самой risk-моделью.
Close-routing correctness	Если конкретная сборка использует position-originated close intents, их маршрут через Order Builder → Pre-execution Guard → Execution Coordinator трактуется одинаково и не нарушает позиционные и учётные инварианты.
Accounting and execution consistency	Поддерживаемые execution contours не расходятся по смыслу правил исполнения, округления, учёта и обработки close-routing.



6.3.6. Волна 3F — Fault scenario tests

Финальным шагом вводятся fault scenario tests. Здесь проверяются duplicate reports, partial fills, timeout или отсутствие внешнего подтверждения, stale context, state mismatch, adapter inconsistency, конфликтующие close-routing scenarios, рестарт в середине in-flight lifecycle и reconcile после ошибки, чтобы ядро демонстрировало корректное поведение не только на happy-path.

Состав	Цель	Done criteria
Fault scenario tests Failure-injection cases Recovery / safe-mode assertions	Проверить, что система проходит через неблагоприятные сценарии без скрытой порчи состояния и без ложной уверенности.	Отказные сценарии переводят систему в явные failure / reconcile / safe-mode paths; silent corruption не допускается; реакции на timeout, duplicate, stale context и restart проверяются формально.

6.4. Зависимости между шагами

Hardening не может начинаться как автономная работа поверх плавающей основы. Он строится на уже собранных доменных, MTF и recovery-контрактах и усиливает их в строго определённой последовательности.

• Заход 3 не стартует, пока завершены Заход 1 и Заход 2: без минимального торгового контура и формализованной MTF/recovery-семантики hardening будет укреплять нестабильную основу.

• Idempotent fill processing должен быть зафиксирован раньше полноценных correctness и fault tests, потому что именно он защищает accounting spine от повторной доставки execution-событий.

• Atomic state persistence должен появиться раньше recovery и fault testing, иначе сценарии рестарта и reconciliation будут проверять нестабильную модель хранения.

• Structured logging должен быть введён раньше широкого fault testing, иначе деградационные сценарии будет трудно диагностировать и воспроизводимо интерпретировать.

• Mock adapters должны появиться раньше широкого тестового покрытия, потому что именно они задают контролируемую внешнюю границу для проверок ядра.

• Correctness tests логически предшествуют fault scenario tests: сначала подтверждается правильность нормального поведения, затем устойчивость к отказам и неопределённости.

6.5. Итоговые done criteria Захода 3

• Повторный приём одного и того же fill или execution report не приводит к повторному изменению позиции, портфеля и истории учёта.

• State persistence не оставляет систему в частично записанном состоянии после сбоя и допускает восстановление согласованного локального state.

• Все ключевые этапы lifecycle имеют structured logs с причинами решений и идентичностью доменных сущностей.

• Ядро тестируется через mock execution boundary без прямой зависимости от реальной биржи.

• Correctness tests подтверждают lifecycle и accounting, а также timing semantics, MTF-context correctness, sizing/rounding correctness и корректность close-routing на поддерживаемых контурах исполнения.

• Fault scenario tests подтверждают корректное поведение при timeout, duplicate, partial fill, stale context, конфликтующих close-routing сценариях, рассинхроне и рестарте в неблагоприятной точке.

• Для каждого hardening-механизма существует самостоятельный проверяемый criterion или test contour: idempotency, atomic persistence, structured logging, mock boundary, correctness suite и fault suite подтверждены отдельно.

6.6. Что сознательно не входит в Заход 3

Чтобы не смешивать уровни документов и фаз развития ядра, следующие направления остаются предметом последующих фаз roadmap и не входят в текущий hardening-пакет:

• multi-instrument readiness;

• multi-strategy readiness;

• regime-aware routing;

• multi-exchange abstraction;

• derivatives expansion;

• governance и эксплуатационные политики.

7. Итог текущей редакции

Редакция v0.9 закрывает последние редакционные замечания предыдущей версии: синхронизирует статус в метаданных с текущей редакцией, выравнивает оформление зависимостей внутри Захода 1 и убирает лишнее дублирование контекстного MTF-first тезиса между метаданными и вводной частью документа.

Дополнительно в данной редакции: удалена устаревшая фраза о статусе Engineering Guardrails как ещё не утверждённого документа; уточнены done criteria Волны 1C с явной фиксацией минимального состава MTF seam для Wave 1 и запретом на локальное восстановление HTF basis в обход ядра; расширены итоговые done criteria Захода 1 с перечнем способностей, которые сознательно не считаются частью первой реализации.

Дальнейшее изменение этого документа допускается только после отдельного согласования следующего захода или новой редакции документа.
