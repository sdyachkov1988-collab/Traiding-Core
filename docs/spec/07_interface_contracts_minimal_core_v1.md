# Interface Contracts / Minimal Core v1 v0.1

## Назначение

Документ `7A` фиксирует implementation-facing interface contracts для первой сборки `Minimal Core v1`. Это не каноническая модель всего ядра, а фазовый слой интерфейсных швов.

## Критическая фазовая граница

Документ описывает только интерфейсы, которые нужны для первой реализации. Он не имеет права превращать временные ограничения `Minimal Core v1` в постоянные invariants будущего ядра.

## Общие правила interface layer

- интерфейсы не могут обходить архитектурные швы;
- interface contract не подменяет domain contract;
- execution существует только behind interface;
- владение состоянием не должно расползаться между интерфейсами;
- input и output описываются на уровне доменных сущностей, а не vendor payload;
- reserved seams должны быть видимыми, но не становиться first-class obligations раньше времени.

## Основные интерфейсные контракты

### 1. Normalized Event Input Contract

Минимальный output:

- доменный `MarketEvent`, пригодный как вход для strategy-layer;
- без скрытого стратегического толкования.

### 2. Minimal MTF Input Seam Contract

Минимальный output:

- ранний согласованный MTF input;
- пригоден как strategy-facing contextual basis;
- еще не является полной contract family `TimeframeContext`.

### 3. Strategy Contract

Минимальный output:

- `StrategyIntent` или явный `no-action`.

### 4. Risk Contract

Минимальный output:

- `RiskDecision` как отдельный risk verdict;
- downstream order construction может читать только его, а не скрытые поля strategy-layer.

### 5. Order Construction Contracts

В документе зафиксирован seam для `Order Builder`, который получает:

- approved `RiskDecision`;
- instrument specs;
- execution capabilities в объеме, достаточном для построения исполнимого `OrderIntent`.

## Практический вывод

Следующий кодовый шаг должен строиться вокруг интерфейсов, а не вокруг классов "как удобнее". Это особенно важно для `Package A`, `Package B` и `Package C`.
