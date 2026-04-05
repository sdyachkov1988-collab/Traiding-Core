# Trading Core Spec Index

Этот каталог переводит исходный комплект `.docx` в рабочую Markdown-спецификацию для реализации `Minimal Core v1`.

Цель этого слоя:

- дать единую точку входа вместо чтения восьми документов вручную;
- зафиксировать порядок чтения и зависимости между документами;
- подготовить базу для следующих шагов: архитектурный каркас, доменные модели, интерфейсы и implementation packages.

Важно:

- это не дословная перепечатка исходных документов;
- это рабочий конспект и карта решений для разработки;
- в случае конфликта источником истины остаются исходные `.docx`.

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

1. [01_architectural_roadmap.md](./01_architectural_roadmap.md)
2. [02_technical_roadmap.md](./02_technical_roadmap.md)
3. [03_engineering_guardrails.md](./03_engineering_guardrails.md)
4. [04_trading_domain_model.md](./04_trading_domain_model.md)
5. [05_core_contracts.md](./05_core_contracts.md)
6. [06_trading_governance.md](./06_trading_governance.md)
7. [07_interface_contracts_minimal_core_v1.md](./07_interface_contracts_minimal_core_v1.md)
8. [08_implementation_packages_codex_workset.md](./08_implementation_packages_codex_workset.md)

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
