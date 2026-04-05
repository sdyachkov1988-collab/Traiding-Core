# Engineering Guardrails v0.8

## Назначение

Документ фиксирует обязательные инженерные правила применения ядра. Если они нарушены, код может выглядеть рабочим, но будет ненадежным или неаудируемым.

## Заход 1: Core invariants

Обязательные инварианты:

- Global internal IDs
- UTC-aware datetime only
- Decimal only
- Atomic state writes
- Idempotent Fill Processor

## Заход 2: Observability and traceability

Обязательные правила:

- structured logging with reason;
- metadata у `StrategyIntent`;
- явные причины отказа `Context Gate`;
- lineage rules между upstream и downstream сущностями.

## Заход 3: Boundary and safety

Обязательные правила:

- `MockExecutionAdapter` как boundary test;
- single source of truth for state;
- execution only behind interface;
- timeout / unknown state handling;
- minimal storage and locking discipline.

## Что это значит для будущего кода

- ID должны быть внутренними и глобально различимыми;
- время нельзя хранить как naive datetime;
- денежные значения и цены нельзя вести через `float`;
- запись состояния должна быть атомарной;
- повторная обработка fill не должна ломать состояние;
- логирование должно объяснять причину решения, а не просто факт события.

## Что этот документ не делает

- не определяет доменную сущность `Order`, `Fill` или `Position`;
- не описывает roadmap реализации;
- не задает governance policy.

Он отвечает именно за инженерную дисциплину вокруг уже согласованных контрактов.
