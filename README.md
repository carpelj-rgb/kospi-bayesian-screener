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
- 선택 env: `CORS_ORIGINS`, `FRONTEND_URL` (`PYKRX_ENABLED=false` 로 pykrx 비활성화 가능)

### Vercel (프론트엔드)

Next.js 앱은 **`frontend/`** 폴더에 있습니다.

#### 필수: Root Directory 설정

Vercel 대시보드에서 **반드시** Root Directory를 `frontend`로 지정하세요.

1. [Vercel Dashboard](https://vercel.com) → 프로젝트 선택
2. **Settings → General → Root Directory** → **Edit**
3. `frontend` 입력 → **Save**
4. **Deployments** → 최신 `main` 커밋으로 **Redeploy** (이전 커밋 `3cd4799` 등 재배포 X)

Root Directory = `frontend` 이면 `frontend/package.json`의 Next.js가 정상 감지됩니다.

#### 환경 변수

- `BACKEND_URL` = `https://kospi-bayesian-screener.onrender.com` (Production)
- `NEXT_PUBLIC_API_URL` 은 **설정하지 않음** (same-origin 프록시 사용)

#### Fallback (Root Directory를 `.` 로 둘 때)

루트 `package.json` / `vercel.json` 이 `frontend/` 빌드를 대신 실행하지만, **Root Directory = `frontend` 가 가장 안정적**입니다.

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
- pykrx는 **별도 KRX 회원 로그인 없이** 공개 API로 시도하며, 실패 시 fallback 유니버스 + yfinance로 자동 전환됩니다. API 응답의 `data_source: "limited"` 로 제한 모드를 확인할 수 있습니다.
- EPS 데이터는 yfinance 커버리지에 따라 일부 종목에서 누락될 수 있습니다.
- 본 프로젝트는 **투자 참고용**이며 투자 손실에 대한 책임을 지지 않습니다.
