Trading Governance

Документ №6 в комплекте документов торгового ядра

Версия: v0.1 Статус: согласованный полный текст Роль документа: governance-layer торгового ядра как внешний policy-level слой Следующий документ комплекта: Interface contracts / implementation packages / Codex work



Документ	Trading Governance
Версия	v0.1
Статус	Согласованный полный текст
Место в комплекте	Документ №6
Основание	Архитектурный roadmap v1.7; Technical roadmap v0.9; Engineering Guardrails v0.8; Trading Domain Model v0.5; Core Contracts v0.1





1. Назначение документа

1.1. Роль документа

Документ Trading Governance фиксирует governance-layer торгового ядра как самостоятельный policy-level слой комплекта документов. Его задача — определить не то, что именно ядро считает signal, decision, order, fill, position, account state или reconciliation outcome, а то, когда, при каких условиях и в каком режиме системе разрешено начинать торговлю, продолжать торговлю, ограничивать торговлю, блокировать торговлю и возвращаться в normal flow.

1.2. Основание документа

Основание документа в составе комплекта: Архитектурный roadmap торгового ядра — v1.7; Технический roadmap реализации — v0.9; Engineering Guardrails / Core v1 Engineering Rules — v0.8; Trading Domain Model — v0.5; Core Contracts / Canonical Core Model — v0.1. Trading Governance не вводит новую архитектуру поверх уже утверждённой и не пересобирает canonical core model заново. Он появляется только после того, как комплект уже зафиксировал архитектурные границы ядра, техническую последовательность его сборки, обязательные инженерные правила применения, доменную картину исполнения и каноническую contract-level truth model.

1.3. Главный вопрос документа

Архитектурный roadmap уже определил, как ядро должно быть устроено как система. Technical roadmap определил, в каком порядке оно собирается. Engineering Guardrails закрепил обязательные инженерные правила применения. Trading Domain Model раскрыл доменную реальность исполнения, данных, recovery и market structure. Core Contracts собрал это в canonical contract-level model. После этого Trading Governance отвечает на следующий вопрос: в каком policy-state находится система и какие торговые действия для неё допустимы в этом состоянии.

1.4. Центральная граница

Главная роль данного документа состоит в том, чтобы формально отделить core truth от trade permission policy. Canonical core model уже ответила на вопрос, что именно система считает торговой реальностью и в каких контрактах эта реальность живёт. Governance-layer отвечает на другой вопрос: при каком сочетании contextual, execution, accounting, reconciliation и environment-level условий системе разрешено продолжать normal trading, когда она должна перейти в restricted, degraded, blocked, frozen или safe-mode posture, и на каком основании допускается возврат к normal continuation.

1.5. Адресат документа

Документ предназначен для архитектора торгового ядра, разработчика policy-layer, аудитора реализации и для последующих implementation-oriented документов комплекта. Он должен быть достаточно строгим, чтобы не позволить реализации молча смешивать governance с risk verdict, Context Gate, Pre-execution Guard, ReconciliationResult или operator convenience. Одновременно он не должен превращаться ни в runbook, ни в deployment-инструкцию, ни в кодогенерацию, ни в operational checklist.

1.6. Итоговая цель

После утверждения документа у торгового ядра должен существовать не только корректный architectural, technical, engineering, domain и contract layer, но и отдельный governance layer, который формально определяет trade admission, trade restriction, block/freeze semantics, relationship с reconciliation outcomes и правила возврата системы в trading flow без неявной или произвольной интерпретации текущего торгового состояния системы.



2. Место документа в комплекте

2.1. Позиция в составе комплекта

Trading Governance является документом №6 в комплекте документов торгового ядра и следует непосредственно после документа Core Contracts / Canonical Core Model v0.1. Такое положение отражает принципиальную логику сборки: governance не должен появляться раньше, чем ядро уже имеет формально закреплённую contract-level truth model.

2.2. Логика последовательности

Логика комплекта читается так: архитектурный roadmap задаёт общую модель ядра; technical roadmap переводит её в порядок инженерной сборки; Engineering Guardrails фиксирует обязательные правила инженерного применения; Trading Domain Model раскрывает доменную реальность исполнения, данных, recovery и market structure; Core Contracts собирает это в canonical contract-level model; и только затем Trading Governance накладывает на уже сформированное ядро внешний policy-layer допуска, ограничения, блокировки и возврата к normal flow.

2.3. Асимметричная связь с предыдущими документами

Trading Governance опирается на документы 1–5, но не повторяет их. Architectural roadmap уже зафиксировал существование отдельного governance-layer как внешнего документа. Technical roadmap вынес governance и эксплуатационные политики за пределы своего scope. Engineering Guardrails зафиксировал инженерные invariants, observability rules и boundary/safety rules ядра, а не policy of trade permission. Core Contracts исключил governance-уровень торговли из собственного scope и специально указал, что paper/testnet/live admission, drawdown governance, operator discipline, validation policy и release discipline относятся уже к документу №6.

2.4. Критическое ограничение чтения

Trading Governance не является частью canonical trading-truth layer. Он не создаёт Signal, Decision, RiskDecision, OrderIntent, Order, OrderState, ExecutionEvent, Fill, Position, Balance, AccountState, PortfolioState или ReconciliationResult и не переопределяет их смысл. Governance начинает работать только после того, как эти объекты уже могут быть прочитаны в contract-level модели как отдельные доменные реальности.

2.5. Итог места в комплекте

Trading Governance является первым документом, который начинает описывать не внутреннюю структуру торговой истины ядра и не инженерные правила её применения, а policy-level режимы торгового допуска и continuation control. Он замыкает conceptual bridge между canonical core model и последующими interface contracts, implementation packages и implementation work.



3. Границы документа

3.1. Что входит в scope документа

В scope Trading Governance входит фиксация governance-layer как внешнего policy-level слоя по отношению к canonical core model. Документ определяет, какие policy-states существуют над already-defined core reality, какие классы trade admission и trade restriction различаются, какие operating postures считаются допустимыми для normal continuation, какие circumstances переводят систему в degraded, blocked, frozen или safe-mode state и на каком уровне допускается возврат в normal flow.

