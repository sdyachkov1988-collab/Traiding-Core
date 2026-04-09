Engineering Guardrails
Core v1 Engineering Rules

Документ №3 в комплекте документов торгового ядра
Версия v0.8



Статус	Рабочая редакция v0.8
Текущий scope	Раскрыты Заход 1 — Core invariants, Заход 2 — Observability and traceability rules и Заход 3 — Boundary and safety rules
Роль документа	Фиксирует обязательные инженерные правила ядра, а не порядок реализации
Связь с комплектом	Следует после архитектурного roadmap и технического roadmap
Основание	Архитектурный roadmap торгового ядра v1.7 и Technical Roadmap реализации v0.9



1. Назначение и место документа

Engineering Guardrails — это не roadmap реализации и не повтор технического roadmap. Этот документ фиксирует набор обязательных инженерных правил Core v1, нарушение которых делает ядро инженерно ненадёжным даже при формально рабочем торговом цикле.

Документ работает как слой жёстких ограничений: он определяет, что в ядре допустимо, что недопустимо и как понять, что правило соблюдено.

2. Структура документа

Документ строится по трём заходам. На версии v0.8 подробно раскрыты Заход 1 — Core invariants, Заход 2 — Observability and traceability rules и Заход 3 — Boundary and safety rules.

Заход	Тема	Что покрывает	Статус редакции
1	Core invariants	Global IDs, UTC-aware datetime, Decimal, atomic state writes, idempotent Fill Processor	Раскрыт
2	Observability and traceability rules	Structured logging with reason, StrategyIntent metadata, Context Gate rejection reasons, lineage decision/risk/order/fill/position	Раскрыт
3	Boundary and safety rules	MockExecutionAdapter as boundary test, single source of truth for state, execution behind interface, timeout/unknown state handling, minimal storage and locking discipline	Раскрыт

3. Заход 1 — Core invariants

3.1. Назначение захода

Цель данного захода — зафиксировать базовые инженерные инварианты Core v1, которые обязательны для всех модулей торгового ядра независимо от стратегии, внешнего адаптера, режима исполнения и контура запуска.

Данный заход не описывает порядок реализации и не заменяет технический roadmap. Его задача — определить минимальный набор правил, нарушение которых делает ядро инженерно ненадёжным даже при формально рабочем торговом цикле.

Эти правила имеют приоритет над локальным удобством реализации, скоростью разработки и частными компромиссами конкретной сборки.

3.2. Границы захода

Входит в scope	Не входит в scope
global internal IDs	structured logging
UTC-aware datetime only	lineage и traceability rules
Decimal only	boundary rules для execution adapters
atomic state writes	timeout / unknown state handling
idempotent Fill Processor	extended storage / locking discipline
	observability rules шире минимального инвариантного уровня
	mock adapters
	paper/testnet execution contours

3.3. Статус инвариантов

Каждый инвариант данного раздела трактуется как обязательное правило ядра.

• модуль не считается корректным, если он нарушает хотя бы один из инвариантов;

• локальная работоспособность не отменяет архитектурную некорректность;

• нарушение инварианта должно рассматриваться как инженерный дефект, а не как допустимое упрощение.

3.4. Инвариант 1. Global internal IDs

Смысл

Все ключевые доменные сущности ядра должны иметь собственную внутреннюю идентичность, независимую от внешней площадки, стратегии и формата внешних сообщений. Ядро не должно строить связность доменных объектов только на основании внешних order ids, временных меток, символов, цен или иных неустойчивых признаков.

Что обязательно

• Каждая ключевая доменная сущность имеет собственный internal ID.

• Внутренние идентификаторы используются как каноническая ось связывания доменных объектов.

• Внешние exchange / broker identifiers хранятся как внешние атрибуты, но не заменяют внутреннюю идентичность.

• Минимально это правило распространяется на MarketEvent, StrategyIntent (до harmonization pass — operational name decision-layer), RiskDecision, OrderIntent, ExecutionReport как раннее execution-side update name, Position, Portfolio snapshot / state revision, Fill processing record и recovery / reconciliation records, если они влияют на доменное состояние. Если конкретная реализация уже различает OrderState и/или ExecutionEvent как отдельные доменные сущности вместо единого раннего ExecutionReport, требование internal identity распространяется и на них.

