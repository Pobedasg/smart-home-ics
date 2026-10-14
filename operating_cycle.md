---
config:
  theme: base
  layout: elk
  flowchart:
    curve: step
  themeVariables:
    fontSize: '18px'
    fontFamily: 'Arial'
    primaryColor: '#E8F0FE'
    primaryBorderColor: '#1A56DB'
    primaryTextColor: '#111827'
    lineColor: '#374151'
---
flowchart TB
  A["Завантаження:<br/>initial_state.json, facts.json, rules.json"] --> WM["Робоча пам'ять (факти)"]
  WM --> M["1. Зіставлення:<br/>знайти правила, умови яких виконуються"]
  M --> Q{"Конфліктний набір<br/>порожній?"}
  Q -->|так| E["Кінець: вивести стан пристроїв<br/>і пояснення"]
  Q -->|ні| S["2. Вибір:<br/>найбільший salience,<br/>при рівності – перше у файлі"]
  S --> F["3. Виконання:<br/>змінити факти, запам'ятати,<br/>що правило вже спрацювало"]
  F -->|новий цикл| WM

  classDef io fill:#E0E7FF,stroke:#4338CA,color:#111827
  classDef step fill:#DCFCE7,stroke:#15803D,color:#111827
  classDef end1 fill:#FCE7F3,stroke:#BE185D,color:#111827
  class A,WM io
  class M,S,F step
  class E end1