3.2. Что также входит в scope

В scope документа входит фиксация policy-level relationship между governance и already existing соседними швами ядра: environment modes startup / paper / testnet / live; preconditions до trade admission; admission verdicts allowed / restricted / denied / suspended / reconcile-required; policy-semantics normal, degraded, blocked, frozen, safe-mode и manual-intervention states; escalation triggers после допуска; relationship between reconciliation outcome and governance decision; authority boundaries возврата системы в trading flow.

3.3. Что не входит в scope

В документ не входит повторное определение canonical core objects. Не входят инженерные guardrails и technical mechanics: UTC-aware datetime, Decimal, atomic state writes, idempotent fill processing, structured logging, storage discipline, mock adapters, transport retries и другие engineering rules. Не входят adapter-level и API-level specifics. Не входят strategy logic, UI, dashboard, alerting workflow, human-facing monitoring, эксплуатационные playbooks и иные внешние operational artifacts.

3.4. Критическая граница документа

Критическая граница Trading Governance состоит в следующем: здесь фиксируется policy-layer допуска и continuation control, а не contract-level truth model ядра и не engineering mechanics её применения. Допустимы только такие утверждения, которые отвечают на вопросы: при каких условиях системе разрешено торговать; какие policy-статусы допуска и ограничения различаются; какие postures блокируют новые торговые действия; какие circumstances требуют degraded / blocked / frozen / safe-mode continuation; как reconciliation outcomes влияют на governance decision; и на каком основании допускается resume.



4. Роль governance-layer относительно ядра и соседних слоёв

4.1. Внешний policy-layer

Trading Governance должен читаться как внешний policy-level слой по отношению к already-defined canonical core model. Governance-layer не создаёт и не переопределяет core truth. Он накладывает policy-level interpretation на уже признанные состояния и outcomes ядра.

4.2. Governance не равен RiskDecision

RiskDecision выражает verdict risk layer относительно конкретного upstream Decision. Governance решает вопрос другого класса: разрешено ли системе в текущем environment, при текущем operating posture и при текущем составе unresolved conditions вообще продолжать торговый flow как policy matter.

4.3. Governance не равен Context Gate

Context Gate является core-level admission mechanism для контекста, тогда как governance является external policy-layer для торговой системы в целом. Gate решает вопрос, допустим ли контекст для входа в decision pipeline. Governance решает вопрос, разрешено ли системе как policy matter использовать текущую core reality для продолжения торговых действий.

4.4. Governance не равен Pre-execution Guard

Pre-execution Guard проверяет исполнимость конкретного OrderIntent в текущих instrument/venue constraints. Governance решает вопрос шире: разрешена ли торговля как policy-state системы и какой тип действий вообще допустим в этом состоянии. Guard отвечает за admissibility конкретного execution attempt. Governance отвечает за admissibility текущего торгового posture системы и за policy-level distinction между new actions, restricted continuation и protective-only flow.

4.5. Governance не равен ReconciliationResult

ReconciliationResult выражает formal outcome сверки между локальной и внешней картиной, но не является governance-decision object и сам по себе не отвечает на вопрос, разрешено ли системе торговать как policy matter. Governance читает уже признанный reconcile outcome как одно из оснований для policy-level решения о restriction, block, safe-mode или resume.

4.6. Governance-layer как policy overlay над ядром

Canonical core model описывает, что существует в торговой реальности ядра; соседние core-level gates и verdicts описывают, что допустимо на отдельных швах decision, context и execution pipeline; а Trading Governance описывает, в каком policy-state система находится как торговый контур в целом и какие классы действий разрешены ей при этом состоянии.

4.6.1. Policy-reading sequence относительно соседних швов

Governance-layer должен читаться как policy-level overlay над уже существующими core-level швами, а не как их замена. Минимальная последовательность чтения такова: governance определяет admissibility текущего contour и policy-level допустимость новых действий; далее Context Gate решает допустимость contextual basis для входа в decision pipeline; далее strategy/risk layer формирует Decision и RiskDecision; далее Pre-execution Guard проверяет admissibility конкретного execution attempt; далее execution / fill / position / account / portfolio layers формируют core reality; reconcile outcome затем даёт governance новый policy-level input для возможного ограничения, пересмотра posture или отдельного return-to-flow decision. Эта последовательность не означает, что все слои решают один и тот же вопрос; она означает, что governance читает систему как policy-layer поверх already-defined core truth и соседних admission/verdict boundaries.

4.7. Итог раздела

Trading Governance является внешним policy-layer по отношению к canonical core model и не должен смешиваться с соседними core-level швами. Его собственная роль — определить policy-state торговой системы как целого и зафиксировать, какие торговые действия разрешены, ограничены, заблокированы или требуют explicit return-to-flow decision.



5. Базовые принципы Trading Governance

5.1. Вводный принцип

Опираясь на уже зафиксированную роль governance-layer, принципы данного раздела определяют, как policy-layer должен читать already-recognized core states и outcomes, не подменяя собой canonical model и не расползаясь в operational runbook.

5.2. Governance не создаёт торговую истину

Governance не должен создавать свои собственные суррогаты signal, order, fill, position или reconciliation truth. Он работает на уровне policy-level consequences: допускает ли текущее состояние normal trading, требует ли restriction, блокирует ли новые действия, переводит ли affected contour в freeze/safe-mode и допускает ли explicit return-to-flow.

5.3. Policy-level restriction сильнее локального удобства

Если governance-layer распознаёт состояние, несовместимое с безопасным продолжением trading flow, локальное удобство, желание «не пропустить вход» или частная уверенность отдельного модуля не могут иметь приоритет. Governance обязан считать restriction приоритетной над любым локальным предположением о нормальности состояния.

5.4. Никакого silent continuation under ambiguity

Ambiguity не может быть интерпретирована как молчаливое разрешение продолжать торговлю. Если система находится в unresolved unknown, conflict or reconcile-required posture, governance обязан дать явный ограничивающий verdict, а не позволять неявное continuation by omission.

5.5. Возврат в normal flow не бывает автоматическим по умолчанию