Что запрещено

• Использовать внешний order_id или client_order_id как единственный идентификатор доменной сущности.

• Связывать сущности только по комбинациям вроде symbol + timestamp + price.

• Считать внешнюю execution identity достаточной для восстановления внутренней причинно-следственной цепочки.

Где применяется

• state model

• order / fill processing

• reconciliation

• recovery

• lineage между доменными решениями

Минимальный критерий соблюдения

• Любая ключевая доменная сущность Core v1 имеет собственный internal ID.

• По внутренним идентификаторам можно восстановить происхождение решения и его путь по ядру.

• Потеря внешнего идентификатора не разрушает внутреннюю доменную связность состояния.

3.5. Инвариант 2. UTC-aware datetime only

Смысл

Ядро должно использовать единую и однозначную модель времени. Все временные метки хранятся, сравниваются, сериализуются и восстанавливаются как timezone-aware datetime в UTC.

Что обязательно

• Все timestamps в событиях, fills, execution reports, state snapshots, reconciliation records и recovery records являются UTC-aware.

• Внутреннее сравнение времени выполняется только в одной временной системе.

• Сериализация и десериализация времени сохраняют UTC-смысл без потери timezone information.

Что запрещено

• Naive datetime.

• Смешение UTC и локального времени в одной доменной модели.

• Использование локального machine time как канонического времени ядра.

• Хранение времени только строками без нормализованного UTC-aware представления.

Где применяется

• event layer

• execution / fill facts

• state persistence

• reconciliation

• recovery

• audit-relevant state transitions

Минимальный критерий соблюдения

• Все доменные timestamps Core v1 являются UTC-aware.

• При чтении состояния, событий и execution facts ядро не требует догадки о timezone.

• Одинаковые события времени трактуются одинаково независимо от машины, окружения и локальной timezone-конфигурации.

3.6. Инвариант 3. Decimal only

Смысл

Все финансово значимые величины ядра должны использовать точную арифметику. Цены, количества, комиссии, балансы, PnL, risk amounts и связанные расчётные значения не должны храниться и обрабатываться на float.

Что обязательно

• Для всех финансово значимых полей используется Decimal.

• Округление и квантизация выполняются явно, в соответствии с instrument spec и execution constraints.

• Переход между “сырой величиной” и “исполняемой величиной” оформлен как явная операция, а не как побочный эффект типа данных.

Что запрещено

• float в доменной модели ядра.

• Скрытые преобразования Decimal → float → Decimal.

• Неявное округление по ходу вычислений.

• Использование бинарной арифметики для qty, price, fee, pnl и balances.

Где применяется

• order sizing

• execution preparation

• fill processing

• position updates

• portfolio accounting

• reconciliation comparisons, если сравниваются финансовые значения

Минимальный критерий соблюдения

• Все финансово значимые поля Core v1 используют Decimal.

• Округление выполняется только явно.

• Доменная корректность расчётов не зависит от случайных эффектов плавающей точки.

3.7. Инвариант 4. Atomic state writes

Смысл

Связанные изменения состояния должны фиксироваться как единая согласованная операция. Ядро не должно оставлять после записи частично применённое состояние, в котором одни доменные сущности уже обновлены, а другие ещё нет.

Что обязательно

• Минимальный связанный state update записывается атомарно.

• Запись либо завершена полностью, либо не признаётся валидной.

• После рестарта ядро видит только последний согласованный state, а не промежуточную полуобновлённую комбинацию.

	Для Core v1 минимальный атомарный набор включает как минимум: фиксацию обработанного execution fact / processing marker, соответствующее изменение Position (если оно возникает), соответствующее изменение PortfolioState / accounting state и запись новой state revision / snapshot boundary.

Что запрещено

• Несогласованная раздельная запись позиции, портфеля и обработанных execution facts.

• Partial success без явного failure-state.

• Признание state valid после неполного commit.

• Обновление “по кускам”, если эти куски должны интерпретироваться как единое доменное изменение.

