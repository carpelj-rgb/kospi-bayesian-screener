# KOSPI Bayesian Factor Screener

한국 주식(KOSPI) 대상 **PBR · 수급 턴어라운드 · EPS 상향** 팩터를 계산하고, 베이지안 **사후 상승 확률(π)** 로 랭킹하는 웹 스크리너입니다.

## 구조

```
backend/     FastAPI — pykrx/yfinance 데이터, 팩터·베이지안 계산, REST API
frontend/    Next.js — 스크리너 대시보드 테이블
```

## 빠른 시작 (로컬)

### 1. 백엔드

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API 문서: http://localhost:8000/docs
- 스크리너: http://localhost:8000/api/v1/screener?market=KOSPI&limit=30

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

- 대시보드: http://localhost:3000

`.env.local` (선택):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Docker (선택)

```bash
docker compose up --build
```

## 배포 (Render + Vercel)

### Render (백엔드)

- `render.yaml` — Docker, 서비스명 `kospi-bayesian-screener`
- URL: `https://kospi-bayesian-screener.onrender.com`
- 선택 env: `KRX_ID`, `KRX_PW`, `CORS_ORIGINS`, `FRONTEND_URL`

### Vercel (프론트엔드)

Next.js 앱은 **`frontend/`** 폴더에 있습니다. Vercel 프로젝트에서 아래를 설정하세요.

1. **Settings → General → Root Directory** → `frontend` 로 지정 후 Save
2. **Settings → Environment Variables**
   - `BACKEND_URL` = `https://kospi-bayesian-screener.onrender.com` (Production)
   - `NEXT_PUBLIC_API_URL` 은 **설정하지 않음** (브라우저 CORS 회피용 same-origin 프록시 사용)
3. Redeploy

루트에 `package.json` / `vercel.json` 도 포함되어 있어 Root Directory 없이 빌드할 때를 대비했지만, **Root Directory = `frontend` 가 가장 안정적**입니다.

## API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/health` | 헬스체크 |
| GET | `/api/v1/screener` | 스크리너 목록 (`market`, `min_prob`, `limit`) |
| GET | `/api/v1/screener/{ticker}` | 종목별 팩터 breakdown |

## 팩터 & 베이지안 (`bayesian/screener.py`)

### 핵심 4팩터 (가중 Log-Odds)

| 팩터 | 비중 | LR (true/false) |
|------|------|-----------------|
| Revision Momentum (어닝 서프라이즈/추정치 상향) | **30%** | 2.20 / 0.72 |
| ROE 턴어라운드 + 저 PBR | **25%** | 1.90 / 0.78 |
| 메이저 수급 턴어라운드 | **25%** | 2.50 / 0.70 |
| VCP 상방 돌파 | **20%** | 2.10 / 0.75 |

### 보조 High-LR 팩터 (활성 시 log-odds 가산)

| 팩터 | LR (true) | 설명 |
|------|-----------|------|
| 내부자매수 | 2.80 | 최대주주 지분↑ 또는 장내 매수 |
| 재무안정 | 2.40 | 부채비율 하위 50% + OCF 3년 연속 + |

```
log(Odds_post) = log(Odds_prior) + Σ wᵢ·log(LRᵢ) + Σ bonus·log(LR_aux)
π = exp(log_odds) / (1 + exp(log_odds))
```

### API 응답 필드 (종목별)

- `factor_tags`: 충족 팩터 태그 리스트 (예: `["Revision", "수급전환"]`)
- `posterior_up_prob_pct`: 최종 상승 확률 (%)
- `posterior_up_prob`: 0~1 확률값

## 다음 단계

- [ ] SQLite 일별 스냅샷 + 배치 갱신
- [ ] 종목 상세 페이지 (`/stock/[ticker]`)
- [ ] 팩터 weights calibration notebook
- [ ] Redis 캐시

## 주의

- pykrx/yfinance는 **장 마감 후** 데이터 반영이 지연될 수 있습니다.
- KRX API가 차단되거나 로그인이 필요한 환경에서는 `.env`에 `KRX_ID`, `KRX_PW`를 설정하세요. API 실패 시에도 **폴백 유니버스**로 스크리너는 동작하지만 PBR·수급 데이터는 중립값(0.5)으로 처리될 수 있습니다.
- EPS 데이터는 yfinance 커버리지에 따라 일부 종목에서 누락될 수 있습니다.
- 본 프로젝트는 **투자 참고용**이며 투자 손실에 대한 책임을 지지 않습니다.