Return-to-flow требует явного policy-basis. Этот basis может быть разным в разных классах состояний и environments, но он не должен silently подразумеваться из одного только факта, что сверка завершилась или что локальная картина стала выглядеть лучше.

5.6. Governance decisions должны быть классифицируемыми

Policy-level decisions обязаны существовать как различимые классы, а не как размытые состояния. Документ строится вокруг trade admission classes, operating postures, escalation triggers и resume authority, чтобы policy-решение можно было проверить, объяснить и аудировать.

5.7. Governance обязан быть environment-aware

Условия допустимости торговли не одинаковы для startup, paper, testnet и live. Чем ближе environment к реальному торговому риску, тем строже должны читаться governance-level admissibility and continuation rules.

5.8. Governance различает допуск новых действий и protective continuation

Governance-layer не должен сводить весь policy-state к бинарному «торговать / не торговать». Он обязан различать новые entry-like действия и protective continuation как разные governance-semantics.

5.9. Итог раздела

Trading Governance строится как внешний policy-layer поверх already fixed canonical core model; restriction имеет приоритет над локальным удобством; ambiguity не допускает silent continuation; return-to-flow требует явного основания; governance decisions должны быть формализуемыми; execution environment влияет на строгость допуска; а новые действия и protective continuation должны различаться как разные policy-классы.



6. Оси governance-модели

6.1. Многомерная модель

Trading Governance не должен строиться как одна бинарная шкала вида «торговать / не торговать». Governance должен читать состояние системы по нескольким независимым policy-измерениям.

6.2. Первая ось: environment mode

Первая ось governance-модели — environment mode. Она отвечает на вопрос, в каком execution environment находится система как policy-subject: startup, paper, testnet или live. Эта ось фиксирует policy-класс среды, внутри которого дальше читаются остальные governance-оси.

6.3. Вторая ось: trade admission status

Вторая ось governance-модели — trade admission status. Она отвечает на вопрос, какой policy-verdict имеет система или affected contour относительно допуска новых торговых действий. На минимальном уровне различаются classes allowed, restricted, denied, suspended и reconcile-required. Allowed означает отсутствие policy-level препятствия для допуска новых торговых действий. Далее уже проверяется, что необходимые preconditions действительно выполнены.

6.4. Третья ось: operating posture

Третья ось governance-модели — operating posture. Она отвечает на вопрос, в каком общем policy-состоянии находится trading contour в целом: normal, degraded, blocked, frozen, safe-mode, manual-intervention.

6.5. Четвёртая ось: resume authority

Четвёртая ось governance-модели — resume authority. Она отвечает на вопрос, на каком основании и на каком уровне системе разрешено возвращаться из restricted / suspended / blocked / frozen / safe-mode posture к дальнейшему trading flow. На минимальном policy-level различаются reconcile-confirmed, operator-required и узкий auto-allowed class.

6.6. Совместное чтение осей

Эти четыре оси не должны сворачиваться друг в друга. Environment mode не подменяет admission status. Admission status не подменяет operating posture. Operating posture не включает в себя resume authority. Одновременно они читаются совместно как governance-state tuple.

6.7. Оси не являются новыми доменными объектами

Четыре оси governance-модели не являются новыми canonical objects trading-truth layer. Это не новые доменные сущности исполнения или учёта, а policy-level dimensions, через которые governance читает уже признанное состояние системы.

6.8. Итог раздела

Governance-модель минимально включает environment mode, trade admission status, operating posture и resume authority. Эти оси не должны смешиваться друг с другом и не должны подменять canonical core contracts; они нужны затем, чтобы policy-state системы был формально читаем, проверяем и пригоден для дальнейших разделов документа №6.



7. Governance semantics для startup / paper / testnet / live

7.1. Environment mode как policy-axis

Trading Governance обязан различать startup, paper, testnet и live как разные policy-режимы, а не как технические ярлыки одного и того же торгового процесса.

7.2. Startup semantics

Startup означает не просто факт запуска процесса, а особый policy-режим входа системы в trading flow. Система не должна считаться policy-level ready for trading только на основании того, что процесс поднят, модули инициализированы и market data снова поступают. Startup readiness существует лишь тогда, когда завершён phase of initial state recovery в том объёме, который требуется для текущего supported contour, и когда начальная reconcile-based картина не оставляет unresolved policy-level ambiguity для запуска торговых действий. Startup завершает не инициализацию процесса, а policy-переход из «система поднялась» в «система допущена к торговому flow».

7.3. Paper semantics

Paper является средой наименьшей policy-цены ошибки среди execution environments, но не равен отсутствию governance. Paper допускает наиболее широкий класс admission for strategy/version/config validation, exploratory proving of end-to-end contour и проверку воспроизводимости policy-decisions при минимальной внешней цене ошибки. Но paper не должен превращаться в среду, где policy-level defects считаются допустимыми только потому, что нет реального капитального воздействия.

7.4. Testnet semantics

Testnet должен читаться как промежуточный policy-режим между paper и live. Он уже не является purely simulated validation contour, но ещё не тождественен live по цене ошибки. Testnet нужен как среда policy-проверки того, что system behavior сохраняет свою смысловую дисциплину при более реалистичном execution contour.

7.5. Live semantics

Live является средой максимальной policy-строгости. Здесь unresolved ambiguity, unclear resume basis, version/config uncertainty и continuation under conflict получают максимальную policy-цену ошибки. Live не должен читаться как «тот же самый contour, что testnet, только с реальными ордерами». На уровне governance это качественно другой режим.

7.6. Environment modes не взаимозаменяемы

Paper, testnet и live не должны рассматриваться как механические копии друг друга с разными адаптерами исполнения. Один и тот же core-level contour может быть policy-admissible в paper, restricted in testnet и denied in live.

7.7. Переход между environments не является автоматическим

Переход paper → testnet → live должен читаться не как техническая эскалация запуска, а как отдельный policy-decision, основанный на admissibility текущей версии стратегии, конфигурации и operating contour для более строгой среды.

7.8. Итог раздела

Startup, paper, testnet и live являются разными governance modes и должны читаться как разные policy-классы среды. Эти environments не взаимозаменяемы, а переход между ними не должен считаться автоматическим следствием локальной успешности в предыдущем режиме.