Где применяется

• state store

• fill-driven updates

• position / portfolio transitions

• reconciliation commit

• recovery after restart

Минимальный критерий соблюдения

• Минимальный атомарный набор доменных изменений определяется явно.

• После сбоя ядро либо видит предыдущую согласованную версию state, либо следующую полностью завершённую.

• Нельзя получить состояние, в котором один и тот же execution fact уже изменил Position, но ещё не изменил PortfolioState или журнал обработанных фактов.

3.8. Инвариант 5. Idempotent Fill Processor

Смысл

Повторная доставка одного и того же fill или эквивалентного execution fact не должна повторно менять позицию, портфель и учётное состояние. Идемпотентность требуется не на уровне логов, а на уровне реальных доменных эффектов.

Что обязательно

• Fill Processor умеет определять, что execution fact уже был обработан.

• Повторный приём дубликата не вызывает повторного изменения qty, avg entry, pnl, commissions, reserved capital и связанных эффектов.

	Для Core v1 already-processed определяется по устойчивой нормализованной execution identity: предпочтительно по внешнему fill_id / execution_id после нормализации; если такая identity недоступна, используется детерминированный persisted fingerprint, вычисляемый из достаточного набора атрибутов execution fact.

• Контроль already-processed состояния является частью доменной обработки, а не внешним “надеемся, что дубликатов не будет”.

Что запрещено

• Повторное применение одного и того же fill.

• Зависимость корректности от предположения, что биржа не пришлёт duplicate report.

• Повторное изменение Position или PortfolioState при второй доставке того же execution fact.

• Идемпотентность только в логе, но не в state effects.

Где применяется

• fill processing

• execution report handling

• state update pipeline

• recovery / replay

• reconciliation after communication faults

Минимальный критерий соблюдения

• Один и тот же fill, доставленный повторно, не меняет итоговый state второй раз.

• Повторная доставка не искажает qty, avg entry, pnl, fees и balances.

• Идемпотентность проверяется именно по доменным последствиям обработки.

3.9. Приоритет инвариантов над локальным удобством

Инварианты Core v1 не могут обходиться ради:

• ускорения локальной разработки;

• временного удобства конкретной стратегии;

• особенностей одного execution adapter;

• сокращения объёма кода в отдельном модуле;

• решений вида “потом поправим” в state, time и accounting logic.

Если реализация требует нарушить один из инвариантов, это означает не допустимое упрощение, а неверную инженерную форму решения.

3.10. Минимальная проверка соблюдения

Каждый инвариант должен быть проверяем хотя бы одним из следующих способов:

• через code review rule;

• через unit/integration test;

• через контракт domain model;

• через state persistence rule;

• через replay / duplicate handling check для execution facts.

Инвариант считается реально существующим только тогда, когда его соблюдение можно проверить, а нарушение — обнаружить.

3.11. Итог захода

Результатом Захода 1 должен стать набор обязательных инженерных правил Core v1, которые:

• не зависят от частной стратегии;

• не зависят от конкретной биржи;

• не зависят от конкретной сборки запуска;

• образуют минимальный инженерный фундамент для следующих заходов документа.

4. Заход 2 — Observability and traceability rules

4.1. Назначение захода

Цель данного захода — зафиксировать минимальные инженерные правила наблюдаемости и трассируемости Core v1, которые делают доменные решения ядра объяснимыми, проверяемыми и пригодными для диагностики.

Этот заход не вводит внешние monitoring systems, dashboards или эксплуатационные alerting-практики. Его задача — уже на уровне ядра определить, какие данные о решениях, отказах и переходах состояния должны сохраняться и быть доступны для анализа.

Если Заход 1 фиксирует инженерную корректность ядра как системы идентичности, времени, точной арифметики, атомарности и идемпотентности, то Заход 2 фиксирует инженерную объяснимость ядра: что произошло, почему это произошло и как один доменный шаг связан со следующим.

4.2. Границы захода

