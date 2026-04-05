# Core Contracts / Canonical Core Model v0.1

## Назначение

Документ фиксирует каноническую contract-level модель торгового ядра. Он описывает не код, а обязательные сущности, связи, смысловые различия и truth layers, по которым потом можно проверять реализацию.

## Две плоскости модели

### Upstream contextual layer

- `TimeframeContext`

### Canonical trading-truth layer

- `Signal`
- `Decision`
- `RiskDecision`
- `OrderIntent`
- `Order`
- `OrderState`
- `ExecutionEvent`
- `Fill`
- `Position`
- `Balance`
- `AccountState`
- `PortfolioState`
- `ReconciliationResult`

## Главные принципы

- разные слои торговой реальности не должны сливаться в одну "историю сделки";
- `intent`, `order`, `status`, `execution fact` и `reconciled truth` должны различаться;
- execution facts имеют больший вес, чем status-only представления;
- raw fact, observed state, derived state и reconciled truth являются разными уровнями модели;
- assembly-level упрощения первой сборки не становятся каноническими контрактами.

## Identity и temporal semantics

В документе явно разведены:

- internal identity и external reference;
- created / observed / effective / reconciled semantics;
- temporal ordering и causal ordering.

Это важно для будущих сущностей и журналов событий.

## Что входит в scope

- перечень канонических сущностей;
- связи между ними;
- lifecycle semantics;
- допустимые и запрещенные переходы;
- инварианты truth model;
- различие между contextual, decision, execution, accounting и reconciliation layers.

## Что не входит в scope

- инженерные правила из `Engineering Guardrails`;
- структура модулей и файлов;
- transport details и API adapters;
- governance-level правила допуска торговли;
- strategy parameters, UI и ops-manuals.

## Практический вывод для кода

Будущая реализация должна позволять отдельно выражать:

- аналитическое основание;
- торговое решение;
- риск-вердикт;
- исполнимое намерение;
- внешний order lifecycle;
- execution facts;
- position/account/portfolio truth;
- reconciliation outcome.

Если код начнет смешивать эти слои, он нарушит canonical model даже при формально работающем поведении.