8. Preconditions до trade admission

8.1. Preconditions как обязательный policy-layer

Trade admission не возникает автоматически из одного лишь факта наличия сигнала, сформированного Decision, approved RiskDecision или готового к исполнению OrderIntent. Preconditions до trade admission являются самостоятельным policy-layer и должны быть выполнены до появления allowed-admission verdict.

8.2. Кумулятивный набор

Preconditions образуют кумулятивный policy-basis для допуска новых торговых действий. Если хотя бы одна из обязательных предпосылок отсутствует, admission не должен silently считаться состоявшимся.

8.3. Первая обязательная предпосылка: startup-ready state для текущего contour

До trade admission система должна находиться в таком startup-ready state, который policy-level считается достаточным для входа в trading flow текущего supported contour. Сам факт запуска процесса, инициализации модулей и поступления market data не является достаточной precondition для trade admission.

8.4. Вторая обязательная предпосылка: environment-level admissibility

Trade admission должен быть допустим не вообще, а в конкретном execution environment. Текущая strategy/version/configuration pair и текущий operating contour должны быть policy-level допустимы именно для данного execution environment, а не только для какого-то более мягкого режима.

8.5. Третья обязательная предпосылка: admissible contextual state

Новые торговые действия не должны допускаться без policy-level признания того, что contextual state является допустимым для decision pipeline. Для MTF-contours это означает не локальную strategy-view контекста, а admissibility того contextual basis, который уже признан ядром как допустимый upstream contractual input. Отсутствие admissible contextual basis блокирует trade admission.

8.6. Четвёртая обязательная предпосылка: отсутствие unresolved restrictive condition в affected contour

Trade admission невозможен, если в affected contour сохраняется unresolved condition такого класса, который уже требует restriction, suspension, freeze или reconcile-required posture. До admission новых торговых действий такой condition должен пройти свой явный resolve path.

8.7. Пятая обязательная предпосылка: достаточно признанное position/account/portfolio state

Новый trade admission не должен происходить поверх unresolved position/account/portfolio picture, если эта picture ещё не обладает достаточной степенью признанности для нового policy-level риска. Под «достаточной признанностью» governance-layer здесь понимает не собственную локальную догадку, а уже признанный core-level basis соответствующего truth layer: для affected contour позиционная, account-level и portfolio-level picture должны быть policy-readable как по меньшей мере достаточно определённые для нового admission, а не как unresolved, conflict-bearing или insufficient-for-resume states.

8.8. Шестая обязательная предпосылка: текущая стратегия и профиль остаются допустимыми для данного режима и posture

До trade admission governance-layer должен считать текущую стратегию, её версию и действующий конфигурационный профиль policy-level допустимыми для данного environment и данного operating posture.

8.9. Preconditions данного раздела относятся к new trade admission

Preconditions, описанные выше, относятся прежде всего к допуску новых торговых действий. Они не должны автоматически переноситься один в один на все случаи protective continuation, reduce-only logic или close-management affected contour.

8.10. Итог раздела

Trade admission в Trading Governance возможен только при наличии кумулятивного policy-basis: startup-ready state, environment-level admissibility, admissible contextual state, отсутствие unresolved restrictive condition, достаточно признанное position/account/portfolio state и сохранённая admissibility текущей strategy/profile pair.



9. Admission verdict classes

9.1. Формальный результат допуска

Trading Governance должен фиксировать результат допуска новых торговых действий как формальный admission verdict. Минимальный обязательный набор verdict classes включает: allowed, restricted, denied, suspended, reconcile-required.

9.2. Allowed

Allowed означает, что governance-layer не видит policy-level препятствия для допуска новых торговых действий в текущем contour. Allowed не означает гарантию исполнения и не отменяет значение дальнейших core-level gates. Это policy-level разрешение на запуск нового действия, а не обещание, что вся последующая цепочка уже завершена успешно.

9.3. Restricted

Restricted означает, что governance-layer не запрещает новые торговые действия полностью, но допускает их только в policy-level суженном виде. Restriction может относиться к классу допустимых действий, к affected contour, к environment-level условиям или к текущему operating posture.

9.4. Denied

Denied означает, что governance-layer не допускает новые торговые действия как policy-class в текущем contour. Новый trade admission при verdict denied не допускается.

9.5. Suspended

Suspended означает, что новые торговые действия временно не допускаются до появления дополнительного policy-basis, но этот basis не сводится автоматически ни к общему запрету, ни к уже завершённому reconcile outcome.

9.6. Reconcile-required

Reconcile-required означает, что trade admission blocked именно потому, что дальнейшее policy-level движение требует явного reconcile / resolve path. Это специальный verdict class, который нельзя растворять ни в denied, ни в suspended.

9.7. Verdict classes не тождественны operating posture

Admission verdict classes не должны смешиваться с operating posture системы в целом. Admission verdict отвечает на вопрос, допускаются ли новые торговые действия. Ongoing trading posture отвечает на вопрос, в каком policy-state находится уже идущий trading contour в целом.

9.8. Verdict classes должны быть явными

Admission verdict не должен оставаться неявным. Состояние «мы, кажется, пока не должны торговать, но formal verdict не назван» для документа №6 считается недостаточным.

9.9. Итог раздела

Trading Governance обязан различать как минимум пять admission verdict classes — allowed, restricted, denied, suspended, reconcile-required. Эти verdicts относятся только к допуску новых торговых действий, не подменяют operating posture системы и не заменяют соседние core-level verdicts и outcomes.



10. Governance of ongoing trading

10.1. Самостоятельный policy-layer

После initial admission Trading Governance должен решать уже другой вопрос: не разрешено ли системе войти в торговый цикл, а в каком policy-state находится уже идущая торговля и допустимо ли её дальнейшее normal continuation.

10.2. Текущая торговля не продлевает исходный allowed verdict бесконечно

Allowed-admission verdict сам по себе не даёт системе бессрочного права продолжать торговлю. Ongoing trading должен постоянно читаться governance-layer заново по мере изменения core-level state, а не считаться автоматически нормальным только потому, что admission когда-то уже был allowed.

10.3. Состояние normal trading