Входит в scope	Не входит в scope
structured logging with reason	dashboards и внешние monitoring systems
StrategyIntent metadata как observability / traceability rule	alerting rules
Context Gate rejection reasons	retention policy логов
lineage between StrategyIntent / equivalent Decision identity, RiskDecision, OrderIntent, Fill and Position	storage / locking discipline
минимальная проверка соблюдения traceability-правил	timeout / unknown state handling
	execution adapter boundary rules
	business analytics
	live governance
	эксплуатационные отчёты и human-facing monitoring workflows

4.3. Статус observability-правил

Каждое observability / traceability rule данного раздела трактуется как обязательное инженерное правило ядра.

• модуль не считается корректным, если его ключевые решения не наблюдаемы и не трассируемы;

• отсутствие объяснимости считается инженерным дефектом, а не косметическим недостатком;

• локально рабочая торговая логика не считается достаточной, если невозможно восстановить путь решения и причину отказа или перехода состояния.

4.4. Правило 1. Structured logging with reason

Смысл

Логирование в Core v1 должно быть не текстовым шумом, а структурированным инженерным журналом доменных событий и решений. Каждая запись должна позволять понять: что произошло, к какой доменной сущности это относится, на каком этапе lifecycle это случилось и почему решение было принято, отклонено или изменено.

Что обязательно

• логирование ведётся в структурированной форме, а не как произвольный свободный текст;

• каждая значимая запись содержит как минимум: timestamp, event / decision type, entity type, entity internal ID, stage / lifecycle step, reason или reason_code, если запись относится к решению, отклонению, блокировке, defer или state transition;

• structured logs покрывают как минимум: создание StrategyIntent, результат RiskDecision, создание OrderIntent, pre-execution admit / reject, получение execution / fill fact, обновление Position, обновление PortfolioState на уровне агрегированного перехода, reconciliation start / outcome, recovery-triggered state actions, если они влияют на доменную модель.

Что запрещено

• логировать доменные решения только как свободный текст без структурных полей;

• логировать переход состояния без указания причины, если причина существует в доменной логике;

• делать silent transitions, которые меняют состояние, но не оставляют наблюдаемого следа;

• считать stack trace, raw exception text или debug print полноценной observability-моделью ядра.

Где применяется

• strategy output

• risk decisions

• execution preparation

• fill processing

• position / portfolio transitions

• reconciliation and recovery paths

• Context Gate

Минимальный критерий соблюдения

• каждое доменно значимое решение Core v1 оставляет структурированную запись;

• по журналу можно восстановить не только факт действия, но и его причину;

• отсутствие structured log для ключевого доменного перехода считается нарушением guardrails.

4.5. Правило 2. StrategyIntent metadata

Смысл

StrategyIntent как доменная сущность уже существует в ядре. В рамках данного захода фиксируется не его базовый контракт как таковой, а инженерное правило: у StrategyIntent должны существовать и сохраняться такие metadata, которые делают решение стратегии трассируемым и объяснимым downstream.

Что обязательно

• у StrategyIntent есть минимальный observability / traceability metadata set;

• этот metadata set как минимум позволяет определить: strategy_id, instrument_id, timestamp / source event reference, action / intent kind, origin context reference или equivalent context identity, reason summary, signal class или equivalent explanation handle;

• metadata сохраняются так, чтобы downstream-модули не теряли связь между исходным намерением и дальнейшими доменными объектами;

• при создании StrategyIntent observability-метаданные либо логируются напрямую, либо становятся доступными через последующие lineage-linked записи.

Что запрещено

• создавать StrategyIntent, по которому нельзя понять, какая стратегия и какой контекст его породили;

• терять metadata при переходе от intent к order preparation;

• сводить объяснимость strategy decision только к одному текстовому полю без устойчивой структуры;

• делать strategy output анонимным для downstream-модулей.

Где применяется

• strategy layer

• handoff strategy → risk

• handoff risk → order preparation

• lineage reconstruction

• audit of rejected / admitted strategy decisions

Минимальный критерий соблюдения

• любой StrategyIntent Core v1 имеет достаточный metadata set для downstream traceability;

• по StrategyIntent можно определить хотя бы стратегию, инструмент, момент и контекст происхождения решения;

• потеря intent metadata при передаче по ядру считается нарушением observability rules.

