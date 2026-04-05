# Technical Roadmap v0.9

## Назначение

Технический roadmap переводит архитектуру в последовательность инженерных заходов. Он отвечает на вопрос, что именно собирать первым, какие есть зависимости и когда фаза считается завершенной.

## Scope текущей редакции

В документ входят три захода:

1. `Minimal Core v1`
2. `MTF + recovery + reconciliation`
3. `Hardening`

В документ сознательно не входят:

- governance и эксплуатационные политики;
- multi-instrument/multi-strategy зрелость;
- multi-exchange abstraction;
- поздние расширения derivatives и orchestration.

## Заход 1: Minimal Core v1

Волны реализации:

- `1A` Domain foundation
- `1B` Event normalization and strategy entry point
- `1C` Minimal MTF input seam
- `1D` Decision pipeline
- `1E` Execution and fill-driven accounting spine
- `1F` State survivability
- `1G` End-to-end acceptance slice

## Заход 2: MTF + recovery + reconciliation

Волны реализации:

- `2A` MTF foundation
- `2B` Trading admission through Context Gate
- `2C` Unknown states and safe recovery semantics
- `2D` Reconciliation as a normal operating loop
- `2E` Position-originated close routing contour

Минимальный технический контракт `TimeframeContext` к этому этапу должен включать:

- `context_id`
- `instrument_id`
- `entry_timeframe`
- `timeframe_set`
- сведения о последних допустимых closed bars по каждому таймфрейму
- readiness/freshness flags
- ссылку на alignment policy

## Заход 3: Hardening

Волны реализации:

- `3A` Correctness of execution facts
- `3B` State safety
- `3C` Observability
- `3D` Controllable test boundary
- `3E` Correctness tests
- `3F` Fault scenario tests

## Практический вывод для проекта

На текущем шаге мы должны ориентироваться именно на `Заход 1`. Это значит:

- строить `Minimal Core v1`, а не сразу полное зрелое ядро;
- оставлять reserved seams для `TimeframeContext`, reconciliation и recovery;
- не пропускать волны, которые задают причинный порядок сборки.

## Запреты чтения документа

- нельзя трактовать первую сборку как финальную форму ядра;
- нельзя реализовывать Заход 2 и 3 раньше, чем заложен минимальный вертикальный срез;
- нельзя путать technical order реализации с канонической доменной моделью.