Normal trading означает, что текущий trading contour не несёт active policy-level condition, требующей ограничения обычного flow.

10.4. Состояние degraded trading

Degraded trading означает, что trading contour ещё остаётся рабочим, но уже не должен читаться как обычный normal flow. Continuation ещё возможно, но только при policy-level ограничении, усиленном контроле или суженном классе допустимых действий.

10.5. Состояние blocked

Blocked trading означает, что normal continuation более не допускается как policy-class. В blocked posture governance не просто ограничивает текущий contour, а признаёт, что дальнейшее развитие trading flow должно быть остановлено до появления отдельного basis for re-evaluation.

10.6. Состояние frozen

Frozen trading выражает posture удержания текущего affected contour без права на обычное дальнейшее развитие до явного resolve basis. Frozen сильнее blocked: система policy-level зафиксирована и не должна предпринимать автоматических шагов, ведущих к continuation, пока ambiguity или conflict не получат явного разрешения.

10.7. Состояние safe-mode

Safe-mode означает, что trading contour переведён в специальный ограниченный безопасный режим. Система не находится в normal flow и не продолжает обычную торговлю, а удерживается в policy-level контуре, где приоритетом становится сохранение безопасности над продолжением торговой активности.

10.8. Состояние manual-intervention

Manual-intervention означает, что governance-layer более не должен допускать автоматическое возвращение trading contour в обычное движение без отдельного authority boundary вне самого текущего runtime-flow.

10.9. Ongoing trading posture не равен admission verdict и не заменяет reconcile outcome

Operating posture ongoing trading не должен смешиваться ни с admission verdict classes, ни с ReconciliationResult. Эти слои модели остаются раздельными.

10.10. Раздел фиксирует policy-reading, а не triggers

Настоящий раздел сознательно не перечисляет конкретные escalation triggers и не раскрывает mechanics перехода между posture states. Его задача — зафиксировать, как governance-layer читает ongoing trading на policy-уровне после того, как core-level conditions уже распознаны.

10.11. Итог раздела

Governance of ongoing trading является самостоятельным policy-layer вопросом. Уже идущая торговля должна читаться governance-layer через различимые operating postures: normal, degraded, blocked, frozen, safe-mode, manual-intervention.



11. New actions vs protective actions

11.1. Два разных policy-класса

Trading Governance обязан жёстко различать new actions и protective actions. Governance-layer не должен читать все торговые действия как один и тот же policy-class.

11.2. New actions

New actions — это такие торговые действия, которые создают новую directional exposure, увеличивают уже существующую exposure, запускают новый entry-like торговый эпизод или иным образом расширяют риск-профиль системы. Для них нужен полноценный policy-basis.

11.3. Protective actions

Protective actions — это такие действия, которые не создают новую риск-экспозицию, а направлены на ограничение, сокращение, закрытие, удержание под контролем или разрешение уже существующего affected contour.

11.4. Запрет new actions не означает автоматический запрет protective actions

Если governance запрещает new actions, это не должно автоматически интерпретироваться как запрет protective continuation. Contour может быть уже недостаточно надёжен для открытия нового риска, но ещё требовать допустимого protective behavior по уже существующей позиции или конфликтному состоянию.

11.5. Допустимость protective actions не означает возврат к normal trading

Если governance-layer допускает protective continuation, это не означает, что contour уже вернулся к normal trading posture или что restriction on new actions автоматически снята.

11.6. Protective actions допустимы только пока они не создают новый риск-контур

Protective action допустим только пока он policy-level остаётся именно protective. Если действие под видом protection фактически открывает новую exposure, расширяет позицию, переворачивает её в новый risk episode или создаёт новый trade contour, оно больше не может читаться как protective continuation и должно вернуться в класс new actions.

11.7. Inability-to-execute protective action усиливает restriction

Если governance-layer допускает protective continuation, но protective action не может быть исполнен как ожидалось, система не должна делать вывод, что можно вернуться к обычной торговле. Failure of protection означает escalation, а не нейтральный исход.

11.8. Разведение относится к policy-reading

Настоящий раздел не определяет конкретную execution-mechanics и не перечисляет маршруты модулей. Он определяет только policy-reading двух разных классов действий.

11.9. Итог раздела

Trading Governance обязан различать new actions и protective actions как два разных policy-класса. Запрет новых действий не означает автоматический запрет protective continuation. Допустимость protective continuation не означает возврат к normal trading. Если protective action не может быть исполнен, restriction должна усиливаться, а не ослабляться.



12. Escalation triggers and posture transitions

12.1. Назначение раздела

Настоящий раздел фиксирует, какие classes of conditions должны рассматриваться Trading Governance как основания для escalation и в какие operating postures система должна переводиться после их распознавания.

12.2. Policy-significant condition

Escalation trigger следует понимать не как любой runtime-event, а как такое распознанное condition, которое меняет policy-reading текущего trading contour.

12.3. Базовые классы escalation triggers

Минимально Trading Governance должен различать contextual degradation triggers, execution ambiguity triggers, position/accounting conflict triggers, reconciliation-dependent triggers, protective failure triggers и environment or authority triggers. Во всех случаях речь идёт о policy-significant conditions, а не о перечне инженерных событий.

12.4. Escalation не является бинарной

Trading Governance не должен реагировать на triggers по схеме «либо всё нормально, либо всё остановлено». Posture transition должен быть ступенчатым: один trigger может вести не к полному shutdown, а к более узкому сужению admissible behavior текущего contour.

12.5. Переход в degraded posture

Degraded должен использоваться тогда, когда governance уже не может читать contour как полностью normal, но ещё сохраняется policy-space для ограниченного continuation under control.

12.6. Переход в blocked posture

Blocked должен использоваться тогда, когда governance признаёт: normal flow невозможен, и новые торговые действия не могут продолжаться до появления отдельного policy-basis для пересмотра состояния. Акцент blocked posture — на запрете движения вперёд.

12.7. Переход в frozen posture

Frozen должен использоваться в более жёстком классе случаев, когда governance не просто запрещает дальнейшее normal движение, а фиксирует contour в состоянии без автоматического самодвижения до explicit resolve. Акцент frozen posture — на удержании без самодвижения.