4.6. Правило 3. Context Gate rejection reasons

Смысл

Context Gate не должен молча не пускать торговый цикл дальше. Любой reject, defer или block на входе в decision pipeline должен быть формализован и объясним.

Что обязательно

• для Context Gate существует формализованный набор rejection / defer reason classes;

• как минимум должны быть покрыты причины типа: incomplete context, stale context, warmup not satisfied, session / maintenance restriction, data gap or invalid context continuity, policy-based block, unavailable required context component, look-ahead violation / non-closed-bar usage;

• каждое решение gate фиксируется как admit, reject или defer / hold, если такая семантика предусмотрена;

• для reject/defer обязательно фиксируется reason или reason_code.

Что запрещено

• silent skip без причины;

• смешение нет сигнала и контекст не допущен;

• gate decision без формализованной категории причины;

• локальная стратегия, самостоятельно скрывающая причину отказа контекста вместо использования формального gate outcome.

Где применяется

• TimeframeContext admission

• strategy entry gating

• MTF readiness handling

• warmup enforcement

• data continuity control

Минимальный критерий соблюдения

• любой gate reject/defer имеет формальную причину;

• по наблюдаемым данным можно отличить отсутствие сигнала от недопуска контекста;

• gate decision поддаётся анализу без чтения неструктурированного внутреннего кода стратегии.

4.7. Правило 4. Lineage rules

Смысл

Core v1 должен поддерживать минимальную, но достаточную причинно-следственную связность между ключевыми доменными объектами торгового цикла.

Для Core v1 lineage обязателен на всей цепочке: StrategyIntent (до harmonization pass — operational name decision-layer; в канонической модели — Decision) → RiskDecision → OrderIntent → Fill → Position.

На уровне PortfolioState допустимо агрегирование. Это означает, что связь между конкретным fill и итоговым агрегированным обновлением портфеля может проходить через уже зафиксированное изменение позиции, а не обязана выражаться как прямой one-to-one lineage от каждого fill к PortfolioState.

Что обязательно

• RiskDecision связан с породившим его StrategyIntent или эквивалентной upstream decision identity.

• OrderIntent связан с породившим его RiskDecision.

• Fill связан с тем execution path, который восходит к конкретному OrderIntent;

• Position update связан с тем Fill или набором fills, которые его изменили;

• на уровне Core v1 сохраняется возможность восстановить причинную цепочку: какой StrategyIntent / equivalent Decision породил RiskDecision, какой RiskDecision породил OrderIntent, какой execution path дал Fill и какой Fill изменил Position;

Что запрещено

• создавать OrderIntent, у которого нет восстановимой связи с породившим его upstream decision;

• изменять Position без возможности определить, какой fill это сделал;

• терять lineage при переходе между модулями ядра;

• считать допустимой причинно-следственную цепочку, в которой OrderIntent прослеживается до upstream strategy-side identity (StrategyIntent / equivalent Decision), но не прослеживается через обязательный RiskDecision.

• требовать прямой обязательной one-to-one трассировки каждого fill до PortfolioState, если портфельный уровень обновляется через агрегированный position/accounting step.

Где применяется

• StrategyIntent / equivalent Decision → RiskDecision → OrderIntent handoff

• execution / fill processing

• Position updates

• recovery and reconciliation audit, если проверяется происхождение текущего состояния

• structured logs и state-linked audit records

Минимальный критерий соблюдения

• для любой открытой или изменённой позиции можно восстановить upstream lineage как минимум до StrategyIntent / equivalent Decision identity через обязательный RiskDecision;

• для любого OrderIntent можно определить, каким RiskDecision он был вызван и к какому upstream strategy-side decision identity этот RiskDecision восходит;

• для Core v1 lineage не обрывается внутри основной торговой цепочки StrategyIntent / equivalent Decision → RiskDecision → OrderIntent → Fill → Position;

• на уровне PortfolioState допускается агрегированная связность через Position, а не обязательный прямой lineage от каждого fill.

4.8. Минимальная проверка соблюдения

Каждое observability / traceability rule данного захода должно быть проверяемо хотя бы одним из следующих способов:

• через code review rule;

