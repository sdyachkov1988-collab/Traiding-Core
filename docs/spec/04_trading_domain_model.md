# Trading Domain Model v0.5

## Назначение

Документ раскрывает доменную реальность, с которой работает торговое ядро. Его задача не в том, чтобы диктовать структуру кода, а в том, чтобы убрать опасные упрощения о рынке, данных и исполнении.

## Заход 1: Order lifecycle and execution reality

Ключевые выводы:

- `signal`, `order` и `execution result` не тождественны;
- order lifecycle имеет самостоятельные состояния;
- fill mechanics должны быть отдельным слоем фактов;
- комиссии, спред и проскальзывание являются частью торговой реальности, а не только пост-фактум аналитикой.

## Заход 2: Market data reality

Ключевые выводы:

- market data является представлением рынка, а не самим рынком;
- trades, quotes, book и bars являются разными объектами;
- event time, arrival time и ordering reality не совпадают;
- бары упрощают и искажают исходную последовательность событий;
- возможны gaps, duplicates и stale views.

## Заход 3: Execution uncertainty and recovery reality

Ключевые выводы:

- execution truth не известна мгновенно;
- submitted action, observed order state и fill reality живут на разных слоях;
- внешние подтверждения могут отсутствовать, задерживаться, дублироваться или конфликтовать;
- recovery и reconciliation являются штатной частью ядра.

## Заход 4: Market structure differences

Ключевые выводы:

- spot, borrowed exposure и contract exposure имеют разный доменный смысл;
- instrument specification определяет, что вообще считается исполнимым действием;
- semantics цены, количества, позиции и fee зависят от типа рынка;
- один и тот же торговый intent не переносится между market structures без адаптации.

## Практический вывод для реализации

- нельзя выводить позицию напрямую из strategy-layer;
- нельзя считать order status окончательной execution truth;
- нельзя строить модель только вокруг свечей;
- recovery и reconciliation надо учитывать уже в дизайне сущностей;
- instrument specs должны быть частью исполнимой реальности, а не справочной метаинформацией.
