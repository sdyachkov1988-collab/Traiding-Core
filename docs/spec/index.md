# Trading Core Spec Index

Этот каталог переводит исходный комплект `.docx` в полнотекстовую Markdown-спецификацию для реализации `Minimal Core v1`.

Цель этого слоя:

- дать единую точку входа вместо чтения восьми `.docx` вручную;
- сохранить содержимое документов в текстовом формате, удобном для чтения и работы в репозитории;
- зафиксировать порядок чтения и зависимости между документами.

Важно:

- файлы в этом каталоге являются полнотекстовым переносом исходных `.docx` в `.md`;
- цель этого слоя — сохранить текст документов без summary и без смыслового сокращения;
- в случае сомнений по форматированию или структуре приоритет остается у исходных `.docx`.

## Источники

- `core_contracts_canonical_core_model_v0_1.docx`
- `engineering_guardrails_core_v1_v0_8.docx`
- `Implementation_Packages_Codex_workset_v0_1.docx`
- `Interface_Contracts_Minimal_Core_v1_v0_1.docx`
- `roadmap_torgovogo_yadra_v1_7_arch_final_polish_fixed-1.docx`
- `technical_roadmap_trading_core_v0_9.docx`
- `Trading_Domain_Model_v0_5-2.docx`
- `Trading_Governance_v0_1_final.docx`

## Порядок чтения

1. [roadmap_torgovogo_yadra_v1_7_arch_final_polish_fixed-1.md](./roadmap_torgovogo_yadra_v1_7_arch_final_polish_fixed-1.md)
2. [technical_roadmap_trading_core_v0_9.md](./technical_roadmap_trading_core_v0_9.md)
3. [engineering_guardrails_core_v1_v0_8.md](./engineering_guardrails_core_v1_v0_8.md)
4. [Trading_Domain_Model_v0_5-2.md](./Trading_Domain_Model_v0_5-2.md)
5. [core_contracts_canonical_core_model_v0_1.md](./core_contracts_canonical_core_model_v0_1.md)
6. [Trading_Governance_v0_1_final.md](./Trading_Governance_v0_1_final.md)
7. [Interface_Contracts_Minimal_Core_v1_v0_1.md](./Interface_Contracts_Minimal_Core_v1_v0_1.md)
8. [Implementation_Packages_Codex_workset_v0_1.md](./Implementation_Packages_Codex_workset_v0_1.md)

## Логика комплекта

Комплект читается как последовательность из восьми слоев:

1. Архитектурный roadmap задает устройство ядра и его границы.
2. Технический roadmap переводит архитектуру в очередность реализации.
3. Engineering Guardrails фиксирует обязательные инженерные инварианты.
4. Trading Domain Model объясняет реальность рынка, исполнения и восстановления.
5. Core Contracts задает канонические сущности и truth layers.
6. Trading Governance добавляет внешний policy-layer допуска и ограничений.
7. Interface Contracts формализует интерфейсные швы для `Minimal Core v1`.
8. Implementation Packages превращает интерфейсные швы в рабочие пакеты реализации.

## Что уже можно делать на основе этого каталога

- строить каркас проекта `Minimal Core v1`;
- формализовать доменные модели без преждевременного углубления в адаптеры;
- внедрять интерфейсы по фазовой границе `7A`;
- реализовывать пакеты `A -> B -> C -> ...` по документу `7B`;
- писать audit-friendly тесты на инварианты и контрактные границы.

## Рекомендуемая следующая работа

После завершения этого шага опираться на следующий порядок:

1. создать архитектурный skeleton репозитория;
2. выделить базовые domain objects и протоколы;
3. начать с `Package A — Input and Context Foundation`;
4. только затем переходить к `Strategy`, `Risk` и execution spine.