• через structured log inspection;

• через lineage reconstruction check;

• через trace reconstruction check по structured logs и lineage-linked state records;

• через test scenario, в котором можно восстановить путь решения от intent до position update;

• через gate rejection audit, если проверяется объяснимость недопуска контекста.

Правило считается реально существующим только тогда, когда его соблюдение можно проверить, его нарушение можно обнаружить, а по наблюдаемым артефактам можно восстановить решение без догадки о скрытом внутреннем состоянии.

4.9. Итог захода

Результатом Захода 2 должен стать набор обязательных правил наблюдаемости и трассируемости Core v1, которые:

• делают ключевые доменные решения ядра объяснимыми;

• не позволяют Context Gate и decision pipeline работать как чёрный ящик;

• сохраняют минимальную причинно-следственную связность торговой цепочки;

• задают инженерный минимум observability до перехода к boundary and safety rules следующего захода.

5. Заход 3 — Boundary and safety rules

5.1. Назначение захода

Цель данного захода — зафиксировать минимальные инженерные правила границ и безопасности Core v1, которые защищают ядро от обхода архитектурных швов, расползания источников истины по состоянию и небезопасного поведения при timeout / unknown state сценариях.

Если Заход 1 задаёт фундаментальные инженерные инварианты, а Заход 2 делает решения ядра объяснимыми и трассируемыми, то Заход 3 задаёт минимальную дисциплину: через какие границы ядро имеет право работать; какое состояние считается каноническим; как система обязана вести себя в небезопасных и неопределённых execution-сценариях; какие минимальные storage / locking правила необходимы, чтобы Core v1 оставался согласованным.

Этот заход не превращает документ в production-операционный runbook и не вводит распределённую инфраструктурную сложность. Его задача — зафиксировать минимальный boundary and safety baseline, без которого ядро остаётся архитектурно уязвимым.

5.2. Границы захода

Входит в scope	Не входит в scope
MockExecutionAdapter as boundary test	structured logging и lineage
single source of truth for state	observability / traceability
execution behind interface	business logic стратегии
timeout / unknown state handling	risk policy как торговая логика
minimal storage and locking discipline	dashboards, alerts и monitoring systems
	retention policy
	эксплуатационные playbooks
	distributed coordination
	cluster locking
	HA/storage architecture
	exchange-specific runbooks beyond minimal Core v1 safety rules

5.3. Статус boundary and safety rules

Правила данного раздела рассматриваются как обязательные инженерные правила Core v1.

	модуль не считается корректным, если он обходит boundary rules или нарушает safety semantics;

	локально рабочее поведение не оправдывает нарушение архитектурной границы;

	поведение системы в timeout / unknown state сценариях не может оставаться неявным;

	отсутствие канонического источника истины по состоянию считается инженерным дефектом, а не допустимым компромиссом.

5.4. Правило 1. MockExecutionAdapter as boundary test

Смысл

MockExecutionAdapter нужен не как удобная заглушка ради тестов сама по себе, а как инженерный способ проверить, что execution boundary ядра действительно существует и соблюдается.

Если ядро нельзя стабильно протестировать через mock execution layer, это означает, что execution-логика протекла в модули, которые не должны знать о сыром внешнем исполнении.

Что обязательно

	для Core v1 существует mock execution adapter, реализующий тот же формальный execution contract, что и реальный execution adapter;

	ядро может проходить boundary-oriented tests без обращения к реальной бирже;

	через mock adapter можно воспроизводить как минимум: успешный submit, reject, timeout / missing confirmation, duplicate / repeated execution fact, partial / incremental execution scenario, если он поддерживается текущей сборкой;

	boundary tests подтверждают, что ядро работает с execution через контракт, а не через конкретный адаптер.

Что запрещено

	тестировать execution path только через реальную биржу;

	делать mock adapter неполным образом, если из-за этого не проверяется соблюдение execution boundary;

	встраивать exchange-specific поведение прямо в ядро под видом “так проще протестировать”;

	считать boundary соблюдённым, если mock adapter не может заменить реальный в boundary-oriented test scenario.

