# 3. 설정 및 보안 (Configuration & Secrets)

이 문서는 애플리케이션 환경 설정, 비밀 키 관리, 그리고 로컬 프로젝트 실행 방법을 상세히 설명합니다.

## 환경 변수 (Environment Variables)
백엔드는 `backend/.env`에 위치한 `.env` 파일을 사용합니다.

**필수 변수**:
```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
```
*   **GEMINI_API_KEY**: "믹스 모드"와 "풀 AI 모드"에 필수적입니다. 이 키가 없으면 해당 모드는 실패하거나 오류를 반환합니다. Google AI Studio에서 키를 발급받으세요.

## 의존성 관리 (Dependency Management)
### 백엔드 (Python)
의존성 라이브러리는 `backend/requirements.txt`에 나열되어 있습니다.
*   **주요 라이브러리**:
    *   `fastapi`, `uvicorn`: 웹 서버.
    *   `opencv-python`, `numpy`: 이미지 처리.
    *   `mediapipe`: 정밀 신체 랜드마크 감지.
    *   `google-generativeai`: Gemini API 클라이언트.

**설치**:
```bash
pip install -r backend/requirements.txt
```

### 프론트엔드 (Node.js)
의존성 라이브러리는 `frontend/package.json`에 나열되어 있습니다.
*   **주요 라이브러리**:
    *   `react`, `react-dom`: UI 프레임워크.
    *   `vite`: 빌드 도구.

**설치**:
```bash
cd frontend
npm install
```

## 로컬에서 실행하기 (Running Locally)
개발을 위해서는 보통 두 개의 서버를 동시에 실행해야 합니다.

**1. 백엔드 시작**:
```powershell
# 프로젝트 루트에서
scripts\run_backend.bat
# 또는
cd backend
python -m uvicorn main:app --reload
```
*   주소: `http://localhost:8000`
*   Swagger 문서: `http://localhost:8000/docs`

**2. 프론트엔드 시작**:
```powershell
# 프로젝트 루트에서
scripts\run_frontend.bat
# 또는
cd frontend
npm run dev
```
*   주소: `http://localhost:5173` (기본값)