12.8. Переход в safe-mode posture

Safe-mode должен использоваться там, где contour не должен оставаться ни в normal continuation, ни просто в пассивной фиксации, а должен быть переведён в заранее ограниченный безопасный режим.

12.9. Переход в manual-intervention posture

Manual-intervention должен использоваться тогда, когда escalation trigger переводит contour в класс состояний, из которых дальнейшее движение больше не должно происходить автоматически внутри текущего runtime-цикла.

12.10. Reconciliation-related transitions

Reconciliation-related triggers должны вести не к cosmetic state update, а к явному posture transition — как минимум в blocked, frozen, safe-mode или manual-intervention, в зависимости от тяжести и разрешимости текущего contour.

12.11. Protective-failure transitions

Если contour уже был ограничен и system behavior policy-level допускал только protective continuation, неуспех такого continuation не может оставлять posture прежним или смягчать его. Он должен вести к более жёсткому posture transition.

12.12. Posture transition должен быть явным

Если escalation trigger распознан как policy-significant, переход из одного posture в другой должен быть явным и читаемым.

12.13. Итог раздела

Trading Governance обязан распознавать escalation triggers как policy-significant conditions и переводить affected contour в явные posture transitions. Blocked означает запрет дальнейшего normal движения до basis for re-evaluation. Frozen означает более жёсткую фиксацию contour без автоматического самодвижения до explicit resolve. Safe-mode означает controlled safety contour. Manual-intervention означает вынос authority for further movement за пределы automatic continuation.



13. Relationship between reconciliation outcome and governance decision

13.1. Связаны, но не тождественны

Reconciliation outcome является входом для governance-layer, но не подменяет собой governance decision.

13.2. Domain meaning и policy meaning

Reconciliation outcome отвечает на вопрос, что именно стало известно ядру о соотношении локальной и внешней картины. Governance decision отвечает на вопрос, что policy-layer должен сделать с этим знанием в отношении дальнейшей торговли.

13.3. Чтение по affected contour

Governance-layer не должен читать reconcile outcome как бинарный сигнал «всё хорошо / всё плохо» для всей системы сразу. Он обязан читать outcome по affected contour.

13.4. Confirmed alignment не равен automatic resume

Если reconcile outcome указывает на confirmed alignment, governance-layer получает основание для пересмотра текущего posture, но не обязан и не имеет права молча превращать такой outcome в automatic resume.

13.5. Corrected outcome не снимает ограничение автоматически

Corrected outcome должен читаться осторожнее confirmed alignment. Он может стать основанием для дальнейшего ограничения, пересмотра admission status, сохранения degraded / blocked posture или для перехода к отдельному resolve path.

13.6. Conflict-bearing outcome обязан сохранять или усиливать restriction

Если reconcile outcome указывает на конфликт, неразрешённость или equivalent ambiguity-bearing result, governance-layer обязан читать это как основание для сохранения либо усиления restriction.

13.7. Outcome, недостаточный для resume

Core Contracts признаёт отдельный class reconcile outcome, который является недостаточным основанием для resume, и запрещает молча восстанавливать continuation без explicit outcome meaning. Для policy-layer это означает, что завершённая сверка не равна завершённой проблеме.

13.8. Outcome может менять разные оси governance-модели

Reconcile outcome может менять admission status, operating posture и resume authority, но не одинаково. Один и тот же outcome может подтверждать truth-picture, но не снимать requirement for manual authority; может исправлять local picture, но не возвращать admission for new actions; может снимать freeze, но оставлять degraded posture.

13.9. Environment-зависимость governance effect

Один и тот же reconcile outcome не обязан иметь одинаковый governance effect во всех environments. Подтверждённая alignment picture в paper может быть достаточным basis для более мягкого continuation reading, а в live — лишь для пересмотра restriction.

13.10. Relationship with startup reconciliation

Startup reconcile outcome должен читаться не как формальность запуска, а как один из ключевых inputs для решения, достигла ли система startup-ready state, пригодного для дальнейшего trade admission.

13.11. Governance decision должен быть явным после reconcile outcome

После признания reconcile outcome governance-layer обязан сформировать отдельный decision-reading affected contour: сохраняется ли restriction, усиливается ли posture, возможен ли пересмотр admission, требуется ли manual authority, допустим ли return-to-flow.

13.12. Итог раздела

Reconciliation outcome и governance decision связаны напрямую, но не тождественны. ReconciliationResult даёт domain meaning affected contour. Governance decision даёт policy meaning этого outcome. Confirmed alignment не равен automatic resume. Corrected outcome не снимает ограничение автоматически. Conflict-bearing и insufficient-to-resume outcomes обязаны сохранять или усиливать restriction до отдельного resolve basis.



14. Return-to-flow / resume semantics

14.1. Самостоятельный policy-question

Return-to-flow является самостоятельным policy-вопросом и не сводится к исчезновению проблемы. Он означает, что governance-layer признал достаточным policy-basis для перехода affected contour из ограничивающего posture в более свободный режим дальнейшего торгового движения.

14.2. Resume не является автоматическим следствием reconcile completion

Завершённая сверка сама по себе не образует sufficient resume semantics. Между “сверка завершена” и “системе разрешено продолжать торговлю” всегда должен существовать отдельный governance-step.

14.3. Return-to-flow читается по affected contour

Resume semantics должен читаться по affected contour, а не как глобальная кнопка “возобновить всё”. Возврат одного contour к более свободному режиму не означает, что весь trading system целиком получил resume basis.

14.4. Resume semantics различается для новых действий и для protective continuation

Return-to-flow не должен трактоваться только как возврат к admission of new actions. В некоторых случаях governance-layer может признать достаточным основание лишь для более узкого protective continuation, не восстанавливая normal admissibility новых торговых действий.

14.5. Resume не всегда означает возврат именно в normal posture

Возможны более узкие формы resume: возврат в degraded posture, возврат только к restricted admission, возврат только к protective continuation или возврат лишь к состоянию, где contour снова может быть переоценён без немедленного запуска торговой активности.

14.6. Возврат из blocked posture

