# 🚀 Multi-Agent Ad Generator

An end-to-end **multi-agent AI pipeline** that automatically generates high-converting video ads from scratch.

Built using **CrewAI**, this system takes you from:
> 📊 Ad research → 🧠 Insights → ✍️ Script → 🖼️ Images → 🔊 Voiceover → 🎬 Final video

---

## 🧠 Key Highlight

> ⚡ This system is **fault-tolerant** — even if external APIs fail (Apify, Google Drive, etc.), it automatically falls back to mock data and still produces a complete video.

---

## ⚙️ What It Does

### 🔹 Step 1 — Ad Research (Apify + Fallback)
- Scrapes top-performing Meta ads using Apify, targeted at the **CrowdWisdomTrading niche** (trading, financial education, stock market)
- Filters ads from the **last 30 days** and selects the best-performing ones
- Results saved to `output/data/ads_research.json`
- If Apify scraping fails (e.g. deprecated actor, rate limit) → automatically falls back to a realistic mock ad dataset so the pipeline continues uninterrupted

> ⚠️ Note: During development, some Apify actors returned "invalid or deprecated" errors. The fallback mock dataset was used in those cases and the pipeline completed successfully end-to-end.

### 🔹 Step 2 — Insight Extraction
Extracts the following using an LLM (OpenRouter):
- Pain points
- Hooks
- Marketing frameworks

### 🔹 Step 3 — Script Generation
- Generates a structured **60-second ad script**
- Uses Google Drive product data (if available), or fallback mock product data

### 🔹 Step 4 — Asset Generation
- 🖼️ **Images** → HuggingFace (diffusion models)
- 🔊 **Voiceover** → ElevenLabs

### 🔹 Step 5 — Video Rendering
- 🎬 Built with **Remotion (React + TypeScript)**
- Produces a vertical short-form video (Reels / TikTok format)
- 🔤 **Subtitles included** — auto-generated and overlaid on the video (basic sync implemented; word-level timestamp precision is a known improvement area)

---

## 🏗️ Architecture

```
Agents:
  Researcher    → Fetch ads
  Extractor     → Generate insights
  Script Writer → Create ad copy
  Video Creator → Generate assets

Pipeline:
  Research → Insights → Script → Assets → Video
```

---

## 🔥 Why This Project Stands Out

- ✅ Multi-agent orchestration (CrewAI)
- ✅ Fully automated pipeline (text → video)
- ✅ Fault-tolerant design (handles API failures gracefully)
- ✅ Real-world AI tools (LLMs, TTS, diffusion models)
- ✅ Production-style logging and retries
- ✅ Cross-stack system (Python + React + Node)

---

## ⚠️ Known Limitations

- Apify scraping may fail (fallback handles it)
- HuggingFace free tier may hit rate limits
- Remotion rendering may fail on low-memory systems

> 👉 None of these break the pipeline — it still completes end-to-end.

---

## 📁 Project Structure

```
multi-agent-ad-generator/
│
├── agents/               # CrewAI agents
├── tools/                # Custom tools (Apify, HF, ElevenLabs, GDrive)
├── flows/                # Pipeline orchestration
├── config/               # Environment + credentials
├── utils/                # Logger + LLM setup
│
├── remotion_project/     # Video rendering (React + TS)
│
├── output/               # Generated assets
│   ├── images/
│   ├── audio/
│   ├── videos/
│   └── scripts/
│
├── logs/                 # Execution logs
├── main.py               # Entry point
├── requirements.txt
└── README.md
```

---

## ▶️ How to Run

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-ad-generator.git
cd multi-agent-ad-generator
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Activate — Windows:
.venv\Scripts\activate

# Activate — Mac/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:
```env
OPENROUTER_API_KEY=your_key
APIFY_API_TOKEN=your_token
HF_API_TOKEN=your_token
ELEVENLABS_API_KEY=your_key
```

### 5. Install Remotion
```bash
cd remotion_project
npm install
cd ..
```

### 6. Run the pipeline
```bash
python main.py
```

---

## 📦 Output

| Output       | Path                              |
|--------------|-----------------------------------|
| Ads research | `output/data/ads_research.json`   |
| Script       | `output/scripts/ad_script.txt`    |
| Images       | `output/images/`                  |
| Audio        | `output/audio/voiceover.mp3`      |
| Video        | `output/videos/cwt_ad.mp4`        |

---

## 🧪 Example Output

- ✅ AI-generated script
- ✅ 5 scene images
- ✅ Voiceover narration
- ✅ Subtitles overlaid on video
- ✅ Final video ad (vertical, 60s)
- ✅ Ads research saved to JSON

---

## 🛠️ Tech Stack

| Component        | Tech                  |
|------------------|-----------------------|
| Agents           | CrewAI                |
| LLM              | OpenRouter            |
| Image Generation | HuggingFace           |
| Voice            | ElevenLabs            |
| Video            | Remotion              |
| Backend          | Python                |
| Frontend         | React + TypeScript    |
| IDE / AI Coding  | Antigravity           |

---

## 🔑 Apify Notes

The pipeline uses Apify to scrape Meta ads targeting the CrowdWisdomTrading niche. During development, some Apify actors were found to be **deprecated or invalid**, which triggered the built-in fallback. The Apify API token used for this project will be submitted directly via email as required.

To find your Apify token: go to [apify.com](https://apify.com) → **Settings** → **Integrations** → copy your **Personal API token**.

---

## 📌 Engineering Insight

This project is designed as a **resilient AI system**, not a fragile demo.

Even when external services fail, the pipeline continues using fallback logic and still produces output — a key requirement for production AI systems.

---

## 🚀 Future Improvements

- Real-time ad performance tracking
- Word-level subtitle timestamp precision
- Multi-language voice generation
- Automated ad A/B testing

---

## 👨‍💻 Author

**Mohd Fahad**  
AI/ML Engineer | Generative AI | Multi-Agent Systems

---

## 🏷️ Tags

```
ai, multi-agent, crewai, generative-ai, automation, llm, remotion, python
```