Где применяется

	execution contract validation

	boundary-oriented integration tests

	safety scenario tests

	regression checks для execution handoff

Минимальный критерий соблюдения

	Core v1 проходит execution-path проверки через mock execution adapter;

	boundary test подтверждает, что ядро зависит от execution contract, а не от конкретной биржевой реализации;

	сценарии boundary testability воспроизводимы без обращения к реальной площадке.

5.5. Правило 2. Single source of truth for state

Смысл

Для каждого класса состояния Core v1 должен быть заранее определён один канонический источник истины и порядок обновления. Ядро не должно жить в модели, где разные модули одновременно считают себя владельцами одного и того же состояния.

Это правило относится не к внешним execution facts как таковым, а к внутренней state-модели ядра: где канонически живёт состояние ордера; где канонически живёт состояние позиции; где канонически живёт состояние портфеля; кто имеет право обновлять это состояние; в каком порядке это делается.

Правило должно читаться согласованно с atomic state writes из Захода 1: наличие канонического источника истины неотделимо от согласованного порядка фиксации state changes.

Что обязательно

	для каждого ключевого класса состояния Core v1 определён канонический владелец или канонический state layer;

	как минимум это правило распространяется на: order state, position state, portfolio state, processed execution facts / idempotency state, reconciliation outcome state, если он меняет доменную модель;

	для каждого класса состояния определён допустимый путь обновления;

	один и тот же state change не должен одновременно финализироваться в нескольких независимых местах.

Что запрещено

	несколько “истин” для одного класса состояния;

	прямое обновление position state из нескольких модулей в обход согласованного маршрута;

	локальные shadow states, которые начинают вести себя как канонические;

	попытка синхронизировать расходящиеся state-модели постфактум без заранее определённого source-of-truth rule.

Где применяется

	order lifecycle state

	fill-driven position updates

	portfolio accounting

	reconciliation commit

	recovery after restart

Минимальный критерий соблюдения

	для каждого класса состояния можно явно указать канонический source of truth;

	для каждого state update можно указать модуль, который имеет право его зафиксировать;

	после обработки execution facts ядро не требует догадки, какой из нескольких state copies считается правильной.

5.6. Правило 3. Execution behind interface

Смысл

Ядро должно взаимодействовать с execution только через формальный интерфейс / контракт. Ни стратегия, ни риск-слой, ни state management не должны зависеть от сырой API-специфики конкретной биржи.

Это правило про архитектурную границу: ядро знает execution contract, но не знает детали REST / WebSocket сообщений, HTTP semantics, vendor-specific response shapes и иные сырые внешние особенности.

Что обязательно

	существует формальный execution interface / contract, через который ядро работает с execution;

	все execution-related действия ядра проходят через этот контракт;

	реальный adapter и mock adapter реализуют один и тот же boundary;

	нормализация внешних execution responses выполняется до входа в доменные модули ядра.

Что запрещено

	прямой вызов сырого exchange client из strategy, risk, position или portfolio logic;

	утечка vendor-specific response fields в доменную модель без boundary normalization;

	обход execution interface “ради удобства”;

	привязка core-модулей к одной площадке через импорт, типы данных или исключения vendor SDK.

Где применяется

	order placement path

	cancel / query path

	execution status handling

	reconciliation calls to external execution source

	boundary testing

Минимальный критерий соблюдения

	ни один core-модуль не зависит напрямую от сырого exchange API;

	execution adapter можно заменить без переписывания доменной логики;

	все execution interactions ядра проходят через формальный contract boundary.

5.7. Правило 4. Timeout / unknown state handling

Смысл

Когда ядро распознаёт timeout, missing confirmation или unknown state scenario, оно обязано перейти к формально определённому safety-поведению, а не продолжать торговый цикл как будто неопределённости не возникло.

Это правило не вводит заново доменные категории unknown states — они уже формализованы в техроадмапе. Здесь фиксируется обязательная инженерная реакция на уже распознанный небезопасный сценарий.

Правило должно читаться согласованно с уже формализованными unknown states и safety semantics техроадмапа: guardrails не определяют категорию заново, а фиксируют обязательную реакцию на неё.