Blocked posture может быть снят тогда, когда governance получил достаточный basis for re-evaluation и больше не считает normal flow policy-level запрещённым по самому факту текущего posture. Blocked contour в принципе может быть переведён в degraded, restricted или даже normal continuation, если policy-basis для re-evaluation уже признан достаточным.

14.7. Возврат из frozen posture

Frozen posture не может быть снят одним лишь желанием пересмотреть состояние или даже soft basis for re-evaluation. До любого meaningful override должен существовать предварительный explicit resolve того ambiguity/conflict class, который и привёл contour в frozen state.

14.8. Возврат из safe-mode posture

Resume from safe-mode требует не только исчезновения причины входа, но и признания governance-layer, что controlled safety contour больше не нужен.

14.9. Возврат из manual-intervention posture

Resume from manual-intervention не должен подменяться ни automatic reconcile completion, ни локальной операторской уверенностью. Пока contour находится в manual-intervention posture, resume semantics по определению требует внешнего authority step.

14.10. Resume basis должен быть явным

Если contour переводится к более свободному flow, должен существовать ясно читаемый policy-basis такого перехода — reconcile-confirmed basis, explicit resolve basis, operator-authorized basis или другой формально распознаваемый класс основания. Возобновление торговли без явного основания разрушает всю governance-layer логику.

14.11. Return-to-flow остаётся environment-sensitive

Раздел 7 уже зафиксировал, что paper, testnet и live неэквивалентны как policy-environments. Это напрямую относится и к resume semantics. Одно и то же прояснённое состояние может быть достаточным для более мягкого resume-reading в paper, но недостаточным для автоматического возврата к normal flow в live.

14.12. Итог раздела

Return-to-flow / resume semantics является самостоятельным policy-layer вопросом и не сводится ни к reconcile completion, ни к исчезновению внешних симптомов проблемы. Blocked posture может быть снят при наличии достаточного basis for re-evaluation. Frozen posture требует предварительного explicit resolve до любого meaningful override. Safe-mode требует отдельного признания, что controlled safety contour больше не нужен. Manual-intervention требует внешнего authority step. Во всех случаях resume basis должен быть явным и environment-sensitive.



15. Manual intervention and authority boundaries

15.1. Manual intervention как policy-категория

Manual intervention не является внешним шумом вокруг ядра. Это самостоятельная policy-категория governance-layer для состояний, которые не могут быть честно разрешены только внутренним automatic continuation.

15.2. Смысл authority boundary

Authority boundary отделяет automatic governance от внешнего разрешения на дальнейшее движение. Он отвечает на вопрос, на каком уровне система ещё может изменять свой policy-state сама, а на каком уровне дальнейшее движение trading contour уже требует внешнего разрешения.

15.3. Manual intervention нужен не для всякого ограничения

Manual intervention требуется не для каждого restricted или blocked contour, а для тех случаев, где governance-layer больше не может признать internal automatic basis достаточным для дальнейшего изменения posture или для return-to-flow.

15.4. Это не runbook

Document №6 не превращает authority boundary в operational instruction. Здесь не описывается, кто именно нажимает какую кнопку, какой интерфейс используется и как организован human workflow. Фиксируется только policy-смысл: дальнейшее движение contour требует внешнего authority step.

15.5. Operator-required сильнее reconcile-confirmed

Reconcile-confirmed означает, что governance допускает дальнейшее смягчение posture после такого reconcile outcome, который policy-level признан достаточным основанием. Operator-required означает более жёсткий случай: даже при наличии clarified domain picture или завершённой сверки contour не должен продолжать движение без внешнего разрешения.

15.6. Authority boundary по-разному читается для blocked и frozen

Blocked posture означает, что normal flow запрещён до появления достаточного basis for re-evaluation. Поэтому blocked contour в принципе может быть пересмотрен на основании достаточного policy-basis и, в части случаев, при внешнем override. Frozen posture жёстче: он фиксирует contour без автоматического самодвижения до explicit resolve. Значит, для frozen одного внешнего желания «возобновить торговлю» недостаточно; сначала должен быть снят тот conflict or ambiguity class, который привёл contour в frozen state. Только после этого вообще может возникнуть вопрос о внешнем authority step. Такое различие уже зафиксировано в предыдущих разделах документа №6.

15.7. Authority boundary может относиться к разным объектам решения

Authority boundary не обязан всегда относиться ко всей системе целиком. Он должен читаться по affected contour: отдельно для return-to-flow for new actions, снятия blocked posture для instrument or strategy contour, признания, что safe-mode больше не нужен, и иных policy-решений.

15.8. Environment mode влияет на строгость authority boundary

Один и тот же clarified contour может не требовать operator-required boundary в более мягком режиме и требовать её в live. External authority requirement должен читаться как environment-sensitive.

15.9. Manual intervention не отменяет границы между new actions и protective continuation

Даже если contour попал в manual-intervention posture, governance всё равно не должен терять distinction between new actions and protective continuation. External authority boundary не стирает внутреннюю policy-структуру документа №6.

15.10. Решение за authority boundary должно быть явным

Если contour требует manual intervention, последующее решение должно быть policy-readable, а не растворённым в неявном «ну вроде уже можно».

15.11. Итог раздела

Manual intervention and authority boundaries образуют самостоятельный слой Trading Governance. Он нужен для тех состояний, где internal automatic basis больше недостаточен для дальнейшего движения contour. Operator-required является более сильным требованием, чем reconcile-confirmed. Blocked posture может допускать пересмотр при достаточном basis и, в части случаев, при внешнем override. Frozen posture требует предварительного resolve до любого meaningful override. Authority boundary читается по affected contour, зависит от environment mode, не превращает раздел в runbook и не стирает distinction between new actions and protective continuation.



16. Strategy admission / version policy boundaries

16.1. Только policy-boundaries допуска

Настоящий раздел фиксирует policy-boundaries допуска, а не механику выката. Здесь определяются только policy-условия admissibility стратегии, версии и конфигурации, без deployment mechanics, rollout steps и operational runbook.

16.2. Внешний policy-verdict

Strategy admission является внешним policy-verdict по отношению к ядру, а не продолжением strategy logic или risk layer.

16.3. Strategy / version / profile tuple

