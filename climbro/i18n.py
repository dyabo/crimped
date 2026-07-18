"""
climbro — internationalization (v1: English + Russian).

Design:
- Gettext-style: user-facing English literals stay in the code and are wrapped
  with a translator `t(...)`. The Russian catalog `_RU` below maps the English
  SOURCE STRING -> Russian. Anything not in the catalog falls back to English,
  so a missing translation degrades gracefully (the app never breaks).
- Dynamic strings use named `{placeholders}`; call sites pass them as kwargs and
  `t()` runs `.format(**kw)` after the lookup, so the same key works in both langs.

Reviewers: this file is the single place to check/adjust all Russian wording.
"""

from __future__ import annotations
from enum import Enum


class Language(str, Enum):
    EN = "en"
    RU = "ru"


# --------------------------------------------------------------------------- #
# English source -> Russian.  Keep placeholders ({name}) identical across langs.
# --------------------------------------------------------------------------- #
_RU: dict[str, str] = {
    # ---- CLI wizard chrome ---------------------------------------------------
    "\nclimbro — let's build your plan. Answer a few questions.\n":
        "\nclimbro — соберём твой план. Ответь на несколько вопросов.\n",
    " [optional, Enter to skip]": " [необязательно, Enter — пропустить]",
    "  (required)": "  (обязательно)",
    "  invalid — try again": "  неверно — попробуй ещё раз",
    "(y/n)": "(д/н)",
    "PyYAML is required for --config (pip install pyyaml).":
        "Для --config нужен PyYAML (pip install pyyaml).",
    "\nCan't generate — fix these:": "\nНе получится собрать — исправь:",
    "\n✓ Wrote {path}": "\n✓ Записано в {path}",
    "  {weeks} weeks · goal V{v} · finger norm {pct}%BW (+{kg}{unit})":
        "  {weeks} нед · цель V{v} · норма пальцев {pct}%ВТ (+{kg}{unit})",
    "  Start on the Dashboard; log sessions in Journal and a weekly check-in in Week.":
        "  Начни с «Дашборда»; записывай сессии в «Дневник», а еженедельную сверку — в «Неделя».",

    # ---- Survey prompts (keys = English prompt text in schema.SURVEY) --------
    "Your name (optional, for the file)": "Твоё имя (необязательно, для файла)",
    "Sex (for strength norms)": "Пол (для норм силы)",
    "Age (optional)": "Возраст (необязательно)",
    "Units": "Единицы",
    "Current bodyweight": "Текущий вес тела",
    "Grade scale to display": "Шкала категорий для отображения",
    "Current hardest grade (consistent, not one-off)":
        "Текущая максимальная категория (стабильная, не разовая)",
    "Target grade": "Целевая категория",
    "Years climbing": "Лет в скалолазании",
    "Added load on a 20mm edge, 7s hang (optional)":
        "Доп. вес на зацепе 20 мм, вис 7 с (необязательно)",
    "Added load on a weighted pull-up (optional)":
        "Доп. вес на подтягивании (необязательно)",
    "Primary goal": "Основная цель",
    "Start date (blank = today)": "Дата старта (пусто = сегодня)",
    "Goal / competition date": "Дата цели / соревнования",
    "Do you want to lose weight as part of this?": "Хочешь снижать вес в рамках плана?",
    "Target bodyweight (if cutting)": "Целевой вес тела (если сушка)",
    "Training days per week (2–7)": "Тренировочных дней в неделю (2–7)",
    "Which weekdays (optional, e.g. Mon Tue Thu Sat)":
        "Какие дни недели (необязательно, напр. Пн Вт Чт Сб)",
    "Do you have a fingerboard/hangboard?": "Есть ли фингерборд/ханборд?",
    "Do you have a system board (MoonBoard/Kilter/Tension)?":
        "Есть ли систем-борд (MoonBoard/Kilter/Tension)?",
    "Do you have gym/weights access?": "Есть ли доступ в зал/к весам?",
    "Wearable for recovery metrics": "Гаджет для метрик восстановления",
    "Include a mobility block?": "Добавить блок мобильности?",
    "Include lead / rope sessions in the plan?":
        "Добавить в план сессии с верёвкой (трудность)?",
    "Include the nutrition sheet?": "Добавить лист питания?",

    # ---- Enum display values -------------------------------------------------
    "male": "мужской", "female": "женский",
    "kg": "кг", "lb": "фунт",
    "garmin": "garmin", "other": "другой", "none": "нет",
    "send_grade": "пройти категорию", "competition": "соревнование",
    "yes": "да", "no": "нет",

    # ---- Weekdays ------------------------------------------------------------
    "Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт",
    "Fri": "Пт", "Sat": "Сб", "Sun": "Вс",

    # ---- Validation (schema.validate) ---------------------------------------
    "profile.bodyweight must be positive.": "profile.bodyweight должен быть положительным.",
    "profile.age looks unusual; double-check.": "profile.age выглядит необычно; перепроверь.",
    "climbing.target_grade is below current_grade — pick a target at or above your current level.":
        "climbing.target_grade ниже current_grade — выбери цель не ниже текущего уровня.",
    "Target is {jump} V-grades above current — that is very ambitious for one cycle; consider a nearer target.":
        "Цель на {jump} категорий выше текущей — это очень амбициозно для одного цикла; рассмотри более близкую цель.",
    "goal.goal_date must be after start_date.": "goal.goal_date должна быть позже start_date.",
    "Only {wks} weeks to the goal — climbro needs at least {min} for a sane cycle (otherwise the taper would land after your goal date). Move the date or pick a nearer goal.":
        "До цели всего {wks} нед — climbro нужно минимум {min} для вменяемого цикла (иначе подводка окажется позже даты цели). Сдвинь дату или выбери более близкую цель.",
    "{wks} weeks is tight — phases will be heavily compressed.":
        "{wks} нед — впритык, фазы будут сильно сжаты.",
    "{wks} weeks is a long horizon; consider splitting into multiple cycles.":
        "{wks} нед — длинный горизонт; рассмотри разбиение на несколько циклов.",
    "weight.enabled is true but weight.target_bodyweight is missing.":
        "weight.enabled = true, но weight.target_bodyweight не задан.",
    "weight.target_bodyweight must be below current bodyweight when cutting.":
        "weight.target_bodyweight должен быть ниже текущего веса при сушке.",
    "Implied loss ~{pct}%/wk exceeds your cap {cap}%/wk — the engine will cap the rate and the cut won't finish by the goal date.":
        "Расчётная потеря ~{pct}%/нед превышает твой лимит {cap}%/нед — движок ограничит темп, и сушка не завершится к дате цели.",
    "weight.max_rate_pct outside 0.2–1.0%/wk; >1% risks muscle/strength loss.":
        "weight.max_rate_pct вне 0.2–1.0%/нед; >1% рискует потерей мышц/силы.",
    "availability.days_per_week must be between 2 and 7.":
        "availability.days_per_week должно быть от 2 до 7.",
    "availability.available_days has invalid weekday(s): {bad} (use {valid}).":
        "availability.available_days содержит неверные дни: {bad} (используй {valid}).",
    "availability.available_days length must equal days_per_week.":
        "длина availability.available_days должна равняться days_per_week.",
    "No fingerboard: finger-strength work will be redirected to on-the-wall protocols.":
        "Нет фингерборда: работа на силу пальцев уйдёт в протоколы на стенде.",
    "No gym access: strength work will use bodyweight/board alternatives.":
        "Нет доступа в зал: силовая пойдёт с весом тела/на борде.",

    # ---- Session kinds (engine K_*) -----------------------------------------
    "Max hangs": "Макс. висы",
    "Active pulls": "Активные тяги",
    "Limit bouldering": "Лимитный боулдеринг",
    "Volume / technique": "Объём / техника",
    "Strength on the wall": "Сила на стенде",
    "Power-endurance": "Силовая выносливость",
    "Gym strength": "Силовая (зал)",
    "Zone 2 cardio": "Кардио (Зона 2)",
    "Lead climbing": "Лазание с верёвкой",
    "Rest / mobility": "Отдых / мобильность",

    # ---- Session intents -----------------------------------------------------
    "Max hangs on 20mm, fresh, before climbing":
        "Макс. висы на 20 мм, на свежих силах, до лазания",
    "Active recruitment pulls into a fixed edge":
        "Активные тяги в неподвижную зацепу (рекрутинг)",
    "Limit bouldering, long rests, fresh":
        "Лимитный боулдеринг, длинный отдых, на свежих силах",
    "Volume + footwork/technique, sub-limit":
        "Объём + работа ног/техника, ниже предела",
    "Strength on the wall (system board), 4-7s holds":
        "Сила на стенде (систем-борд), удержания 4–7 с",
    "Power-endurance (4x4 / intervals / comp sim)":
        "Силовая выносливость (4×4 / интервалы / симуляция соревнований)",
    "Weighted pulls, antagonists, core":
        "Тяги с весом, антагонисты, кор",
    "Easy aerobic, conversational pace":
        "Лёгкое аэробное, разговорный темп",
    "Routes on a rope: mileage below limit (base) or linked circuits for power-endurance (bridge/peak); log honest RPE":
        "Трассы с верёвкой: накат ниже предела (база) или связки на силовую выносливость (переход/пик); честно ставь RPE",
    "Rest or mobility": "Отдых или мобильность",

    # ---- Phase names (keep the ' — ' separator: Week sheet splits on it) -----
    "Assess & baseline": "Оценка и базовые замеры",
    "Base — max hangs + technique": "База — макс. висы + техника",
    "Contact strength": "Контактная сила",
    "Bridge — exit deficit & build power": "Переход — выход из дефицита и рост мощности",
    "Bridge — build power": "Переход — рост мощности",
    "Peak — power & RFD": "Пик — мощность и RFD",
    "Taper": "Подводка",

    # ---- Phase focus fragments (concatenated in periodization) --------------
    "Tests (max hang, pull-ups, body comp) + baseline HRV/weight. Maintenance eating.":
        "Тесты (макс. вис, подтягивания, состав тела) + базовые ВСР/вес. Питание на поддержании.",
    "Max-hang finger strength + high technique volume.":
        "Сила пальцев через макс. висы + большой объём техники.",
    " Deficit starts.": " Старт дефицита.",
    "Active recruitment pulls + strength-on-the-wall; limit bouldering 2x.":
        "Активные тяги (рекрутинг) + сила на стенде; лимитный боулдеринг 2×.",
    " Deficit continues.": " Дефицит продолжается.",
    "Return to maintenance eating; power rises; introduce power-endurance.":
        "Возврат к питанию на поддержании; растёт мощность; вводим силовую выносливость.",
    "Raise intensity; introduce power-endurance.":
        "Повышаем интенсивность; вводим силовую выносливость.",
    "Peak contact strength, power and RFD on light bodyweight.":
        "Пик контактной силы, мощности и RFD на лёгком весе тела.",
    "Peak contact strength, power and RFD.":
        "Пик контактной силы, мощности и RFD.",
    " Comp-style simulations.": " Симуляции в формате соревнований.",
    "Volume -50%, intensity held; carb-load into the comp.":
        "Объём −50%, интенсивность держим; углеводная загрузка к соревнованию.",
    "Volume -50%, intensity held; arrive fresh for the send window.":
        "Объём −50%, интенсивность держим; подходим свежими к окну попыток.",

    # ---- Schedule sheet ------------------------------------------------------
    "Schedule · Assess & Base": "Расписание · Оценка и База",
    "Schedule · Contact": "Расписание · Контактная сила",
    "Schedule · Bridge & Peak": "Расписание · Переход и Пик",
    "Schedule · Taper": "Расписание · Подводка",
    "Week {week} · {phase}": "Неделя {week} · {phase}",
    "  ·  DELOAD": "  ·  РАЗГРУЗКА",
    "  ·  planned {wt}kg": "  ·  план {wt} кг",
    "Day": "День", "Type": "Тип", "Session": "Сессия", "What": "Что",
    "rest": "отдых", "quality": "качество", "support": "поддержка",
    "Focus: {focus}": "Фокус: {focus}",
    "Quality days (green) = fingers/limit, kept fresh and ≥48h apart. Support = technique/strength/cardio. Rearranging days won't break anything — keep the spacing.":
        "Качественные дни (зелёные) = пальцы/лимит, на свежих силах и ≥48 ч между ними. Поддержка = техника/сила/кардио. Переставлять дни можно — сохраняй интервалы.",

    # ---- Setup sheet ---------------------------------------------------------
    "Setup — your inputs for this plan": "Настройка — твои вводные для плана",
    "Name": "Имя", "Sex": "Пол", "Age": "Возраст",
    "used for finger-strength norms": "используется для норм силы пальцев",
    "Start bodyweight": "Стартовый вес тела",
    "Current grade": "Текущая категория", "scale: {s}": "шкала: {s}",
    "Goal": "Цель", "Start date": "Дата старта",
    "Goal date": "Дата цели", "{weeks} weeks": "{weeks} нед",
    "influences technique vs strength emphasis": "влияет на акцент техника/сила",
    "Cut enabled": "Сушка включена",
    "Target bodyweight": "Целевой вес тела",
    "Training days/week": "Тренир. дней/нед",
    "Fingerboard": "Фингерборд", "System board": "Систем-борд",
    "MoonBoard / Kilter / Tension": "MoonBoard / Kilter / Tension",
    "Gym access": "Доступ в зал", "Wearable": "Гаджет",
    "Mobility block": "Блок мобильности",
    "Lead sessions": "Сессии с верёвкой",
    "1x/week: replaces volume (base) / PE slot (peak)":
        "1×/нед: заменяет объём (база) / силовую выносливость (пик)",
    "Nutrition sheet": "Лист питания",
    "Finger-strength target": "Цель по силе пальцев",
    "To match the {tgt} norm: ~{pct}% bodyweight (7 s, 20 mm, two hands) = about +{kg} {unit} added at {bw} {unit}. Population guide, not a hard rule.":
        "Чтобы соответствовать норме {tgt}: ~{pct}% веса тела (7 с, 20 мм, две руки) = примерно +{kg} {unit} доп. веса при {bw} {unit}. Популяционный ориентир, не жёсткое правило.",

    # ---- Cycle sheet ---------------------------------------------------------
    "Cycle — your macrocycle (dates & planned weight computed)":
        "Цикл — твой макроцикл (даты и плановый вес вычислены)",
    "Wk": "Нед", "Dates": "Даты", "Phase": "Фаза", "Deload": "Разгрузка",
    "Focus": "Фокус", "Plan wt": "План вес", "Sessions": "Сессии",
    "DELOAD": "РАЗГРУЗКА",
    "Planned weight follows your cut curve (green = deficit weeks). Day-by-day sessions are on the phase schedule sheets. What you actually do goes in Journal / Week.":
        "Плановый вес идёт по кривой сушки (зелёный = недели дефицита). Сессии по дням — на листах расписания фаз. Что реально сделал — в «Дневник» / «Неделя».",

    # ---- Journal sheet -------------------------------------------------------
    "Journal — one row per session": "Дневник — одна строка на сессию",
    "Date": "Дата", "Min": "Мин", "RPE 1-10": "RPE 1–10", "Load": "Нагрузка",
    "Hang +{unit}": "Вис +{unit}", "Grade V": "Кат. V", "Volume": "Объём",
    "Pain 0-3": "Боль 0–3", "Notes": "Заметки",
    "start date (don't edit) →": "дата старта (не менять) →",

    # ---- Week sheet ----------------------------------------------------------
    "Week — fill yellow; the rest computes": "Неделя — заполняй жёлтое; остальное считается",
    "Baseline HRV:": "Базовая ВСР:", "Baseline resting HR:": "Базовый пульс покоя:",
    "No wearable selected — HRV / resting-HR columns are optional.":
        "Гаджет не выбран — столбцы ВСР / пульса покоя необязательны.",
    "Weight": "Вес", "Plan wt": "План вес", "Δ plan": "Δ план", "Δ/wk": "Δ/нед",
    "Pace": "Темп", "HRV": "ВСР", "HRV−base": "ВСР−база", "Rest HR": "Пульс покоя",
    "RHR−base": "ПП−база", "Sleep h": "Сон, ч", "Fatigue 1-10": "Усталость 1–10",
    "Chronic": "Хронич.", "ACWR": "ACWR", "Fingers %BW": "Пальцы %ВТ",
    "To target": "До цели", "Max pain": "Макс. боль", "Week status": "Статус недели",
    "Sleep Q 1-5": "Качество сна 1–5", "Stress 1-10": "Стресс 1–10",
    "Plan ses": "План сес", "Done %": "Готово %",
    # status strings (must match exactly; searched by emoji in conditional formatting)
    "🔴 Finger pain": "🔴 Боль в пальцах",
    "🔴 Load spike": "🔴 Скачок нагрузки",
    "🔴 Cutting too fast": "🔴 Слишком быстрая сушка",
    "🟡 Fatigue (HRV↓)": "🟡 Усталость (ВСР↓)",
    "🟡 High fatigue": "🟡 Высокая усталость",
    "🟡 High stress": "🟡 Высокий стресс",
    "🟡 Poor sleep": "🟡 Плохой сон",
    "🟡 Behind on weight": "🟡 Отстаёшь по весу",
    "🟢 On track": "🟢 В графике",

    # ---- Pace values (Week col I; also matched in conditional formatting) ----
    "fast": "быстро", "gain": "набор", "ok": "норм",

    # ---- Injuries sheet ------------------------------------------------------
    # NOTE: these status values are also used inside COUNTIF / conditional-format
    # formulas — the code applies the SAME translation on both sides, so they stay
    # in sync. Type values are display-only.
    "Active": "Активна", "Rehab": "Реабилитация", "Resolved": "Закрыта",
    "Finger/tendon": "Палец/сухожилие", "Elbow": "Локоть", "Shoulder": "Плечо",
    "Wrist": "Запястье", "Knee": "Колено", "Back": "Спина", "Other": "Другое",
    "Injuries & niggles — log + rehab": "Травмы и ниглы — журнал + реабилитация",
    "Start date": "Дата начала", "Area / location": "Зона / локализация",
    "Severity 0-3": "Тяжесть 0–3", "Status": "Статус", "Days": "Дни",
    "What I'm doing (rehab)": "Что делаю (реабилитация)", "Resolved date": "Дата закрытия",
    "Log what affects your training: a structural niggle (finger / tendon / joint), pain under load, or anything lasting past the next session — set status Active and unload that area. Do NOT log bumps, skin / flappers, or one-off soreness with an obvious cause (a Journal note is enough). When unsure: unexplained finger/tendon pain, or lost grip function → log it. 'Days' auto-counts (to resolved date or today); Active/Rehab rows feed the Dashboard advisor.":
        "Записывай то, что влияет на тренировки: структурный нигл (палец / сухожилие / сустав), боль под нагрузкой или всё, что тянется дольше следующей сессии — ставь статус «Активна» и разгружай зону. НЕ записывай ушибы, кожу / надрывы кожи и разовую крепатуру с очевидной причиной (хватит заметки в «Дневнике»). Если сомневаешься: необъяснимая боль в пальце/сухожилии или потеря хвата → записывай. «Дни» считаются автоматически (до даты закрытия или сегодня); строки «Активна»/«Реабилитация» питают советчик на «Дашборде».",

    # ---- Charts sheet --------------------------------------------------------
    "Charts (populate as you log)": "Графики (заполняются по мере записей)",
    "Weight: actual vs plan": "Вес: факт vs план",
    "Fingers %BW (target {pct}%)": "Пальцы %ВТ (цель {pct}%)",
    "Best grade / week (V)": "Лучшая категория / нед (V)",
    "Weekly load: acute vs chronic (sRPE)": "Недельная нагрузка: острая vs хроническая (sRPE)",
    "ACWR — overload risk": "ACWR — риск перегруза",
    "Sessions: planned vs done": "Сессии: план vs факт",
    "Fatigue & stress (1-10)": "Усталость и стресс (1–10)",
    "Sleep (h / night)": "Сон (ч / ночь)",
    "Max finger pain (0-3)": "Макс. боль в пальцах (0–3)",
    "HRV & resting HR": "ВСР и пульс покоя",
    "Lines appear as Week fills in. Axes are pre-scaled to your plan's range; keep ACWR in the 0.8–1.3 band and finger pain at 0.":
        "Линии появляются по мере заполнения «Недели». Оси заранее подогнаны под диапазон твоего плана; держи ACWR в коридоре 0.8–1.3, а боль в пальцах — на 0.",

    # ---- Dashboard: KPIs -----------------------------------------------------
    "Dashboard — where you are and what to do": "Дашборд — где ты и что делать",
    "Now (last completed week)": "Сейчас (последняя завершённая неделя)",
    "Reading": "Чтение",
    "Current weight": "Текущий вес", "From the latest check-in": "Из последней сверки",
    "Lost so far": "Сброшено", "From start": "От старта",
    "Left to target": "Осталось до цели", "≤0 = weight goal met": "≤0 = цель по весу достигнута",
    "Current phase": "Текущая фаза", "Where you are in the plan (by date)": "Где ты в плане (по дате)",
    "(bw+hang)/bw": "(вес+вис)/вес",
    "To V-target norm": "До нормы целевой V", "≤0 = V{v} finger norm reached": "≤0 = норма пальцев V{v} достигнута",
    "Best grade (wk)": "Лучшая кат. (нед)", "Max in a week": "Максимум за неделю",
    "Week load (sRPE)": "Нагрузка нед (sRPE)", "Sum of min×RPE": "Сумма мин×RPE",
    "ACWR (overload risk)": "ACWR (риск перегруза)", "0.8–1.3 ok · >1.5 risky": "0.8–1.3 норм · >1.5 риск",
    "Composite traffic light": "Сводный светофор",
    "Weeks logged": "Недель записано", "Check-ins so far": "Сверок пока",
    "Sessions logged": "Сессий записано", "Journal rows": "Строк в дневнике",
    "Week completion": "Выполнение недели", "Actual ÷ planned sessions": "Факт ÷ план сессий",
    "Active injuries": "Активные травмы", "Active + rehab (see Injuries)": "Активные + реабилитация (см. «Травмы»)",
    "Fingers %BW": "Пальцы %ВТ",

    # ---- Dashboard: advisor (fragments concatenated into Excel formulas) ----
    "Advisor": "Советчик",
    "-0.5 kg/wk": "-0.5 кг/нед", "-1.1 lb/wk": "-1.1 фунт/нед",
    "Weight: down ": "Вес: минус ",
    " of ": " из ",
    " kg, ": " кг, ",
    " to go. ": " осталось. ",
    "Behind the planned curve — add ~100-150 kcal deficit or 1 Zone-2 session.":
        "Отстаёшь от плановой кривой — добавь ~100–150 ккал дефицита или 1 сессию Зоны 2.",
    "Faster than planned — raise calories; aim {rate} to keep strength.":
        "Быстрее плана — подними калории; целься {rate}, чтобы сохранить силу.",
    "On the planned curve.": "На плановой кривой.",
    "Weight: enter a bodyweight in Week.": "Вес: введи вес тела в «Неделя».",
    "Fingers: ": "Пальцы: ",
    " BW; to the V{v} norm (": " ВТ; до нормы V{v} (",
    ") ": ") ",
    "— reached. Now convert it on the wall (technique, limit).":
        "— достигнута. Теперь реализуй её на стенде (техника, лимит).",
    "need ": "нужно ещё ",
    " pts (~": " п. (~",
    " {unit}). Keep 2 finger sessions/wk, add load slowly.":
        " {unit}). Держи 2 пальцевые сессии/нед, добавляй вес медленно.",
    "Fingers: log a max hang in Journal.": "Пальцы: запиши макс. вис в «Дневник».",
    "Fatigue: ACWR ": "Усталость: ACWR ",
    ". ": ". ",
    "Sharp jump — next week drop 1 power-endurance/volume session and add a rest day.":
        "Резкий скачок — на след. неделе убери 1 сессию силовой выносливости/объёма и добавь день отдыха.",
    "Low — you can add 1 volume/technique session.":
        "Низко — можешь добавить 1 сессию объёма/техники.",
    "In the optimal band, hold steady.": "В оптимальном коридоре, держи темп.",
    "Fatigue: ACWR builds after ~2-3 logged weeks.":
        "Усталость: ACWR набирается после ~2–3 записанных недель.",
    "⚠ Active injuries: ": "⚠ Активные травмы: ",
    " — follow the rehab in Injuries, don't load the area, swap the affected sessions.":
        " — следуй реабилитации в «Травмы», не нагружай зону, замени затронутые сессии.",
    "Injuries: none active.": "Травмы: активных нет.",
    "Finger pain ": "Боль в пальцах ",
    "/3 — rest fingers, switch to legs/cardio/mobility, add an Injuries row.":
        "/3 — дай пальцам отдых, перейди на ноги/кардио/мобильность, добавь строку в «Травмы».",
    "Sleep/stress are down — swap the next limit day for a technique day, prioritise sleep.":
        "Сон/стресс просели — замени следующий лимитный день на технический, приоритет — сон.",
    "Recovery: sleep and stress look fine.": "Восстановление: сон и стресс в норме.",
    "Log pain, sleep and stress to track recovery.":
        "Записывай боль, сон и стресс, чтобы отслеживать восстановление.",
    "Completion: ": "Выполнение: ",
    "Week under-done — don't cram it back; add volume gradually (+10-15%).":
        "Неделя недоделана — не навёрстывай рывком; добавляй объём постепенно (+10–15%).",
    "Volume on plan.": "Объём по плану.",
    "Completion shows once sessions + plan exist.":
        "Выполнение появится, когда будут сессии и план.",
    "Overall last-week status: ": "Общий статус прошлой недели: ",
    "Status appears after your first check-in.": "Статус появится после первой сверки.",

    # ---- Recovery sheet ------------------------------------------------------
    "Recovery & health traffic light": "Восстановление и светофор здоровья",
    "Zone": "Зона", "What it means": "Что это значит", "What to do": "Что делать",
    "🟢 Green": "🟢 Зелёный", "🟡 Amber": "🟡 Жёлтый", "🔴 Red": "🔴 Красный",
    "HRV at/above baseline; resting HR steady; ACWR 0.8-1.3; strength holding/rising; sleep good; fingers pain-free; losing 0.4-0.55 kg/wk.":
        "ВСР на/выше базы; пульс покоя стабилен; ACWR 0.8–1.3; сила держится/растёт; сон хороший; пальцы без боли; теряешь 0.4–0.55 кг/нед.",
    "Carry on as planned.": "Продолжай по плану.",
    "HRV a few days below baseline; ACWR 1.3-1.5; fatigue 8+/10; weight stalled or dropping fast; mild finger fatigue.":
        "ВСР несколько дней ниже базы; ACWR 1.3–1.5; усталость 8+/10; вес встал или падает быстро; лёгкая усталость пальцев.",
    "Easy/technique day instead of limit. More food and sleep. Check rate and volume.":
        "Лёгкий/технический день вместо лимита. Больше еды и сна. Проверь темп и объём.",
    "HRV chronically low + RHR rising; ACWR >1.5; strength down 2 sessions; finger pain ≥2/3; sleep/mood/libido down; losing >0.7 kg/wk.":
        "ВСР хронически низкая + пульс покоя растёт; ACWR >1.5; сила упала 2 сессии; боль в пальцах ≥2/3; сон/настроение/либидо просели; теряешь >0.7 кг/нед.",
    "Cut volume, exit the deficit. Finger pain — pause. Persistent symptoms — see a doctor.":
        "Снизь объём, выйди из дефицита. Боль в пальцах — пауза. Стойкие симптомы — к врачу.",
    "Recovery protocols": "Протоколы восстановления",
    "Sleep": "Сон",
    "7-9 h. The main lever for CNS recovery and keeping strength in a deficit.":
        "7–9 ч. Главный рычаг восстановления ЦНС и сохранения силы в дефиците.",
    "Deloads": "Разгрузки",
    "Every 3-4 weeks: volume -40-50%, intensity held (see Cycle).":
        "Каждые 3–4 недели: объём −40–50%, интенсивность держим (см. «Цикл»).",
    "Fingers/pulleys": "Пальцы/кольцевые связки",
    "Always warm up progressively. Half-crimp and open grip first. Collagen slower in a deficit — add load carefully.":
        "Всегда разминайся постепенно. Сначала полукримп и открытый хват. Коллаген в дефиците медленнее — добавляй нагрузку осторожно.",
    "Don't ramp weekly load in jumps. >50% over the 4-week average = risk.":
        "Не наращивай недельную нагрузку рывками. >50% над 4-недельным средним = риск.",
    "HRV / Body Battery": "ВСР / Body Battery",
    "Low in the morning → easy/technique day instead of limit or max hangs.":
        "Низко утром → лёгкий/технический день вместо лимита или макс. висов.",
    "Cardio as recovery": "Кардио как восстановление",
    "Easy Zone 2 aids recovery and burns fat with little interference.":
        "Лёгкая Зона 2 помогает восстановлению и жжёт жир почти без интерференции.",

    # ---- Glossary sheet ------------------------------------------------------
    "Glossary — plain language": "Глоссарий — простыми словами",
    "Term": "Термин", "What it is": "Что это",
    "Subjective session hardness 1-10 (10 = max). You enter it after training.":
        "Субъективная сложность сессии 1–10 (10 = максимум). Ставишь после тренировки.",
    "sRPE load": "sRPE-нагрузка",
    "Duration × RPE. A simple measure of what a session 'cost'.":
        "Длительность × RPE. Простая мера того, во что «обошлась» сессия.",
    "Weekly load": "Недельная нагрузка",
    "Sum of session sRPE for the week. Total stress.":
        "Сумма sRPE сессий за неделю. Суммарный стресс.",
    "Acute:chronic load = this week ÷ 4-week average. 0.8-1.3 = ok, >1.5 = a spike and injury risk.":
        "Острая:хроническая нагрузка = эта неделя ÷ среднее за 4 недели. 0.8–1.3 = норм, >1.5 = скачок и риск травмы.",
    "Relative strength (%BW)": "Относительная сила (%ВТ)",
    "Strength relative to bodyweight. Losing weight raises it without new training.":
        "Сила относительно веса тела. Снижение веса повышает её без новых тренировок.",
    "Finger norm (V-target)": "Норма пальцев (цель V)",
    "Population guide (Lattice): the %BW max hang on a 20 mm edge that tends to match a grade. Wide spread.":
        "Популяционный ориентир (Lattice): %ВТ макс. виса на зацепе 20 мм, обычно соответствующий категории. Большой разброс.",
    "~7-10 s hang on an edge with added load, hard but clean (Eva Lopez method). Base finger strength.":
        "Вис ~7–10 с на зацепе с доп. весом, тяжело но чисто (метод Эвы Лопес). Базовая сила пальцев.",
    "Pulling hard into a fixed edge (overcoming isometric). Safer than heavy hangs, transfers to the wall.":
        "Сильная тяга в неподвижную зацепу (преодолевающий изометрический). Безопаснее тяжёлых висов, переносится на стенд.",
    "Very hard boulders at your ceiling, 3-5 moves, long rests. Strength and power.":
        "Очень трудные боулдеры на пределе, 3–5 перехватов, длинный отдых. Сила и мощность.",
    "Holding high output 1-5 min under pump. For comp format; introduced late, fades fast.":
        "Удержание высокой отдачи 1–5 мин под забитостью. Для формата соревнований; вводится поздно, уходит быстро.",
    "4x4": "4×4",
    "4 boulders back-to-back = a round; rest 4 min; 4 rounds.":
        "4 боулдера подряд = раунд; отдых 4 мин; 4 раунда.",
    "A lighter week every 3-4 weeks for recovery.":
        "Более лёгкая неделя каждые 3–4 недели для восстановления.",
    "Cutting volume before the goal so you arrive fresh.":
        "Снижение объёма перед целью, чтобы подойти свежим.",
    "Zone 2": "Зона 2",
    "Easy cardio where you can still talk.": "Лёгкое кардио, при котором ещё можешь говорить.",
    "Heart-rate variability (wearable, overnight). Falling = fatigue.":
        "Вариабельность сердечного ритма (гаджет, за ночь). Падает = усталость.",
    "RED-S": "RED-S",
    "Energy deficiency in sport from prolonged under-fuelling at high load. Hits hormones, sleep, bone, immunity.":
        "Дефицит энергии в спорте от длительного недоедания при высокой нагрузке. Бьёт по гормонам, сну, костям, иммунитету.",
    "Pain 0-3": "Боль 0–3",
    "An in-session signal, not a diagnosis: 0 none, 1 mild, 2 noticeable (stop signal), 3 sharp/'pop' (stop immediately). A 2+ is a prompt to consider an Injuries entry, not an automatic one.":
        "Сигнал во время сессии, не диагноз: 0 нет, 1 лёгкая, 2 заметная (сигнал стоп), 3 резкая/«щелчок» (немедленно стоп). 2+ — повод подумать о записи в «Травмы», не автоматически.",
    "Injury vs bump": "Травма vs ушиб",
    "Log an *injury* when a structure (finger/tendon/joint) hurts — especially with no clear cause, under load, or lasting past the next session. A *bump* (a knock, skin/flapper, one-off soreness with an obvious cause) is not an injury; a Journal note is enough.":
        "Записывай *травму*, когда болит структура (палец/сухожилие/сустав) — особенно без ясной причины, под нагрузкой или дольше следующей сессии. *Ушиб* (удар, кожа/надрыв, разовая крепатура с очевидной причиной) — не травма; хватит заметки в «Дневнике».",
    "A2 pulley": "Кольцевая связка A2",
    "A finger pulley near the bone; the most common climber injury.":
        "Пальцевая кольцевая связка у кости; самая частая травма скалолаза.",
    "Half-crimp / open": "Полукримп / открытый",
    "Grip positions; open-hand is gentler on the pulleys.":
        "Положения хвата; открытый мягче для кольцевых связок.",

    # ---- How to use sheet ----------------------------------------------------
    "How to use — this file is your plan, tracker and advisor":
        "Как пользоваться — этот файл: план, трекер и советчик",
    "Two actions, that's all": "Два действия, и всё",
    "1) After every session add ONE row in Journal. 2) Once a week fill 5-6 numbers in Week (weight + recovery). Everything else — load, ACWR, finger strength, weight pace, status — computes itself.":
        "1) После каждой сессии добавь ОДНУ строку в «Дневник». 2) Раз в неделю заполни 5–6 чисел в «Неделя» (вес + восстановление). Всё остальное — нагрузка, ACWR, сила пальцев, темп веса, статус — считается само.",
    "All weights in this workbook are in {unit} — enter bodyweight and added load in {unit}. Percent-of-bodyweight numbers are unit-free.":
        "Все веса в этой книге в {unit} — вводи вес тела и доп. вес в {unit}. Числа в процентах от веса тела не зависят от единиц.",
    "Journal (after a session)": "Дневник (после сессии)",
    "Date (as a real date), type from the dropdown, minutes, RPE 1-10. When relevant: hang added load, best grade, pain 0-3, a note. Week number and load compute. Don't edit the grey start-date cell (B2).":
        "Дата (настоящей датой), тип из списка, минуты, RPE 1–10. Где уместно: доп. вес виса, лучшая категория, боль 0–3, заметка. Номер недели и нагрузка считаются. Не меняй серую ячейку даты старта (B2).",
    "Week (weekly check-in)": "Неделя (еженедельная сверка)",
    "Weight, sleep hours, fatigue, sleep quality, stress — plus HRV/resting HR if you track them. Auto columns: pace vs the planned curve, fingers %BW, gap to your grade norm, load, ACWR, completion vs plan, and a traffic-light status.":
        "Вес, часы сна, усталость, качество сна, стресс — плюс ВСР/пульс покоя, если отслеживаешь. Авто-столбцы: темп vs плановая кривая, пальцы %ВТ, разрыв до нормы категории, нагрузка, ACWR, выполнение vs план и статус-светофор.",
    "Dashboard": "Дашборд",
    "Your landing page: headline numbers from the latest week plus an advisor that tells you what to do (adjust the deficit, back off load, swap a limit day, rest a finger).":
        "Твоя стартовая страница: ключевые числа за последнюю неделю плюс советчик, который говорит что делать (поправить дефицит, снизить нагрузку, заменить лимитный день, дать пальцу отдых).",
    "Cycle & Schedules": "Цикл и Расписания",
    "Cycle is the macro plan (phases, dates, deloads, planned weight). The Schedule sheets expand each phase day by day. Rearranging days is fine — keep quality days spaced and fingers ≥48h apart.":
        "«Цикл» — макроплан (фазы, даты, разгрузки, плановый вес). Листы «Расписание» расписывают каждую фазу по дням. Переставлять дни можно — держи качественные дни разнесёнными, а пальцы ≥48 ч друг от друга.",
    "Injuries": "Травмы",
    "Log what affects training: structural pain (finger/tendon/joint), pain under load, anything lasting past the next session. Bumps, skin and one-off soreness with an obvious cause don't belong here.":
        "Записывай то, что влияет на тренировки: структурную боль (палец/сухожилие/сустав), боль под нагрузкой, всё, что тянется дольше следующей сессии. Ушибы, кожа и разовая крепатура с очевидной причиной сюда не входят.",
    "How the advisor thinks": "Как думает советчик",
    "sRPE load = minutes × RPE → weekly sum → ACWR (this week ÷ 4-week average; 0.8-1.3 ok, >1.5 risk). Plus weight pace vs plan, finger strength vs the population norm for your target grade, and pain. Finger pain overrides everything.":
        "sRPE-нагрузка = минуты × RPE → сумма за неделю → ACWR (эта неделя ÷ среднее за 4 недели; 0.8–1.3 норм, >1.5 риск). Плюс темп веса vs план, сила пальцев vs популяционная норма для целевой категории, и боль. Боль в пальцах перебивает всё.",
    "Honesty": "Честность",
    "Norms are population guides with wide spread; this tool is not medical or coaching advice (see DISCLAIMER in the repo). When in doubt — less load, more sleep.":
        "Нормы — популяционные ориентиры с большим разбросом; этот инструмент не медицинский и не тренерский совет (см. DISCLAIMER в репозитории). Сомневаешься — меньше нагрузки, больше сна.",

    # ---- Mobility sheet ------------------------------------------------------
    "Mobility — protocol, measurements, periodization":
        "Мобильность — протокол, замеры, периодизация",
    "Protocol (climbing-specific: active mobility, not passive splits)":
        "Протокол (специфично для скалолазания: активная мобильность, не пассивные шпагаты)",
    "When": "Когда", "Frequency": "Частота", "Why": "Зачем",
    "Dynamic warm-up": "Динамическая разминка", "Every session": "Каждую сессию",
    "Leg/hip swings, 90-90, glute bridge, band pull-aparts & dislocates, cat-cow, wrists (8-10')":
        "Махи ног/бёдер, 90-90, ягодичный мост, разведения/выкруты с резиной, кошка-корова, запястья (8–10 мин)",
    "Prep tissue. No static stretch pre-session — it cuts force.":
        "Подготовка тканей. Без статической растяжки до сессии — она режет силу.",
    "Targeted mobility": "Целевая мобильность", "2x/week": "2×/нед",
    "Hips (90-90, deep squat hold, frog, couch), shoulders/T-spine (hangs, rotations), ankles (knee-to-wall). Active holds (20-25')":
        "Бёдра (90-90, глубокий сед, лягушка, couch), плечи/грудной отдел (висы, ротации), голеностопы (колено-к-стене). Активные удержания (20–25 мин)",
    "Usable range for climbing positions": "Рабочая амплитуда для позиций в лазании",
    "PNF / contract-relax": "ПНФ / сокращение-расслабление", "1x/week": "1×/нед",
    "Enter stretch → 5-6s ~70% contraction → relax deeper, 3-4 cycles. Stubborn areas (hips)":
        "Вошёл в растяжку → 5–6 с ~70% сокращение → расслабься глубже, 3–4 цикла. Упрямые зоны (бёдра)",
    "Best range gains for strength-based athletes":
        "Лучший прирост амплитуды для силовых атлетов",
    "Measurements (every 2-4 weeks — range changes slowly)":
        "Замеры (каждые 2–4 недели — амплитуда меняется медленно)",
    "Deep squat hold, s": "Глубокий сед, с", "Sit-and-reach, cm": "Наклон сидя, см",
    "Shoulder wall 0/1/2": "Плечо у стены 0/1/2", "Dorsi L, cm": "Тыл. сгиб Л, см",
    "Dorsi R, cm": "Тыл. сгиб П, см", "Asym |L−R|": "Асимм. |Л−П|", "Tightness 0-3": "Зажатость 0–3",
    "Yellow = your input. Asymmetry auto-computes (>2 cm highlighted — worth balancing). Shoulder wall: 0 = can't reach overhead without arching, 1 = partial, 2 = easy. Same conditions each time.":
        "Жёлтое = твой ввод. Асимметрия считается сама (>2 см подсвечивается — стоит выровнять). Плечо у стены: 0 = не дотянуться над головой без прогиба, 1 = частично, 2 = легко. Одинаковые условия каждый раз.",
    "Periodization (in sync with the main cycle)": "Периодизация (в такт с основным циклом)",
    "Base / contact (deficit)": "База / контактная сила (дефицит)",
    "Most mobility volume — best window to build range. 2 targeted + 1 PNF per week.":
        "Больше всего объёма мобильности — лучшее окно для роста амплитуды. 2 целевые + 1 ПНФ в неделю.",
    "Bridge / peak": "Переход / пик",
    "Reduce deep stretching and PNF (they add fatigue before the peak). Dynamic + light maintenance only.":
        "Меньше глубокой растяжки и ПНФ (добавляют усталость перед пиком). Только динамика + лёгкое поддержание.",
    "Dynamic warm-up and light mobilization only. Nothing new or intense.":
        "Только динамическая разминка и лёгкая мобилизация. Ничего нового или интенсивного.",

    # ---- Nutrition sheet -----------------------------------------------------
    "Nutrition — targets from current weight + principles":
        "Питание — цели от текущего веса + принципы",
    "Targets (computed from your latest weight)": "Цели (вычислены от последнего веса)",
    "Weight used for calc, {unit}": "Вес для расчёта, {unit}",
    "Protein, g/day — minimum": "Белок, г/день — минимум",
    "Protein, g/day — target": "Белок, г/день — цель",
    "Protein per meal (x4-5), g": "Белок за приём (×4–5), г",
    "Carbs on training days, g (~3-4 g/kg)": "Углеводы в тренир. дни, г (~3–4 г/кг)",
    "Fat minimum, g (~0.8 g/kg)": "Жиры минимум, г (~0.8 г/кг)",
    "Principles": "Принципы",
    "Rate of loss": "Темп снижения",
    "0.4-0.55 kg/wk ≈ 0.9-1.2 lb/wk (0.5-0.7% BW). Slow = keeps strength.":
        "0.4–0.55 кг/нед ≈ 0.9–1.2 фунт/нед (0.5–0.7% ВТ). Медленно = сохраняет силу.",
    "Deficit": "Дефицит",
    "~300-500 kcal/day. No crash dieting.": "~300–500 ккал/день. Без жёстких диет.",
    "Protein": "Белок",
    "The key nutrient against strength loss in a deficit — keep near the upper target.":
        "Ключевой нутриент против потери силы в дефиците — держи у верхней цели.",
    "Carbs": "Углеводы",
    "More around quality sessions (fingers, limit), less on Zone-2/rest days.":
        "Больше вокруг качественных сессий (пальцы, лимит), меньше в дни Зоны 2/отдыха.",
    "Collagen + vitamin C": "Коллаген + витамин C",
    "15 g gelatin/collagen + vit C, 30-60 min before finger loading.":
        "15 г желатина/коллагена + вит. C, за 30–60 мин до нагрузки на пальцы.",
    "Exit the deficit": "Выход из дефицита",
    "Return to maintenance 4-6 weeks before the goal; carb-load at the very end.":
        "Вернись на поддержание за 4–6 недель до цели; углеводная загрузка в самом конце.",
    "Supplements": "Добавки",
    "Creatine 3-5 g/day, caffeine 3-6 mg/kg pre-comp, vitamin D.":
        "Креатин 3–5 г/день, кофеин 3–6 мг/кг перед соревнованием, витамин D.",
    "Important": "Важно",
    "This is a framework. Exact calories/macros — see a sports dietitian.":
        "Это рамка. Точные калории/макросы — к спортивному диетологу.",
}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def translator(lang):
    """Return a `t(source, **kw)` function for the given language.

    Unknown sources fall back to English, so missing translations never break
    generation. Placeholders are filled via str.format after the lookup.
    """
    if isinstance(lang, str):
        lang = Language(lang)
    is_ru = lang == Language.RU

    def t(source: str, **kw) -> str:
        out = _RU.get(source, source) if is_ru else source
        return out.format(**kw) if kw else out

    return t


def tr(lang, source: str, **kw) -> str:
    """One-shot translate (convenience for call sites without a bound translator)."""
    return translator(lang)(source, **kw)
