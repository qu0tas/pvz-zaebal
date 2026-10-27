# Вход для агента

Это репозиторий статического планировщика Garden Ops на Time Park, с экспериментальной локальной генерацией трёх BIN; это не готовый FBMOD.

1. Прочитай `skills/maintain-timepark-planner/SKILL.md`.
2. Для структуры и JSON открой `docs/ARCHITECTURE.md`; для генератора — `docs/BIN-BUILDER.md`; для игровых исследований — `docs/GAME-MODDING-NOTES.md`.
3. Правь `src/`, `data/`; `index.html` — только результат `python scripts/build.py`.
4. Запусти `python scripts/build.py --check` и `python -m unittest discover -s tests -v`, затем `node tests/bin_builder.cjs`.
5. При визуальных правках проверь фотографии, клики, экспорт, desktop и mobile. Python-тесты не заменяют визуальную проверку.

Инварианты: фон не отражать без прямого запроса; `photo x/y` не равно `world X/Y/Z`; метка Axx не является SpawnID; не менять GUID/координаты мира при перемещении значков. Импорт старого JSON сохраняет номера назначенных точек.

Не объявляй игровые спавны исправленными по одному XML. Не публикуй игровые BIN/XML, FBMOD/FBPROJECT и local-game-files. Не запускай агента, не пушь и не развёртывай сайт без соответствующего запроса и доступа к конкретному репозиторию. Зафиксируй, какие проверки реально выполнил.