Policy-reading должен относиться как минимум к strategy / version / configuration profile tuple, а не к одному только strategy name. Одна и та же стратегия как family может быть policy-admissible в одном version/profile сочетании и policy-inadmissible в другом.

16.4. Admission зависит от environment mode

Одна и та же strategy / version / profile tuple может быть допустима для paper, затем допустима для testnet и при этом ещё не быть admissible для live. Strategy admission всегда должен быть environment-sensitive.

16.5. Admission зависит от current posture системы

Strategy admission не должен читаться как статическая метка, одинаково действующая в любом posture. Strategy / version / profile tuple может оставаться в принципе admissible для данного environment, но быть временно недопустимой для новых действий в текущем restricted, blocked, frozen, safe-mode или manual-intervention posture.

16.6. Admission стратегии не равен факту существования core-level способности её исполнить

«Ядро умеет провести такую стратегию» и «данная версия стратегии разрешена к использованию в текущем режиме» — это разные суждения. Первое принадлежит архитектурной и технической зрелости ядра. Второе принадлежит governance-layer.

16.7. Material config change ставит вопрос об admissibility заново

Существенное изменение configuration profile не должно silently наследовать предыдущий admission verdict. Document №6 фиксирует только policy-правило: material config change breaks silent inheritance of prior admission.

16.8. Version change не должен молча наследовать prior live-admission

Новая version form не должна автоматически считаться admissible по инерции предыдущей. Более мягкие environments могут использоваться для ранней governance-validation новой version form, но более строгие environments требуют отдельного policy-reading этой версии.

16.9. Strategy admission не должен превращаться в strategy specification

Настоящий раздел не определяет, какая стратегия «хорошая», какие её сигналы правильные и как именно она должна принимать торговые решения. Strategy admission отвечает только на один policy-level вопрос: допустимо ли данное strategy / version / profile tuple как источник новых торговых действий в текущем режиме.

16.10. Strategy admission не равен release mechanics

Document №6 не описывает rollout sequence, approval workflow, branching model, deployment windows, rollback steps или действия оператора по выкладке версии. Governance фиксирует policy-boundary допуска; implementation and operational layers решают, каким образом этот boundary practically enforced.

16.11. Admission verdict по стратегии должен быть явным

Если strategy / version / profile tuple участвует в current trading environment как источник новых торговых действий, governance-layer должен читать его admissibility явно: admissible, restricted, temporarily not admissible или requiring separate reconsideration before use.

16.12. Итог раздела

Strategy admission / version policy boundaries являются частью внешнего governance-layer и не относятся ни к canonical core model, ни к deployment mechanics. Его admissibility зависит от environment mode и current posture системы. Material config change и version change не должны silently наследовать prior admission verdict. Документ фиксирует только policy-условия допуска версии и конфигурации к использованию как источника новых торговых действий.



17. Итоговые governance invariants

17.1. Governance внешен по отношению к core truth

Trading Governance не создаёт и не переопределяет canonical trading truth. Он работает только как внешний policy-layer поверх уже признанных core states, truth layers и outcomes.

17.2. Допуск торговли должен быть явным

Для новых торговых действий должен существовать явный admission verdict, а для ограничивающих состояний — явный operating posture.

17.3. Предпосылки являются обязательными

Новые торговые действия недопустимы без кумулятивного policy-basis: допустимого execution environment для текущей strategy/version/profile pair, admissible contextual basis, достаточной признанности affected state и отсутствия unresolved condition, несовместимого с trade admission.

17.4. Неопределённость не продолжает normal flow молча

Неопределённость, конфликт или reconcile-required condition не могут молча интерпретироваться как normal continuation. После их распознавания contour обязан перейти в ограничивающее policy-состояние.

17.5. Reconciliation outcome не является решением governance

ReconciliationResult несёт domain meaning для affected contour, но не является сам по себе разрешением на дальнейшую торговлю. Между reconcile outcome и return-to-flow всегда остаётся отдельный governance step.

17.6. Confirmed не означает автоматический resume

Даже подтверждённая или частично скорректированная reconcile-picture не открывает автоматически normal flow. Resume требует отдельного явного policy-basis.

17.7. Новые действия и protective actions — разные policy-классы

Запрет новых торговых действий не означает автоматический запрет protective continuation, а допустимость protective continuation не означает возврат к normal trading.

17.8. Неудачная защита усиливает ограничение

Если policy-level допустимая protective continuation не может быть реализована, restriction не ослабляется, а усиливается; affected contour должен перейти в более жёсткое ограничивающее состояние.

17.9. Blocked не равен frozen

Blocked posture означает запрет дальнейшего normal движения до появления basis for re-evaluation. Frozen posture сильнее: contour удерживается без автоматического самодвижения до explicit resolve. Эти postures не должны смешиваться ни в logic of escalation, ни в logic of resume.

17.10. Manual intervention является policy-категорией

Manual intervention не является operational noise или runbook substitute. Это отдельный governance-class для состояний, где internal automatic basis уже недостаточен для дальнейшего движения contour.

17.11. Authority boundary зависит от environment mode

Требование внешнего authority step и строгость resume-reading зависят от environment mode. Policy-consequence одного и того же clarified contour не обязана быть одинаковой в paper, testnet и live.

17.12. Допуск стратегии связан с policy, а не с deployment

Допуск стратегии относится к strategy / version / configuration profile tuple и не должен silently наследоваться при material config change или version change. При этом strategy admission не равен deployment mechanics и не превращается в release runbook.

17.13. Решения governance должны оставаться читаемыми

Каждое policy-значимое ограничение, усиление, удержание, manual boundary и return-to-flow должны оставаться формально читаемыми и объяснимыми. Неявная или произвольная интерпретация текущего торгового состояния системы несовместима с данным документом.

17.14. Итог раздела

Система не имеет права торговать, продолжать торговлю, ослаблять ограничение или возвращаться в flow по инерции, по локальной догадке или по неявной трактовке состояния. Для каждого такого шага должен существовать явный policy-basis, читаемый по affected contour, по environment mode и по already-recognized core truth. Только при соблюдении этих invariants governance остаётся самостоятельным внешним слоем комплекта, а не расплывчатым приложением к canonical core model.
