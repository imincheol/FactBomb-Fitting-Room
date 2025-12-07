# FactBomb Fitting Room (Smh-Fassion)

**"현실을 직시하는 매운맛 피팅룸"**

**FactBomb Fitting Room**은 사용자의 신체 비율을 '워너비' 모델과 냉철하게 비교 분석하는 인터랙티브 웹 애플리케이션입니다. 컴퓨터 비전(CV) 기술로 신체를 분석하고, 생성형 AI(Google Gemini)를 활용하여 유머러스하고 날카로운("팩트폭행") 피드백을 제공합니다. 또한, 사용자의 비율을 모델에 대입했을 때의 모습을 시각적으로 시뮬레이션(Warping)하여 보여줍니다.

---

## 🚀 주요 기능 (Key Features)

1.  **시각적 시뮬레이션 (Visual Simulation)**
    *   사용자의 얼굴과 신체 특징을 유지하면서, 모델의 비율(등신)에 맞춰 이미지를 변환합니다.
    *   5분할 워핑 알고리즘을 통해 자연스러운 신체 비율 조정을 수행합니다.

2.  **3가지 분석 모드 (Analysis Modes)**
    *   **Standard Mode (기본)**: 순수 컴퓨터 비전 알고리즘 기반의 비율 분석.
    *   **Mix Mode (하이브리드)**: 시각적 분석은 CV가 담당하고, 텍스트 피드백은 AI가 생성.
    *   **Full AI Mode (실험적)**: Vision AI가 이미지를 직접 보고 분석 및 코멘트 생성.

3.  **팩트폭행 리포트 (FactBomb Report)**
    *   "몇 등신인지", "다리 길이는 어떤지" 등 냉정한 수치 데이터 제공.
    *   AI 페르소나가 작성한 위트 있고 매운맛의 코멘터리.

---

## 🛠 설치 및 실행 (Setup & Run)

### 사전 요구 사항 (Prerequisites)
*   **Python 3.10+**
*   **Node.js 18+**
*   **Google Gemini API Key**: `.env` 파일에 설정 필요.

### 1. 환경 설정 (Configuration)
프로젝트 루트에 `.env` 파일을 생성하고 API 키를 입력하세요. (필요 시 `backend/.env` 확인)
```ini
GEMINI_API_KEY=your_api_key_here
```

### 2. 자동 실행 (Windows)
프로젝트 루트의 `start_app.bat` 파일을 더블 클릭하거나 터미널에서 실행하면 백엔드와 프론트엔드가 자동으로 시작되고 브라우저가 열립니다.
```powershell
.\start_app.bat
```

### 3. 수동 실행 (Manual Start)

**Backend (FastAPI)**
```bash
.\scripts\run_backend.bat
# 또는
# cd backend
# uvicorn main:app --reload
```

**Frontend (React/Vite)**
```bash
.\scripts\run_frontend.bat
# 또는
# cd frontend
# npm run dev
```

## 🧪 테스트 및 품질 관리 (Testing & Quality)

프로젝트 안정성을 위해 테스트와 린팅 도구가 설정되어 있습니다.

**단위 테스트 및 커버리지 (Unit Tests & Coverage)**
```powershell
.\scripts\run_tests.bat
```
*   실행 후 `htmlcov/index.html`을 열면 상세한 코드 커버리지를 볼 수 있습니다.

**코드 품질 검사 (Linting)**
```powershell
.\scripts\run_lint.bat
```
*   `ruff`를 사용하여 빠른 린팅과 포맷팅 검사를 수행합니다.

---

## 📂 프로젝트 구조 (Project Structure)

*   `backend/`: Python FastAPI 서버 (API, CV 로직, AI 연동).
*   `frontend/`: React 클라이언트 (UI, 인터랙션).
*   `docs/`: 상세 프로젝트 문서 (아키텍처, 배포 가이드 등).
*   `scripts/`: 테스트 및 유틸리티 스크립트.
*   `samples/`: 샘플 이미지 및 테스트 결과물 저장소.

---

## 📖 문서 (Documentation)
더 자세한 내용은 `docs/` 폴더를 참고하세요:
*   [01. 프로젝트 개요](docs/guides/01_overview.md)
*   [02. 분석 모드 상세](docs/guides/02_analysis_modes.md)
*   [03. 설정 가이드](docs/guides/03_configuration.md)
*   [04. 배포 가이드](docs/guides/04_deployment.md)

개발 관련 문서는 `docs/development/`에 있습니다.

---
Developed by **Antigravity** & **User**
