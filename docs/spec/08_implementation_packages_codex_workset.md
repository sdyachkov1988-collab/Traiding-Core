# Implementation Packages / Codex Workset v0.1

## Назначение

Документ `7B` завершает переход от interface contracts к рабочим implementation packages. Он не задает структуру репозитория буквально, но организует первую реализацию в audit-friendly units.

## Общие правила package layer

- пакеты строятся по load-bearing seams, а не по папкам;
- package не подменяет interface contract;
- package не имеет права обходить зависимости;
- один package не должен незаметно поглощать соседний seam;
- package layer обязан сохранять execution boundary и fill-driven discipline;
- package layer не заменяет hardening.

## Package A — Input and Context Foundation

Закрывает:

- `Normalized Event Input Contract`
- `Minimal MTF Input Seam Contract`

Роль:

- дать базовые доменные модели входа;
- дать normalized event flow;
- создать ранний MTF-ready input/context basis для первой стратегии.

Зависимости:

- upstream packages отсутствуют;
- downstream-пакеты зависят от него.

Практический вывод:

- это первый кодовый пакет, с которого надо начинать реализацию.

## Package B — Strategy Decision Boundary

Закрывает:

- `Strategy Contract`

Роль:

- принимать допустимый input/context basis только из `Package A`;
- выдавать только `StrategyIntent` или explicit no-action.

Зависимости:

- зависит от `Package A`;
- служит единственным непосредственным upstream основанием для `Package C`.

## Package C — Risk Verdict Boundary

Закрывает:

- `Risk Contract`

Роль:

- быть отдельным downstream verdict boundary между strategy и order construction.

## Что особенно важно для будущей работы

`7B` уже фактически задает безопасный backlog для Codex:

1. `Package A`
2. `Package B`
3. `Package C`
4. далее пакеты execution boundary, fill-driven spine и persistence

## Как использовать этот документ дальше

На следующем шаге можно прямо преобразовать его в:

- каркас директорий проекта;
- список модулей по пакетам;
- пошаговый backlog реализации;
- границы задач для последовательной разработки.