Что обязательно

	для timeout / unknown state scenarios существует формально определённая handling semantics;

	как минимум должны быть определены обязательные действия для случаев: order submit timeout, missing external confirmation, unknown order state, unknown position state, stale context, reconciliation-required conflict, stale execution certainty after partial processing failure;

	после распознавания такого сценария ядро обязано: блокировать дальнейшие небезопасные торговые действия в затронутом контуре, инициировать reconcile / recovery path, если это предусмотрено, либо перейти в freeze / safe-mode semantics, либо явно зафиксировать, что дальнейшее автоматическое действие запрещено до разрешения неопределённости;

	safety handling не должен зависеть от локальной догадки модуля, что “скорее всего всё нормально”.

Что запрещено

	продолжать normal trading flow после распознавания unknown state;

	маскировать timeout или unknown state под accepted / filled / synchronized;

	делать auto-continue без формальной safety semantics;

	держать ambiguous execution state как временную мелочь, не переводя его в наблюдаемое failure / safety condition.

Где применяется

	execution submit path

	fill / execution confirmation path

	reconciliation triggers

	recovery после communication failures

	state safety enforcement before further trading actions

Минимальный критерий соблюдения

	для каждого timeout / unknown state scenario Core v1 имеет заранее определённую safety reaction;

	после распознавания unknown state система не продолжает торговлю в обычном режиме по умолчанию;

	safety handling проверяем и воспроизводим в тестовом сценарии.

5.8. Правило 5. Minimal storage and locking discipline

Смысл

Core v1 не требует сложной распределённой storage / locking архитектуры, но должен иметь минимальную дисциплину хранения и блокировок, достаточную для предотвращения несогласованных state updates и конфликтующих записей.

Это правило задаёт инженерный минимум, а не промышленную кластерную систему координации.

Правило должно читаться согласованно с atomic state writes из Захода 1 и с single source of truth for state данного захода: storage discipline обязана поддерживать оба ограничения, а не существовать отдельно от них.

Что обязательно

	для критических state transitions определён минимальный storage discipline;

	для операций записи state определена минимальная locking / mutual exclusion semantics, достаточная для предотвращения конфликтующих обновлений в пределах Core v1;

	state persistence и state mutation не должны выполняться параллельно так, чтобы результат зависел от случайного interleaving;

	storage discipline согласован с atomic state writes из Захода 1.

Что запрещено

	несогласованные конкурентные записи в один и тот же state segment;

	параллельные state updates без минимального coordination rule;

	хранение состояния в форме, где порядок записи не поддаётся воспроизводимому контролю;

	подмена минимальной locking discipline надеждой, что “обновления просто не пересекутся”.

Где применяется

	state store writes

	fill-driven state transitions

	reconciliation commit path

	recovery restore / persist path

	idempotency-related processed-fact recording

Минимальный критерий соблюдения

	для критических state writes определено, как предотвращаются конфликтующие обновления;

	запись одного и того же state segment не зависит от неявной гонки между модулями;

	storage / locking discipline достаточна для Core v1, даже если она ещё не является industrial-grade distributed solution.

5.9. Минимальная проверка соблюдения

Каждое boundary and safety rule данного захода должно быть проверяемо хотя бы одним из следующих способов:

	через code review rule;

	через boundary-oriented integration test;

	через mock execution scenario;

	через state ownership check;

	через timeout / unknown state safety scenario;

	через storage / write conflict check;

	через traceable boundary audit, если проверяется, что execution interaction действительно проходит через формальный interface.

Правило считается реально существующим только тогда, когда его соблюдение можно проверить, его нарушение можно обнаружить, а небезопасный сценарий приводит к формально определённой реакции, а не к неявному поведению.

5.10. Итог захода

Результатом Захода 3 должен стать набор обязательных boundary and safety rules Core v1, которые:

	защищают ядро от обхода execution boundary;

	не допускают расползания источников истины по state-модели;

	формализуют обязательную safety-реакцию на timeout / unknown state scenarios;

	задают минимальную storage and locking discipline, достаточную для Core v1;

	замыкают базовый набор инженерных guardrails документа перед переходом к следующим документам комплекта.
