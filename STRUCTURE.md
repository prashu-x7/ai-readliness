# Directory Structure

```
ai-readiness-assessment/
├── .env.example
├── .gitignore
├── FLOW.md
├── README.md
├── start.bat
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── config/
│       │   ├── database.py
│       │   ├── logging_config.py
│       │   └── settings.py
│       │
│       ├── core/
│       │   ├── assessment_engine.py
│       │   ├── ast_metrics.py
│       │   ├── classifier.py
│       │   ├── dependency_checker.py
│       │   ├── extra_checks.py
│       │   ├── file_reader.py
│       │   ├── import_graph.py
│       │   ├── log_store.py
│       │   ├── report_builder.py
│       │   ├── sandbox.py
│       │   ├── score_engine.py
│       │   └── static_analyzer.py
│       │
│       ├── routers/
│       │   ├── admin.py
│       │   ├── assess.py
│       │   ├── auth.py
│       │   ├── report.py
│       │   ├── system.py
│       │   └── user.py
│       │
│       ├── storage/
│       │   ├── assessment_repo.py
│       │   ├── schemas.py
│       │   └── user_repo.py
│       │
│       └── utils/
│           └── auth_utils.py
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    │
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        │
        ├── components/
        │   ├── AmbientMesh.jsx
        │   └── Navbar.jsx
        │
        ├── context/
        │   ├── AuthContext.jsx
        │   └── EngineContext.jsx
        │
        ├── pages/
        │   ├── SplashPage.jsx
        │   ├── LoginPage.jsx
        │   ├── SignupPage.jsx
        │   ├── Dashboard.jsx
        │   ├── UploadPage.jsx
        │   ├── ReportPage.jsx
        │   ├── AdminPage.jsx
        │   ├── ProfilePage.jsx
        │   └── SettingsPage.jsx
        │
        ├── services/
        │   └── apiClient.js
        │
        └── utils/
            ├── sound.js
            └── validators.js
```
