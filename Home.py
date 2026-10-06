import streamlit as st
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="信州上田 CKM症候群・心血管リスク予測 (PREVENT)", layout="wide")

html_code = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>信州上田 CKM症候群・心血管リスク予測 (PREVENT)</title>
<style>
  :root {
    --indigo-deep: #1a2c42;      
    --stone-gray: #5c6266;       
    --keyaki-green: #2d6e35;     
    --sanada-red: #b32020;       
    --gold-accent: #d4af37;      
    --risk-low: #27ae60;         
    --risk-border: #f1c40f;      
    --risk-mid: #e67e22;         
    --risk-high: #c0392b;        
    --bg-color: #f4f6f8;
  }
  body { font-family: "Yu Mincho", "Hiragino Mincho ProN", "MS PMincho", serif; background-color: var(--bg-color); color: #333; margin: 0; padding: 20px; }
  .container { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); overflow: hidden; border: 1px solid #e0e4e8; }
  
  .header-area { background: linear-gradient(135deg, var(--indigo-deep), #2c425e); padding: 35px 20px 25px; text-align: center; color: white; position: relative; border-bottom: 6px solid var(--stone-gray); }
  .gate-svg { width: 120px; height: auto; margin-bottom: 15px; fill: var(--stone-gray); filter: drop-shadow(2px 2px 0px rgba(0,0,0,0.5)); }
  h2 { font-family: "HGS 行書B", "HGP行書B", "HG行書B", serif; margin: 0; font-size: 1.8em; letter-spacing: 0.05em; text-shadow: 2px 2px 4px rgba(0,0,0,0.6); line-height: 1.4; }
  .sub-title { font-size: 0.9em; margin-top: 10px; color: #cbd5e1; font-family: sans-serif; }
  .endpoint-label { display: inline-block; background: rgba(255,255,255,0.15); padding: 5px 12px; border-radius: 20px; font-size: 0.8em; margin-top: 15px; border: 1px solid rgba(255,255,255,0.3); }

  .content-body { padding: 30px; font-family: sans-serif; }
  .grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
  @media (max-width: 600px) { .grid-2col { grid-template-columns: 1fr; } }
  .form-group { margin-bottom: 15px; }
  label { display: block; font-weight: bold; margin-bottom: 6px; color: var(--indigo-deep); font-size: 0.9em; position: relative; }
  input[type="number"], select { width: 100%; padding: 10px; font-size: 16px; border: 2px solid #ccd1d9; border-radius: 6px; box-sizing: border-box; transition: all 0.2s; }
  input:focus, select:focus { border-color: var(--indigo-deep); outline: none; background: #f8faff; }

  .checkbox-group { background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
  .check-label { display: inline-flex; align-items: center; margin-right: 15px; margin-bottom: 8px; font-weight: bold; cursor: pointer; color: #475569; }
  .check-label input { transform: scale(1.2); margin-right: 8px; accent-color: var(--indigo-deep); }

  .optional-group { border-left: 4px solid var(--gold-accent); background: #fffbf0; padding: 15px; margin-bottom: 25px; border-radius: 0 6px 6px 0; }
  .optional-title { font-size: 0.85em; color: #856404; font-weight: bold; margin-bottom: 10px; }

  /* ツールチップ基本（上向き） */
  .tooltip-icon { display: inline-flex; justify-content: center; align-items: center; width: 18px; height: 18px; background: var(--stone-gray); color: white; border-radius: 50%; font-size: 12px; font-family: sans-serif; margin-left: 5px; cursor: help; vertical-align: middle; position: relative; font-weight: normal; letter-spacing: normal; text-shadow: none; line-height: 1; }
  .tooltip-text { visibility: hidden; width: 320px; background-color: var(--indigo-deep); color: #fff; text-align: left; border-radius: 6px; padding: 12px; position: absolute; z-index: 100; bottom: 130%; left: 50%; margin-left: -160px; opacity: 0; transition: opacity 0.3s; font-size: 14px; font-weight: normal; box-shadow: 0 4px 10px rgba(0,0,0,0.5); pointer-events: none; line-height: 1.5; white-space: normal; letter-spacing: normal; text-shadow: none; }
  .tooltip-text::after { content: ""; position: absolute; top: 100%; left: 50%; margin-left: -6px; border-width: 6px; border-style: solid; border-color: var(--indigo-deep) transparent transparent transparent; }
  .tooltip-icon:hover .tooltip-text { visibility: visible; opacity: 1; }
  
  /* ツールチップ下向き（見切れ防止用） */
  .tooltip-down .tooltip-text { bottom: auto; top: 130%; }
  .tooltip-down .tooltip-text::after { top: auto; bottom: 100%; border-color: transparent transparent var(--indigo-deep) transparent; }

  button.calc-btn { width: 100%; padding: 16px; background: linear-gradient(to bottom, var(--indigo-deep), #0f1926); color: white; border: none; border-radius: 6px; font-size: 1.2em; font-weight: bold; cursor: pointer; box-shadow: 0 4px 0 var(--stone-gray); margin-bottom: 20px; transition: all 0.1s; letter-spacing: 0.1em; }
  button.calc-btn:active { transform: translateY(4px); box-shadow: 0 0 0 var(--stone-gray); }

  #result-area { display: none; animation: fadeIn 0.5s ease; }
  
  .ckm-table-container { margin-bottom: 25px; overflow-x: auto; }
  .ckm-table { width: 100%; border-collapse: collapse; font-size: 0.85em; text-align: center; }
  .ckm-table th { background: var(--stone-gray); color: white; padding: 8px; border: 1px solid #fff; }
  .ckm-table td { background: #f1f5f9; padding: 10px 5px; border: 1px solid #fff; color: #475569; transition: all 0.3s; }
  .ckm-table td.active-stage { background: var(--gold-accent); color: #fff; font-weight: bold; transform: scale(1.05); box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 4px; }
  
  .risk-bar-container { position: relative; margin: 40px 0 20px; background: #e2e8f0; height: 30px; border-radius: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
  .risk-gradient { position: absolute; top: 0; left: 0; height: 100%; width: 100%; border-radius: 15px; background: linear-gradient(to right, var(--risk-low) 0%, var(--risk-low) 25%, var(--risk-border) 25%, var(--risk-border) 37.5%, var(--risk-mid) 37.5%, var(--risk-mid) 50%, var(--risk-high) 50%, var(--risk-high) 100%); opacity: 0.8; }
  .risk-labels { display: flex; justify-content: space-between; position: absolute; width: 100%; top: 35px; font-size: 0.75em; font-weight: bold; color: #64748b; }
  .risk-pin { position: absolute; top: -35px; width: 30px; height: 30px; background: #fff; border: 3px solid var(--indigo-deep); border-radius: 50%; transform: translateX(-50%); transition: left 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 10; display: flex; justify-content: center; align-items: center; }
  .risk-pin::after { content: ""; position: absolute; bottom: -10px; border-width: 5px 5px 0; border-style: solid; border-color: var(--indigo-deep) transparent transparent transparent; }
  .pin-icon { width: 16px; height: 16px; fill: var(--indigo-deep); }

  .big-result { text-align: center; margin: 20px 0; }
  .big-number { font-size: 4em; font-weight: bold; color: var(--indigo-deep); font-family: serif; line-height: 1; transition: color 0.3s; }
  .big-unit { font-size: 0.3em; color: #64748b; font-family: sans-serif; }
  .hf-result { font-weight:bold; color:var(--stone-gray); margin-top:15px; font-size: 1.15em; padding: 10px; background: #fffbf0; border-radius: 8px; border: 1px solid #e6dcc8; display: inline-block;}
  .hf-val { color: var(--sanada-red); font-size: 1.4em; font-family: sans-serif; transition: color 0.3s; }

  .sim-area { border: 2px dashed #94a3b8; border-radius: 8px; padding: 20px; background: #f8fafc; margin-top: 20px; }
  .sim-title { text-align: center; font-weight: bold; color: var(--indigo-deep); margin-bottom: 15px; font-size: 1.05em; }
  .sim-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
  .sim-btn { background: #fff; border: 2px solid #cbd5e1; color: #475569; padding: 10px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; font-size: 0.85em; transition: all 0.2s; display: flex; align-items: center; user-select: none; }
  .sim-btn input { display: none; }
  .sim-btn.active { background: var(--indigo-deep); color: white; border-color: var(--indigo-deep); box-shadow: 0 3px 6px rgba(0,0,0,0.15); }
  .sim-btn.disabled { opacity: 0.4; cursor: not-allowed; background: #e2e8f0; border-color: #cbd5e1; }
  .source-area { margin-top: 40px; padding: 15px; background: #f1f5f9; border-radius: 8px; font-size: 0.75em; color: #64748b; line-height: 1.5; }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>

<div class="container">
  <div class="header-area">
    <svg class="gate-svg" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <path d="M10,100 L40,40 L60,40 L60,100 Z" />
      <path d="M190,100 L160,40 L140,40 L140,100 Z" />
      <rect x="50" y="45" width="100" height="25" />
      <rect x="75" y="70" width="50" height="30" fill="var(--indigo-deep)" />
      <rect x="55" y="20" width="90" height="25" />
      <path d="M40,25 L100,5 L160,25 Z" />
      <path d="M45,45 L100,35 L155,45 Z" />
    </svg>
    <h2>
      CKM症候群
      <!-- tooltip-downクラスを追加して下向きに表示 -->
      <span class="tooltip-icon tooltip-down">?<span class="tooltip-text">心臓・血管（Cardiovascular）、腎臓（Kidney）、代謝（Metabolic）の頭文字をとった概念です。肥満や糖尿病、腎機能の低下が連鎖し、命に関わる心不全や心筋梗塞のリスクを加速度的に高める状態を指します。</span></span>
      <br>10年リスク予測
    </h2>
    <div class="sub-title">Powered by AHA PREVENT Equations (信州上田マッピング ver.)</div>
    <div class="endpoint-label">🎯 予測エンドポイント：心筋梗塞・脳卒中・<b>心不全</b></div>
  </div>

  <div class="content-body">
    <div id="error-msg" style="color: var(--sanada-red); font-weight: bold; text-align: center; margin-bottom: 10px;"></div>

    <div class="grid-2col">
      <div class="form-group"><label>年齢 (30-79歳)</label><input type="number" id="age" value="55"></div>
      <div class="form-group"><label>性別</label><select id="sex"><option value="1">男性</option><option value="0">女性</option></select></div>
      <div class="form-group"><label>収縮期血圧 (mmHg)</label><input type="number" id="sbp" value="135"></div>
      <div class="form-group">
        <label>eGFR (mL/min/1.73m²)
          <span class="tooltip-icon">?<span class="tooltip-text">推算糸球体濾過量。腎臓が老廃物を排泄する能力を示す指標です。心血管イベントや心不全のリスクに強く影響します。</span></span>
        </label>
        <input type="number" id="egfr" value="65">
      </div>
      <div class="form-group"><label>総コレステロール (mg/dL)</label><input type="number" id="tc" value="220"></div>
      <div class="form-group"><label>HDLコレステロール (mg/dL)</label><input type="number" id="hdl" value="45"></div>
      <div class="form-group">
        <label>BMI (kg/m²)
          <span class="tooltip-icon">?<span class="tooltip-text">Body Mass Index（体格指数）。25以上の過体重はCKM Stage 1に分類され、30以上の高度肥満は心不全単独の発症リスクを指数関数的に押し上げます。</span></span>
        </label>
        <input type="number" id="bmi" value="26">
      </div>
    </div>

    <div class="checkbox-group">
      <label class="check-label"><input type="checkbox" id="bp_med"> 降圧薬服用</label>
      <label class="check-label"><input type="checkbox" id="statin" onchange="handleStatinChange(this)"> スタチン内服</label>
      <label class="check-label"><input type="checkbox" id="dm"> 糖尿病</label>
      <label class="check-label"><input type="checkbox" id="smoke" onchange="handleSmokeChange(this)"> 喫煙者</label>
    </div>

    <div class="optional-group">
      <div class="optional-title">▼ アドオン・モジュール（入力すると予測精度が向上します）</div>
      <div class="grid-2col" style="margin-bottom:0;">
        <div class="form-group" style="margin-bottom:0;">
          <label>UACR (尿中アルブミン mg/gCr)
            <span class="tooltip-icon">?<span class="tooltip-text">腎臓の微小なダメージを早期に捉える指標です。入力するとより精度の高い「UACR Add-onモデル」に自動で切り替わります。</span></span>
          </label>
          <input type="number" id="uacr" placeholder="未入力でベースモデル">
        </div>
        <div class="form-group" style="margin-bottom:0;">
          <label>HbA1c (%)
            <span class="tooltip-icon">?<span class="tooltip-text">入力すると糖尿病関連の予測精度が向上する「HbA1c Add-onモデル」に自動で切り替わります。</span></span>
          </label>
          <input type="number" id="hba1c" placeholder="未入力でベースモデル">
        </div>
      </div>
    </div>

    <button type="button" class="calc-btn" id="calcBtn" onclick="handleCalcClick(this)">リスクとCKMステージを計算する</button>

    <div id="result-area">
      <div class="ckm-table-container">
        <table class="ckm-table">
          <tr><th>Stage 0</th><th>Stage 1</th><th>Stage 2</th><th>Stage 3</th></tr>
          <tr>
            <td id="stage0">危険因子<br>なし</td>
            <td id="stage1">過体重/肥満<br>または 境界型糖尿病</td>
            <td id="stage2">代謝性危険因子<br>または <b>CKD</b></td>
            <td id="stage3">サブクリニカルCVD<br>高リスク(20%以上)</td>
          </tr>
        </table>
      </div>

      <div class="big-result">
        <div style="font-weight:bold; color:var(--stone-gray); font-size: 1.1em;">
          10年以内の総CVD発症確率
          <span class="tooltip-icon tooltip-down" style="background:var(--indigo-deep);">?<span class="tooltip-text">今後10年の間に、心筋梗塞、脳卒中、または心不全のいずれかを初めて発症する確率です。（CVD＝心血管疾患）</span></span>
        </div>
        <div class="big-number" id="risk-val">--<span class="big-unit">%</span></div>
        <div class="hf-result">⚠ うち、心不全(HF)単独の発症確率: <span class="hf-val" id="hf-risk-val">--</span> %</div>
        <div id="model-type" style="font-size:0.8em; color:#94a3b8; margin-top:5px;"></div>
      </div>

      <div class="risk-bar-container">
        <div class="risk-gradient"></div>
        <div class="risk-labels">
          <span style="position:absolute; left:0%;">0%</span>
          <span style="position:absolute; left:25%; transform:translateX(-50%);">5%<br>(低)</span>
          <span style="position:absolute; left:37.5%; transform:translateX(-50%);">7.5%<br>(境界)</span>
          <span style="position:absolute; left:50%; transform:translateX(-50%);">20%<br>(中)</span>
          <span style="position:absolute; right:0%; color:var(--risk-high);">高リスク</span>
        </div>
        <div class="risk-pin" id="risk-pin">
          <svg class="pin-icon" viewBox="0 0 24 24"><path d="M12,2C8.13,2 5,5.13 5,9c0,5.25 7,13 7,13s7,-7.75 7,-13C19,5.13 15.87,2 12,2z M12,11.5c-1.38,0 -2.5,-1.12 -2.5,-2.5s1.12,-2.5 2.5,-2.5 2.5,1.12 2.5,2.5S13.38,11.5 12,11.5z"/></svg>
        </div>
      </div>

      <div class="sim-area">
        <div class="sim-title">▼ 介入シミュレーション（What-if）</div>
        <div class="sim-grid">
          <label class="sim-btn" id="lbl-quit"><input type="checkbox" value="quit" onchange="toggleSim(this)"> 🚭 禁煙する</label>
          <label class="sim-btn" id="lbl-weight"><input type="checkbox" value="weight" onchange="toggleSim(this)"> ⚖️ 体重管理(BMI改善)</label>
          <label class="sim-btn" id="lbl-statin"><input type="checkbox" value="statin" onchange="toggleSim(this)"> 💊 スタチン導入(LDL低下)</label>
          <label class="sim-btn" id="lbl-sglt2"><input type="checkbox" value="sglt2" onchange="toggleSim(this)"> 💧 SGLT2阻害薬</label>
          <label class="sim-btn" id="lbl-mra"><input type="checkbox" value="mra" onchange="toggleSim(this)"> 🛡️ MRA</label>
        </div>
        <div style="font-size:0.75em; color:#94a3b8; text-align:center; margin-top:10px;">
          ※一部の薬剤効果は、一般的な相対リスク低下(RRR)を用いた教育的推計です。<br>
          ※体重管理を行うと、BMIを25未満に正常化した場合の「肥満による心不全リスク」の劇的な低下が確認できます。
        </div>
      </div>
      
      <div class="source-area">
        <div style="font-weight: bold; color: #333; margin-bottom: 5px;">【参考文献】</div>
        <ul style="list-style-type: none; padding: 0; margin: 0;">
          <li style="margin-bottom: 3px; padding-left: 10px; text-indent: -10px;">・Khan SS, et al. Novel Prediction Equations for Absolute Risk Assessment of Total Cardiovascular Disease Incorporating Cardiovascular-Kidney-Metabolic Health: A Scientific Statement From the American Heart Association. Circulation. 2023;148:1982–2004.</li>
          <li style="margin-bottom: 3px; padding-left: 10px; text-indent: -10px;">・Khan SS, et al. Development and Validation of the American Heart Association Predicting Risk of Cardiovascular Disease EVENTS (PREVENT) Equations. Circulation. 2024;149:430–442.</li>
        </ul>
      </div>

    </div>
  </div>
</div>

<script>
  let baseCalcRisk = 0;
  let baseHFRisk = 0;

  document.addEventListener("DOMContentLoaded", function() {
    handleStatinChange(document.getElementById('statin'));
    handleSmokeChange(document.getElementById('smoke'));
  });

  function handleStatinChange(el) {
    let simBtn = document.getElementById('lbl-statin');
    let simInput = simBtn.querySelector('input');
    if (el.checked) {
      simInput.checked = false; simInput.disabled = true; 
      simBtn.classList.remove('active'); simBtn.classList.add('disabled');
      simBtn.title = "すでにスタチンを内服しているため選択できません";
    } else {
      simInput.disabled = false; simBtn.classList.remove('disabled'); simBtn.title = "";
    }
  }

  function handleSmokeChange(el) {
    let simBtn = document.getElementById('lbl-quit');
    let simInput = simBtn.querySelector('input');
    if (!el.checked) {
      simInput.checked = false; simInput.disabled = true; 
      simBtn.classList.remove('active'); simBtn.classList.add('disabled');
      simBtn.title = "喫煙者ではないため選択できません";
    } else {
      simInput.disabled = false; simBtn.classList.remove('disabled'); simBtn.title = "";
    }
  }

  function handleCalcClick(btn) {
    let originalText = btn.innerText;
    btn.innerText = "計算中...";
    setTimeout(() => { calcRisk(); btn.innerText = originalText; }, 150);
  }

  function calcRisk() {
    let errorDiv = document.getElementById('error-msg');
    errorDiv.innerHTML = "";
    
    try {
      let age = parseFloat(document.getElementById('age').value);
      let sex = parseInt(document.getElementById('sex').value);
      let sbp = parseFloat(document.getElementById('sbp').value);
      let egfr = parseFloat(document.getElementById('egfr').value);
      let tc = parseFloat(document.getElementById('tc').value);
      let hdl = parseFloat(document.getElementById('hdl').value);
      let bmi = parseFloat(document.getElementById('bmi').value) || 22;
      
      let bp_med = document.getElementById('bp_med').checked;
      let statin = document.getElementById('statin').checked;
      let dm = document.getElementById('dm').checked;
      let smoke = document.getElementById('smoke').checked;
      let uacrStr = document.getElementById('uacr').value;
      let hba1cStr = document.getElementById('hba1c').value;
      
      if(isNaN(age) || isNaN(sbp) || isNaN(egfr) || isNaN(tc) || isNaN(hdl)) {
        errorDiv.innerHTML = "⚠️️ 必須項目（年齢〜HDL）をすべて入力してください。";
        errorDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
        return;
      }

      let stage = 0;
      if (bmi >= 25) stage = 1; 
      if (sbp >= 130 || bp_med || tc >= 200 || statin || dm || hdl < 40 || egfr < 60 || (uacrStr && parseFloat(uacrStr) >= 30)) stage = 2;

      document.querySelectorAll('.sim-btn input').forEach(inp => {
        if(!inp.disabled) { inp.checked = false; inp.parentElement.classList.remove('active'); }
      });

      baseCalcRisk = executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr);
      baseHFRisk = executeHFPredictEquation(age, sex, sbp, bp_med, egfr, bmi, dm, smoke, uacrStr, hba1cStr);
      
      if (baseCalcRisk >= 20.0) stage = 3;

      document.querySelectorAll('.ckm-table td').forEach(td => td.classList.remove('active-stage'));
      document.getElementById('stage' + stage).classList.add('active-stage');

      let resultArea = document.getElementById('result-area');
      resultArea.style.display = 'block';
      updateRiskUI(baseCalcRisk, baseHFRisk);

      setTimeout(() => { resultArea.scrollIntoView({behavior: 'smooth', block: 'start'}); }, 100);

    } catch(e) {
      errorDiv.innerHTML = "⚠ エラーが発生しました: " + e.message;
    }
  }

  function toggleSim(checkbox) {
    if(checkbox.checked) checkbox.parentElement.classList.add('active');
    else checkbox.parentElement.classList.remove('active');
    runSimulation();
  }

  function runSimulation() {
    let age = parseFloat(document.getElementById('age').value);
    let sex = parseInt(document.getElementById('sex').value);
    let sbp = parseFloat(document.getElementById('sbp').value);
    let egfr = parseFloat(document.getElementById('egfr').value);
    let tc = parseFloat(document.getElementById('tc').value);
    let hdl = parseFloat(document.getElementById('hdl').value);
    let bmi = parseFloat(document.getElementById('bmi').value) || 22;
    
    let bp_med = document.getElementById('bp_med').checked;
    let statin = document.getElementById('statin').checked;
    let dm = document.getElementById('dm').checked;
    let smoke = document.getElementById('smoke').checked;
    let uacrStr = document.getElementById('uacr').value;
    let hba1cStr = document.getElementById('hba1c').value;

    let checkedSims = Array.from(document.querySelectorAll('.sim-btn input:checked')).map(inp => inp.value);

    // AHAモデルのスタチン相互作用項の統計アーティファクトを回避するため、変数代入ではなく相対リスク低下(RRR)でシミュレーションする
    if (checkedSims.includes('quit')) smoke = false;
    if (checkedSims.includes('weight')) { bmi = Math.min(bmi, 24.9); sbp = Math.max(110, sbp - 5); }

    let simRisk = executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr);
    let simHfRisk = executeHFPredictEquation(age, sex, sbp, bp_med, egfr, bmi, dm, smoke, uacrStr, hba1cStr);

    // スタチンのCVDリスク低下効果 (RRR 25%を乗算)
    if (checkedSims.includes('statin')) { simRisk *= 0.75; }
    if (checkedSims.includes('sglt2')) { simRisk *= 0.75; simHfRisk *= 0.75; }
    if (checkedSims.includes('mra')) { simRisk *= 0.85; simHfRisk *= 0.85; }

    updateRiskUI(simRisk, simHfRisk);
  }

  function updateRiskUI(riskVal, hfRiskVal) {
    let numDiv = document.getElementById('risk-val');
    numDiv.innerHTML = riskVal.toFixed(1) + '<span class="big-unit">%</span>';
    
    let hfDiv = document.getElementById('hf-risk-val');
    hfDiv.innerText = hfRiskVal.toFixed(1);

    let color = 'var(--indigo-deep)';
    if (riskVal < 5.0) color = 'var(--risk-low)';
    else if (riskVal < 7.5) color = 'var(--risk-border)';
    else if (riskVal < 20.0) color = 'var(--risk-mid)';
    else color = 'var(--risk-high)';
    
    numDiv.style.color = color;
    hfDiv.style.color = color;
    document.querySelector('.risk-pin').style.borderColor = color;
    document.querySelector('.pin-icon').style.fill = color;

    let pos = 0;
    if (riskVal <= 5) pos = (riskVal / 5) * 25;
    else if (riskVal <= 7.5) pos = 25 + ((riskVal - 5) / 2.5) * 12.5;
    else if (riskVal <= 20) pos = 37.5 + ((riskVal - 7.5) / 12.5) * 12.5;
    else pos = 50 + ((Math.min(riskVal, 40) - 20) / 20) * 50;
    
    document.getElementById('risk-pin').style.left = Math.min(Math.max(pos, 0), 100) + '%';
  }

  // --- PREVENT Total CVD ---
  function executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr) {
    let has_uacr = (uacrStr && parseFloat(uacrStr) > 0);
    let has_hba1c = (hba1cStr && parseFloat(hba1cStr) > 0);

    let non_hdl_term = ((tc - hdl) * 0.02586) - 3.5;
    let hdl_term = ((hdl * 0.02586) - 1.3) / 0.3;
    let age_term = (age - 55) / 10;
    let sbp_low = (Math.min(sbp, 110) - 110) / 20;
    let sbp_high = (Math.max(sbp, 110) - 130) / 20;
    let egfr_low = (Math.min(egfr, 60) - 60) / -15;
    let egfr_high = (Math.max(egfr, 60) - 90) / -15;

    let dm_val = dm ? 1 : 0;
    let smoke_val = smoke ? 1 : 0;
    let bp_med_val = bp_med ? 1 : 0;
    let statin_val = statin ? 1 : 0;

    let uacr_term = has_uacr ? Math.log(parseFloat(uacrStr)) : 0;
    let hba1c_val = has_hba1c ? parseFloat(hba1cStr) : 0;
    let hba1c_term = has_hba1c ? (hba1c_val - 5.3) : 0;

    let logOdds = 0;
    let modelText = "";

    if (has_uacr && has_hba1c) {
        modelText = "✓ 適用モデル: PREVENT Full Add-on (UACR + HbA1c)";
        if (sex === 0) {
            logOdds = -3.860385 + 0.7716794 * age_term + 0.0062109 * non_hdl_term - 0.1547756 * hdl_term
                - 0.1933123 * sbp_low + 0.3071217 * sbp_high + 0.496753 * dm_val + 0.466605 * smoke_val
                + 0.4780697 * egfr_low + 0.0529077 * egfr_high + 0.3034892 * bp_med_val - 0.1556524 * statin_val
                - 0.0667026 * bp_med_val * sbp_high + 0.1061825 * statin_val * non_hdl_term
                - 0.0742271 * age_term * non_hdl_term + 0.0288245 * age_term * hdl_term
                - 0.0875188 * age_term * sbp_high - 0.2267102 * age_term * dm_val
                - 0.0676125 * age_term * smoke_val - 0.1493231 * age_term * egfr_low
                + 0.1645922 * uacr_term + 0.1298513 * hba1c_term * dm_val + 0.1412555 * hba1c_term * (1 - dm_val) + 0.1804508; 
        } else {         
            logOdds = -3.631387 + 0.7847578 * age_term + 0.0534485 * non_hdl_term - 0.0911282 * hdl_term
                - 0.4921973 * sbp_low + 0.2972415 * sbp_high + 0.4527054 * dm_val + 0.3726641 * smoke_val
                + 0.3886854 * egfr_low + 0.0081661 * egfr_high + 0.2508052 * bp_med_val - 0.1538484 * statin_val
                - 0.0474695 * bp_med_val * sbp_high + 0.1415382 * statin_val * non_hdl_term
                - 0.0436455 * age_term * non_hdl_term + 0.0199549 * age_term * hdl_term
                - 0.1022686 * age_term * sbp_high - 0.1762507 * age_term * dm_val
                - 0.0715873 * age_term * smoke_val - 0.1428668 * age_term * egfr_low
                + 0.1772853 * uacr_term + 0.1165698 * hba1c_term * dm_val + 0.1048297 * hba1c_term * (1 - dm_val) + 0.144759;  
        }
    } else if (has_uacr) {
        modelText = "✓ 適用モデル: PREVENT Add-on Model (UACR)";
        if (sex === 0) { 
            logOdds = -3.738341 + 0.7969249 * age_term + 0.0256635 * non_hdl_term - 0.1588107 * hdl_term
                - 0.2255701 * sbp_low + 0.3396649 * sbp_high + 0.8047515 * dm_val + 0.5285338 * smoke_val
                + 0.4803511 * egfr_low + 0.0434472 * egfr_high + 0.2985207 * bp_med_val - 0.1497787 * statin_val
                - 0.0742889 * bp_med_val * sbp_high + 0.106756 * statin_val * non_hdl_term
                - 0.0778126 * age_term * non_hdl_term + 0.0306768 * age_term * hdl_term
                - 0.0907168 * age_term * sbp_high - 0.2705122 * age_term * dm_val
                - 0.0830564 * age_term * smoke_val - 0.1389249 * age_term * egfr_low + 0.1793037 * uacr_term;
        } else {         
            logOdds = -3.510705 + 0.7768655 * age_term + 0.0659949 * non_hdl_term - 0.0951111 * hdl_term
                - 0.420667 * sbp_low + 0.3120151 * sbp_high + 0.698521 * dm_val + 0.4314669 * smoke_val
                + 0.3841364 * egfr_low + 0.009384 * egfr_high + 0.2676494 * bp_med_val - 0.1390966 * statin_val
                - 0.0579315 * bp_med_val * sbp_high + 0.1383719 * statin_val * non_hdl_term
                - 0.0488332 * age_term * non_hdl_term + 0.0200406 * age_term * hdl_term
                - 0.102454 * age_term * sbp_high - 0.2236355 * age_term * dm_val
                - 0.089485 * age_term * smoke_val - 0.1321848 * age_term * egfr_low + 0.1887974 * uacr_term;
        }
    } else if (has_hba1c) {
        modelText = "✓ 適用モデル: PREVENT Add-on Model (HbA1c)";
        if (sex === 0) { 
            logOdds = -3.306162 + 0.7858178 * age_term + 0.0194438 * non_hdl_term - 0.1521964 * hdl_term
                - 0.2296681 * sbp_low + 0.3465777 * sbp_high + 0.5366241 * dm_val + 0.5411682 * smoke_val
                + 0.5931898 * egfr_low + 0.0472458 * egfr_high + 0.3158567 * bp_med_val - 0.1535174 * statin_val
                - 0.0687752 * bp_med_val * sbp_high + 0.1054746 * statin_val * non_hdl_term
                - 0.0761119 * age_term * non_hdl_term + 0.0307469 * age_term * hdl_term
                - 0.0905966 * age_term * sbp_high - 0.2241857 * age_term * dm_val
                - 0.080186 * age_term * smoke_val - 0.1667286 * age_term * egfr_low
                + 0.1338348 * hba1c_term * dm_val + 0.1622409 * hba1c_term * (1 - dm_val);
        } else {         
            logOdds = -3.040901 + 0.7699177 * age_term + 0.0605093 * non_hdl_term - 0.0888525 * hdl_term
                - 0.417713 * sbp_low + 0.3288657 * sbp_high + 0.4759471 * dm_val + 0.4385663 * smoke_val
                + 0.5334616 * egfr_low + 0.0206431 * egfr_high + 0.2917524 * bp_med_val - 0.1383313 * statin_val
                - 0.0482622 * bp_med_val * sbp_high + 0.1393796 * statin_val * non_hdl_term
                - 0.0463501 * age_term * non_hdl_term + 0.0205926 * age_term * hdl_term
                - 0.1037717 * age_term * sbp_high - 0.1737697 * age_term * dm_val
                - 0.0915839 * age_term * smoke_val - 0.1637039 * age_term * egfr_low
                + 0.13159 * hba1c_term * dm_val + 0.1295185 * hba1c_term * (1 - dm_val);
        }
    } else {
        modelText = "✓ 適用モデル: PREVENT Base Model (10年 総CVD)";
        if (sex === 0) { 
            logOdds = -3.307728 + 0.7939329 * age_term + 0.0305239 * non_hdl_term - 0.1606857 * hdl_term 
                - 0.2394003 * sbp_low + 0.360078 * sbp_high + 0.8667604 * dm_val + 0.5360739 * smoke_val 
                + 0.6045917 * egfr_low + 0.0433769 * egfr_high + 0.3151672 * bp_med_val - 0.1477655 * statin_val 
                - 0.0663612 * bp_med_val * sbp_high + 0.1197879 * statin_val * non_hdl_term 
                - 0.0819715 * age_term * non_hdl_term + 0.0306769 * age_term * hdl_term 
                - 0.0946348 * age_term * sbp_high - 0.27057 * age_term * dm_val 
                - 0.078715 * age_term * smoke_val - 0.1637806 * age_term * egfr_low;
        } else {         
            logOdds = -3.031168 + 0.7688528 * age_term + 0.0736174 * non_hdl_term - 0.0954431 * hdl_term 
                - 0.4347345 * sbp_low + 0.3362658 * sbp_high + 0.7692857 * dm_val + 0.4386871 * smoke_val 
                + 0.5378979 * egfr_low + 0.0164827 * egfr_high + 0.288879 * bp_med_val - 0.1337349 * statin_val 
                - 0.0475924 * bp_med_val * sbp_high + 0.150273 * statin_val * non_hdl_term 
                - 0.0517874 * age_term * non_hdl_term + 0.0191169 * age_term * hdl_term 
                - 0.1049477 * age_term * sbp_high - 0.2251948 * age_term * dm_val 
                - 0.0895067 * age_term * smoke_val - 0.1543702 * age_term * egfr_low;
        }
    }

    document.getElementById('model-type').innerText = modelText;
    let risk = (Math.exp(logOdds) / (1 + Math.exp(logOdds))) * 100;
    return Math.max(0.1, Math.min(risk, 99.9));
  }

  // --- PREVENT Heart Failure (心不全単独モデル) ---
  function executeHFPredictEquation(age, sex, sbp, bp_med, egfr, bmi, dm, smoke, uacrStr, hba1cStr) {
    let has_uacr = (uacrStr && parseFloat(uacrStr) > 0);
    let has_hba1c = (hba1cStr && parseFloat(hba1cStr) > 0);

    let age_term = (age - 55) / 10;
    let sbp_low = (Math.min(sbp, 110) - 110) / 20;
    let sbp_high = (Math.max(sbp, 110) - 130) / 20;
    let egfr_low = (Math.min(egfr, 60) - 60) / -15;
    let egfr_high = (Math.max(egfr, 60) - 90) / -15;
    let bmi_low = (Math.min(bmi, 30) - 25) / 5;
    let bmi_high = (Math.max(bmi, 30) - 30) / 5;

    let dm_val = dm ? 1 : 0;
    let smoke_val = smoke ? 1 : 0;
    let bp_med_val = bp_med ? 1 : 0;

    let uacr_term = has_uacr ? Math.log(parseFloat(uacrStr)) : 0;
    let hba1c_val = has_hba1c ? parseFloat(hba1cStr) : 0;
    let hba1c_term = has_hba1c ? (hba1c_val - 5.3) : 0;

    let logOdds = 0;

    if (has_uacr && has_hba1c) {
        if (sex === 0) { 
            logOdds = -4.896524 + 0.884209 * age_term - 0.421474 * sbp_low + 0.3002919 * sbp_high
                + 0.6170359 * dm_val + 0.5380269 * smoke_val - 0.0191335 * bmi_low + 0.2764302 * bmi_high
                + 0.5975847 * egfr_low + 0.0654197 * egfr_high + 0.3313614 * bp_med_val
                - 0.1002304 * bp_med_val * sbp_high - 0.0845363 * age_term * sbp_high
                - 0.2989062 * age_term * dm_val - 0.1111354 * age_term * smoke_val
                + 0.0008104 * age_term * bmi_high - 0.1666635 * age_term * egfr_low
                + 0.1948135 * uacr_term + 0.176668 * hba1c_term * dm_val + 0.1614911 * hba1c_term * (1 - dm_val) + 0.1819138; 
        } else { 
            logOdds = -4.663513 + 0.9095703 * age_term - 0.6765184 * sbp_low + 0.3111651 * sbp_high
                + 0.5535052 * dm_val + 0.4326811 * smoke_val - 0.0854286 * bmi_low + 0.3551736 * bmi_high
                + 0.5102245 * egfr_low + 0.015472 * egfr_high + 0.2570964 * bp_med_val
                - 0.0591177 * bp_med_val * sbp_high - 0.1219056 * age_term * sbp_high
                - 0.2437577 * age_term * dm_val - 0.105363 * age_term * smoke_val
                + 0.0037907 * age_term * bmi_high - 0.1660207 * age_term * egfr_low
                + 0.2164607 * uacr_term + 0.148297 * hba1c_term * dm_val + 0.1234088 * hba1c_term * (1 - dm_val) + 0.1694628; 
        }
    } else if (has_uacr) {
        if (sex === 0) { 
            logOdds = -4.841506 + 0.9145975 * age_term - 0.4441346 * sbp_low + 0.3260323 * sbp_high
                + 0.9611365 * dm_val + 0.5755787 * smoke_val + 0.0008831 * bmi_low + 0.2988964 * bmi_high
                + 0.5915291 * egfr_low + 0.0556823 * egfr_high + 0.3314097 * bp_med_val
                - 0.1078596 * bp_med_val * sbp_high - 0.0875231 * age_term * sbp_high
                - 0.356859 * age_term * dm_val - 0.1220248 * age_term * smoke_val
                - 0.0053637 * age_term * bmi_high - 0.1610389 * age_term * egfr_low + 0.2197281 * uacr_term;
        } else { 
            logOdds = -4.556907 + 0.9111795 * age_term - 0.6693649 * sbp_low + 0.3290082 * sbp_high
                + 0.8377655 * dm_val + 0.4978917 * smoke_val - 0.042749 * bmi_low + 0.3624165 * bmi_high
                + 0.5075796 * egfr_low + 0.0137716 * egfr_high + 0.2739963 * bp_med_val
                - 0.0645712 * bp_med_val * sbp_high - 0.1230039 * age_term * sbp_high
                - 0.3013297 * age_term * dm_val - 0.1410318 * age_term * smoke_val
                + 0.0021531 * age_term * bmi_high - 0.1548018 * age_term * egfr_low + 0.2306299 * uacr_term;
        }
    } else if (has_hba1c) {
        if (sex === 0) { 
            logOdds = -4.288225 + 0.8997391 * age_term - 0.4422749 * sbp_low + 0.3378691 * sbp_high
                + 0.681284 * dm_val + 0.5886005 * smoke_val - 0.0148657 * bmi_low + 0.2958374 * bmi_high
                + 0.73447 * egfr_low + 0.05926 * egfr_high + 0.3543475 * bp_med_val
                - 0.1002139 * bp_med_val * sbp_high - 0.0878765 * age_term * sbp_high
                - 0.303684 * age_term * dm_val - 0.1178943 * age_term * smoke_val
                - 0.008345 * age_term * bmi_high - 0.1912183 * age_term * egfr_low
                + 0.1856442 * hba1c_term * dm_val + 0.1833083 * hba1c_term * (1 - dm_val);
        } else { 
            logOdds = -3.961954 + 0.911787 * age_term - 0.6568071 * sbp_low + 0.3524645 * sbp_high
                + 0.5849752 * dm_val + 0.5014014 * smoke_val - 0.0512352 * bmi_low + 0.365294 * bmi_high
                + 0.6892219 * egfr_low + 0.0292377 * egfr_high + 0.3038296 * bp_med_val
                - 0.0515032 * bp_med_val * sbp_high - 0.1262343 * age_term * sbp_high
                - 0.2449514 * age_term * dm_val - 0.1392217 * age_term * smoke_val
                + 0.0009592 * age_term * bmi_high - 0.1917105 * age_term * egfr_low
                + 0.1652857 * hba1c_term * dm_val + 0.1505859 * hba1c_term * (1 - dm_val);
        }
    } else {
        if (sex === 0) { 
            logOdds = -4.310409 + 0.8998235 * age_term - 0.4559771 * sbp_low + 0.3576505 * sbp_high
                + 1.038346 * dm_val + 0.583916 * smoke_val - 0.0072294 * bmi_low + 0.2997706 * bmi_high
                + 0.7451638 * egfr_low + 0.0557087 * egfr_high + 0.3534442 * bp_med_val
                - 0.0981511 * bp_med_val * sbp_high - 0.0946663 * age_term * sbp_high
                - 0.3581041 * age_term * dm_val - 0.1159453 * age_term * smoke_val
                - 0.003878 * age_term * bmi_high - 0.1884289 * age_term * egfr_low;
        } else { 
            logOdds = -3.946391 + 0.8972642 * age_term - 0.6811466 * sbp_low + 0.3634461 * sbp_high
                + 0.923776 * dm_val + 0.5023736 * smoke_val - 0.0485841 * bmi_low + 0.3726929 * bmi_high
                + 0.6926917 * egfr_low + 0.0251827 * egfr_high + 0.2980922 * bp_med_val
                - 0.0497731 * bp_med_val * sbp_high - 0.1289201 * age_term * sbp_high
                - 0.3040924 * age_term * dm_val - 0.1401688 * age_term * smoke_val
                + 0.0068126 * age_term * bmi_high - 0.1797778 * age_term * egfr_low;
        }
    }
    return (Math.exp(logOdds) / (1 + Math.exp(logOdds))) * 100;
  }
</script>
</body>
</html>
"""

components.html(html_code, height=1800, scrolling=False)