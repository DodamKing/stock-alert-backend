# 주식 전고점 대비 하락률 조회 서비스

주식 이름을 검색하여 전고점 대비 현재 하락률을 확인하고 매수 시점을 판단할 수 있는 서비스입니다.

## 주요 기능

- 주식 이름으로 종목 검색 (국내, 미국 주식 및 ETF 지원)
- 전고점 대비 현재 하락률 계산 및 시각화
- 하락 정도에 따른 분석 제공
- 다크 모드 지원
- 사용자 설정 저장 기능
- 알림 설정 기능

## 기술 스택

- **백엔드**: Express.js + FastAPI
  - Express.js: 클라이언트 API 제공 및 데이터 가공
  - FastAPI: FinanceDataReader를 통한 주식 데이터 조회
- **프론트엔드**: Vue.js + Vite
  - 반응형 디자인
  - 시각적 애니메이션

## 설치 및 실행 방법

### 필수 요구사항

- Node.js 14 이상
- Python 3.8 이상
- npm 또는 yarn

### 백엔드 설정

```bash
# 필요한 패키지 설치
cd server
npm install

# Python 가상환경 설정
cd ../api
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 필요한 Python 패키지 설치
pip install fastapi uvicorn pandas finance-datareader
```

### 프론트엔드 설정

```bash
# 프론트엔드 의존성 설치
cd ../frontend
npm install
```

### 실행 방법

1. 백엔드 서버 실행 (Express와 FastAPI를 한번에 실행)

```bash
cd ../server
npm run dev
```

2. 프론트엔드 개발 서버 실행 (새 터미널에서)

```bash
cd ../frontend
npm run dev
```

3. 브라우저에서 표시되는 URL로 접속 (기본: http://localhost:5173)

## 사용 방법

1. 검색창에 주식 이름 입력 (예: 삼성전자, Apple, QQQ 등)
2. 시장 필터를 사용하여 검색 범위 조정 가능
3. 검색 결과에서 원하는 종목 선택
4. 전고점 대비 하락률 및 분석 내용 확인

## 참고사항

- 다크 모드는 우측 상단의 토글 버튼으로 전환할 수 있습니다.
- 시장 필터 설정은 로컬 스토리지에 저장됩니다.
- 특정 종목에 대한 알림 설정도 가능합니다.