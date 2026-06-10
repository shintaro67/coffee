# Coffee Brew Logger

ESP32 + HX711 + 温度センサの抽出データを記録・解析するプロジェクトです。現在は Streamlit プロトタイプに加えて、FastAPI + Next.js の本命構成を同一リポジトリ内に用意しています。

## Structure

- `esp32_firmware/`: ESP32 (PlatformIO) firmware
- `streamlit_app/`: 既存の Streamlit プロトタイプ
- `backend/`: FastAPI + SQLite + SQLAlchemy
- `frontend/`: Next.js + TypeScript + Tailwind

## New Stack Quick Start

### Backend

```powershell
cd c:\Users\cream\OneDrive\デスクトップ\cafe\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd c:\Users\cream\OneDrive\デスクトップ\cafe\frontend
npm install
npm run dev
```

Default connection settings:

- API base URL: `http://127.0.0.1:8000`
- WebSocket: `ws://127.0.0.1:8000/ws/telemetry`
- UDP ingest port: `5005`

## Notes

- Brew 画面にはリアルタイム折れ線グラフを置かず、数値メーターとプログレスバーのみにしています。
- History 画面だけが保存済みの `timeseries_json` を使って静的グラフを描画します。
- 既存の Streamlit プロトタイプは参照用に残しています。
- ESP32 側の UDP テレメトリ契約は `elapsed,weight,temp_kettle,temp_dripper` を想定しています。
