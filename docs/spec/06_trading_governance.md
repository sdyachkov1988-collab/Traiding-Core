# Trading Governance v0.1

## Назначение

Документ вводит внешний policy-layer поверх уже сформированной core truth model. Он отвечает не на вопрос "что есть торговая реальность", а на вопрос "когда системе разрешено торговать и в каком режиме".

## Роль governance-layer

Governance определяет:

- trade admission;
- trade restriction;
- block/freeze semantics;
- возврат в normal flow;
- связь между reconciliation outcomes и policy decisions.

## Важные разграничения

Governance не равен:

- `RiskDecision`
- `Context Gate`
- `Pre-execution Guard`
- `ReconciliationResult`

Все эти объекты и швы остаются частью core reality или соседних boundary-слоев. Governance читает их как входы для policy-level решения.

## Базовые policy states

Из документа следует, что система должна различать режимы вроде:

- `normal`
- `restricted`
- `blocked`
- `frozen`
- `safe-mode`
- `manual-intervention`

Также фигурируют admission verdicts:

- `allowed`
- `restricted`
- `denied`
- `suspended`
- `reconcile-required`

## Ключевые принципы

- governance не создает торговую истину;
- policy restriction сильнее локального удобства;
- нельзя silently continue under ambiguity;
- возврат в normal flow не должен быть автоматическим по умолчанию;
- governance decisions должны быть классифицируемыми и объяснимыми.

## Что пока не делаем

На этапе `Minimal Core v1` этот документ важен как reserved policy layer, но не как первый кодовый приоритет. Его нужно учитывать в проектировании seam'ов, но не втаскивать раньше времени в ядро, если это ломает фазовую границу технического roadmap.
