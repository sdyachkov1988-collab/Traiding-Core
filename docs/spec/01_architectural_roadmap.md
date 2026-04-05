# Architectural Roadmap v1.7

## Назначение

Архитектурный roadmap задает форму торгового ядра как системы. Он отвечает на вопрос, какие обязательные слои и контуры вообще должны существовать, но не превращается в код или пакетную структуру.

## Главная роль документа

- определить границы торгового ядра;
- описать обязательные доменные сущности и архитектурные швы;
- задать жизненный цикл торгового потока;
- зафиксировать состав `Minimal Core v1`;
- отделить архитектуру ядра от governance и эксплуатации.

## Ключевой торговый цикл

Базовая архитектурная последовательность выглядит так:

1. Ядро получает нормализованное рыночное событие.
2. Timeframe layer собирает согласованный контекст.
3. `Context Gate` проверяет готовность контекста.
4. `Strategy Engine` формирует `StrategyIntent` или no-action.
5. `Risk Engine` выдает отдельный риск-вердикт.
6. `Pre-execution Guard` повторно проверяет исполнимость.
7. `Order Builder` создает `OrderIntent`.
8. `Execution Coordinator` работает только через execution boundary.
9. `Fill Processor` обновляет order/fill reality.
10. `Position Engine` и `Portfolio Engine` формируют позиционную и учетную реальность.
11. `State Store` сохраняет состояние.
12. `Reconciliation Layer` сверяет локальную и внешнюю картину.

## Состав Minimal Core v1

Минимальный архитектурный состав:

- Core models
- Event layer
- Minimal MTF input seam
- Strategy contract
- Risk engine
- Order builder
- Execution contract
- Fill processor
- Position engine
- Portfolio engine
- State store
- Startup reconciliation

## Важные архитектурные идеи

- MTF-контекст является first-class seam, но в первой реализации может существовать в минимальной фазовой форме.
- Исполнение должно быть изолировано за интерфейсом.
- Fill-driven accounting spine важнее status-only трактовок.
- Reconciliation является штатной способностью ядра, а не только аварийным режимом.
- Governance остается внешним policy-level слоем, а не частью доменной истины.

## Что это значит для реализации

- не смешивать strategy, risk, execution и accounting в один модуль;
- не строить ядро вокруг adapter-specific API;
- сразу проектировать швы между слоями;
- не превращать assembly-level компромиссы в постоянные правила ядра.

## Что не нужно делать на этом этапе

- канонизировать структуру репозитория;
- вводить vendor-specific transport semantics внутрь доменной модели;
- смешивать governance и risk;
- подменять execution facts предположениями о результате приказа.
