import streamlit as st

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
  /* --- 新テーマ：深藍と石垣グレー --- */
  :root {
    --indigo-deep: #1a2c42;      /* 深藍（ヘッダー等） */
    --stone-gray: #5c6266;       /* 石垣グレー */
    --keyaki-green: #2d6e35;     /* けやきグリーン（低リスク・安全） */
    --sanada-red: #b32020;       /* 真田レッド（高リスク・警告） */
    --gold-accent: #d4af37;      /* ゴールドアクセント */
    
    /* リスクバー用カラー */
    --risk-low: #27ae60;         /* < 5% */
    --risk-border: #f1c40f;      /* 5 - 7.5% */
    --risk-mid: #e67e22;         /* 7.5 - 20% */
    --risk-high: #c0392b;        /* >= 20% */
    
    --bg-color: #f4f6f8;
  }

  body { 
    font-family: "Yu Mincho", "Hiragino Mincho ProN", "MS PMincho", serif; 
    background-color: var(--bg-color); 
    color: #333; margin: 0; padding: 20px;
  }

  .container { 
    max-width: 800px; margin: 0 auto; background: #fff; 
    border-radius: 12px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); 
    overflow: hidden; border: 1px solid #e0e4e8; 
  }
  
  /* --- ヘッダー --- */
  .header-area {
    background: linear-gradient(135deg, var(--indigo-deep), #2c425e);
    padding: 35px 20px 25px; text-align: center; color: white; position: relative;
    border-bottom: 6px solid var(--stone-gray);
  }

  .gate-svg { width: 120px; height: auto; margin-bottom: 15px; fill: var(--stone-gray); filter: drop-shadow(2px 2px 0px rgba(0,0,0,0.5)); }
  
  h2 { font-family: "HGS 行書B", "HGP行書B", "HG行書B", serif; margin: 0; font-size: 1.8em; letter-spacing: 0.05em; text-shadow: 2px 2px 4px rgba(0,0,0,0.6); }
  .sub-title { font-size: 0.9em; margin-top: 8px; color: #cbd5e1; font-family: sans-serif; }
  .endpoint-label { display: inline-block; background: rgba(255,255,255,0.15); padding: 5px 12px; border-radius: 20px; font-size: 0.8em; margin-top: 15px; border: 1px solid rgba(255,255,255,0.3); }

  /* --- フォームレイアウト --- */
  .content-body { padding: 30px; font-family: sans-serif; }
  
  .grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
  @media (max-width: 600px) { .grid-2col { grid-template-columns: 1fr; } }
  
  .form-group { margin-bottom: 15px; }
  label { display: block; font-weight: bold; margin-bottom: 6px; color: var(--indigo-deep); font-size: 0.9em; }
  input[type="number"], select { 
    width: 100%; padding: 10px; font-size: 16px; 
    border: 2px solid #ccd1d9; border-radius: 6px; box-sizing: border-box;
    transition: all 0.2s;
  }
  input:focus, select:focus { border-color: var(--indigo-deep); outline: none; background: #f8faff; }

  .checkbox-group { background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
  .check-label { display: inline-flex; align-items: center; margin-right: 15px; margin-bottom: 8px; font-weight: bold; cursor: pointer; color: #475569; }
  .check-label input { transform: scale(1.2); margin-right: 8px; accent-color: var(--indigo-deep); }

  .optional-group { border-left: 4px solid var(--gold-accent); background: #fffbf0; padding: 15px; margin-bottom: 25px; border-radius: 0 6px 6px 0; }
  .optional-title { font-size: 0.85em; color: #856404; font-weight: bold; margin-bottom: 10px; }

  /* --- ボタン --- */
  button.calc-btn { 
    width: 100%; padding: 16px; 
    background: linear-gradient(to bottom, var(--indigo-deep), #0f1926);
    color: white; border: none; border-radius: 6px; 
    font-size: 1.2em; font-weight: bold; cursor: pointer; 
    box-shadow: 0 4px 0 var(--stone-gray); margin-bottom: 20px;
    transition: all 0.1s; letter-spacing: 0.1em;
  }
  button.calc-btn:active { transform: translateY(4px); box-shadow: 0 0 0 var(--stone-gray); }

  /* --- 結果表示 --- */
  #result-area { display: none; animation: fadeIn 0.5s ease; }
  
  /* CKM表 */
  .ckm-table-container { margin-bottom: 25px; overflow-x: auto; }
  .ckm-table { width: 100%; border-collapse: collapse; font-size: 0.85em; text-align: center; }
  .ckm-table th { background: var(--stone-gray); color: white; padding: 8px; border: 1px solid #fff; }
  .ckm-table td { background: #f1f5f9; padding: 10px 5px; border: 1px solid #fff; color: #475569; transition: all 0.3s; }
  .ckm-table td.active-stage { background: var(--gold-accent); color: #fff; font-weight: bold; transform: scale(1.05); box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 4px; }
  
  /* リスクバー */
  .risk-bar-container { position: relative; margin: 40px 0 20px; background: #e2e8f0; height: 30px; border-radius: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
  .risk-gradient { position: absolute; top: 0; left: 0; height: 100%; width: 100%; border-radius: 15px;
    background: linear-gradient(to right, 
      var(--risk-low) 0%, var(--risk-low) 25%, 
      var(--risk-border) 25%, var(--risk-border) 37.5%, 
      var(--risk-mid) 37.5%, var(--risk-mid) 50%, 
      var(--risk-high) 50%, var(--risk-high) 100%);
    opacity: 0.8;
  }
  .risk-labels { display: flex; justify-content: space-between; position: absolute; width: 100%; top: 35px; font-size: 0.75em; font-weight: bold; color: #64748b; }
  
  .risk-pin { 
    position: absolute; top: -35px; width: 30px; height: 30px; 
    background: #fff; border: 3px solid var(--indigo-deep); border-radius: 50%;
    transform: translateX(-50%); transition: left 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3); z-index: 10; display: flex; justify-content: center; align-items: center;
  }
  .risk-pin::after { content: ""; position: absolute; bottom: -10px; border-width: 5px 5px 0; border-style: solid; border-color: var(--indigo-deep) transparent transparent transparent; }
  .pin-icon { width: 16px; height: 16px; fill: var(--indigo-deep); }

  .big-result { text-align: center; margin: 20px 0; }
  .big-number { font-size: 4em; font-weight: bold; color: var(--indigo-deep); font-family: serif; line-height: 1; transition: color 0.3s; }
  .big-unit { font-size: 0.3em; color: #64748b; font-family: sans-serif; }

  /* --- シミュレーション --- */
  .sim-area { border: 2px dashed #94a3b8; border-radius: 8px; padding: 20px; background: #f8fafc; margin-top: 20px; }
  .sim-title { text-align: center; font-weight: bold; color: var(--indigo-deep); margin-bottom: 15px; font-size: 1.05em; }
  .sim-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
  .sim-btn { 
    background: #fff; border: 2px solid #cbd5e1; color: #475569; 
    padding: 10px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; font-size: 0.85em;
    transition: all 0.2s; display: flex; align-items: center; user-select: none;
  }
  .sim-btn input { display: none; }
  .sim-btn.active { background: var(--indigo-deep); color: white; border-color: var(--indigo-deep); box-shadow: 0 3px 6px rgba(0,0,0,0.15); }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>

<div class="container">
  <div class="header-area">
    <!-- 上田城 東虎口櫓門をイメージしたSVGシルエット -->
    <svg class="gate-svg" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
      <!-- 石垣 -->
      <path d="M10,100 L40,40 L60,40 L60,100 Z" />
      <path d="M190,100 L160,40 L140,40 L140,100 Z" />
      <!-- 櫓門 1階部分 -->
      <rect x="50" y="45" width="100" height="25" />
      <!-- 門の開口部 -->
      <rect x="75" y="70" width="50" height="30" fill="var(--indigo-deep)" />
      <!-- 櫓門 2階壁 -->
      <rect x="55" y="20" width="90" height="25" />
      <!-- 屋根 -->
      <path d="M40,25 L100,5 L160,25 Z" />
      <path d="M45,45 L100,35 L155,45 Z" />
    </svg>
    <h2>PREVENT 10年リスク予測</h2>
    <div class="sub-title">信州上田 CKM症候群マッピング ver.</div>
    <div class="endpoint-label">🎯 予測エンドポイント：心筋梗塞・脳卒中・<b>心不全</b></div>
  </div>

  <div class="content-body">
    <div id="error-msg" style="color: var(--sanada-red); font-weight: bold; text-align: center; margin-bottom: 10px;"></div>

    <div class="grid-2col">
      <div class="form-group"><label>年齢 (30-79歳)</label><input type="number" id="age" value="55"></div>
      <div class="form-group"><label>性別</label><select id="sex"><option value="1">男性</option><option value="0">女性</option></select></div>
      <div class="form-group"><label>収縮期血圧 (mmHg)</label><input type="number" id="sbp" value="135"></div>
      <div class="form-group"><label>eGFR (mL/min/1.73m²)</label><input type="number" id="egfr" value="65"></div>
      <div class="form-group"><label>総コレステロール (mg/dL)</label><input type="number" id="tc" value="220"></div>
      <div class="form-group"><label>HDLコレステロール (mg/dL)</label><input type="number" id="hdl" value="45"></div>
      <div class="form-group"><label>BMI (kg/m²)</label><input type="number" id="bmi" value="26" placeholder="※CKMステージ判定用"></div>
    </div>

    <div class="checkbox-group">
      <label class="check-label"><input type="checkbox" id="bp_med"> 降圧薬服用</label>
      <label class="check-label"><input type="checkbox" id="statin"> スタチン内服</label>
      <label class="check-label"><input type="checkbox" id="dm"> 糖尿病</label>
      <label class="check-label"><input type="checkbox" id="smoke"> 喫煙者</label>
    </div>

    <div class="optional-group">
      <div class="optional-title">▼ アドオン・モジュール（入力すると予測精度が向上します）</div>
      <div class="grid-2col" style="margin-bottom:0;">
        <div class="form-group" style="margin-bottom:0;"><label>UACR (尿中アルブミン mg/gCr)</label><input type="number" id="uacr" placeholder="未入力でベースモデル"></div>
        <div class="form-group" style="margin-bottom:0;"><label>HbA1c (%)</label><input type="number" id="hba1c" placeholder="未入力でベースモデル"></div>
      </div>
    </div>

    <button type="button" class="calc-btn" onclick="calcRisk()">リスクとCKMステージを計算する</button>

    <div id="result-area">
      
      <!-- CKMステージ判定表 -->
      <div class="ckm-table-container">
        <table class="ckm-table">
          <tr><th>Stage 0</th><th>Stage 1</th><th>Stage 2</th><th>Stage 3</th></tr>
          <tr>
            <td id="stage0">危険因子<br>なし</td>
            <td id="stage1">過体重/肥満<br>または 境界型糖尿病</td>
            <td id="stage2">代謝性危険因子<br>または <b>CKD</b></td>
            <td id="stage3">サブクリニカルCVD<br>高リスク</td>
          </tr>
        </table>
      </div>

      <div class="big-result">
        <div style="font-weight:bold; color:var(--stone-gray);">10年以内の総CVD発症確率</div>
        <div class="big-number" id="risk-val">--<span class="big-unit">%</span></div>
        <div id="model-type" style="font-size:0.8em; color:#94a3b8; margin-top:5px;"></div>
      </div>

      <!-- 横型リスクバー -->
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
          <!-- 六文銭アイコンの代わりとなるピンマーク -->
          <svg class="pin-icon" viewBox="0 0 24 24"><path d="M12,2C8.13,2 5,5.13 5,9c0,5.25 7,13 7,13s7,-7.75 7,-13C19,5.13 15.87,2 12,2z M12,11.5c-1.38,0 -2.5,-1.12 -2.5,-2.5s1.12,-2.5 2.5,-2.5 2.5,1.12 2.5,2.5S13.38,11.5 12,11.5z"/></svg>
        </div>
      </div>

      <!-- 治療シミュレーション -->
      <div class="sim-area">
        <div class="sim-title">▼ 介入シミュレーション（What-if）</div>
        <div class="sim-grid">
          <label class="sim-btn" id="lbl-quit"><input type="checkbox" value="quit" onchange="toggleSim(this)"> 🚭 禁煙する</label>
          <label class="sim-btn" id="lbl-weight"><input type="checkbox" value="weight" onchange="toggleSim(this)"> ⚖️ 体重管理(血圧・糖代謝改善)</label>
          <label class="sim-btn" id="lbl-statin"><input type="checkbox" value="statin" onchange="toggleSim(this)"> 💊 スタチン導入(LDL低下)</label>
          <label class="sim-btn" id="lbl-sglt2"><input type="checkbox" value="sglt2" onchange="toggleSim(this)"> 💧 SGLT2阻害薬</label>
          <label class="sim-btn" id="lbl-mra"><input type="checkbox" value="mra" onchange="toggleSim(this)"> 🛡️ MRA</label>
        </div>
        <div style="font-size:0.75em; color:#94a3b8; text-align:center; margin-top:10px;">
          ※一部の薬剤効果は、一般的な相対リスク低下(RRR)を用いた教育的推計です。
        </div>
      </div>

    </div>
  </div>
</div>

<script>
  let baseCalcRisk = 0;

  function calcRisk() {
    document.getElementById('error-msg').innerHTML = "";
    
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
      document.getElementById('error-msg').innerHTML = "⚠️ 必須項目（年齢〜HDL）をすべて入力してください。";
      return;
    }

    // --- CKMステージ判定ロジック ---
    let stage = 0;
    if (bmi >= 25) stage = 1; // 過体重をStage1とする
    if (sbp >= 130 || bp_med || tc >= 200 || statin || dm || hdl < 40 || egfr < 60 || (uacrStr && parseFloat(uacrStr) >= 30)) {
      stage = 2; // 代謝異常またはCKD
    }
    // Stage3の判定は計算後にリスクが>=20%の場合に上書きする

    // --- UIリセット ---
    document.querySelectorAll('.sim-btn').forEach(btn => {
      btn.classList.remove('active');
      btn.querySelector('input').checked = false;
    });

    // リスク計算実行
    baseCalcRisk = executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr);
    
    if (baseCalcRisk >= 20.0) stage = 3;

    // CKMステージUI更新
    document.querySelectorAll('.ckm-table td').forEach(td => td.classList.remove('active-stage'));
    document.getElementById('stage' + stage).classList.add('active-stage');

    document.getElementById('result-area').style.display = 'block';
    updateRiskUI(baseCalcRisk);
  }

  function toggleSim(checkbox) {
    if(checkbox.checked) {
      checkbox.parentElement.classList.add('active');
    } else {
      checkbox.parentElement.classList.remove('active');
    }
    runSimulation();
  }

  function runSimulation() {
    let age = parseFloat(document.getElementById('age').value);
    let sex = parseInt(document.getElementById('sex').value);
    let sbp = parseFloat(document.getElementById('sbp').value);
    let egfr = parseFloat(document.getElementById('egfr').value);
    let tc = parseFloat(document.getElementById('tc').value);
    let hdl = parseFloat(document.getElementById('hdl').value);
    
    let bp_med = document.getElementById('bp_med').checked;
    let statin = document.getElementById('statin').checked;
    let dm = document.getElementById('dm').checked;
    let smoke = document.getElementById('smoke').checked;
    let uacrStr = document.getElementById('uacr').value;
    let hba1cStr = document.getElementById('hba1c').value;

    let checkedSims = Array.from(document.querySelectorAll('.sim-btn input:checked')).map(inp => inp.value);

    // 数式内パラメーターの書き換えシミュレーション
    if (checkedSims.includes('quit')) smoke = false;
    if (checkedSims.includes('weight')) {
      sbp = Math.max(110, sbp - 5); 
      if (hba1cStr) hba1cStr = String(Math.max(5.5, parseFloat(hba1cStr) - 0.5));
    }
    if (checkedSims.includes('statin')) {
      statin = true;
      tc = Math.max(130, tc - 40); // 仮想的なLDL低下をTC低下で代用
    }

    // 再計算
    let simRisk = executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr);

    // KFRE同様の相対リスク減少(RRR)の乗算シミュレーション
    if (checkedSims.includes('sglt2')) simRisk *= 0.75; 
    if (checkedSims.includes('mra')) simRisk *= 0.85;

    updateRiskUI(simRisk);
  }

  function updateRiskUI(riskVal) {
    // 数字のアニメーション
    let numDiv = document.getElementById('risk-val');
    numDiv.innerHTML = riskVal.toFixed(1) + '<span class="big-unit">%</span>';

    // 色の変更
    let color = 'var(--indigo-deep)';
    if (riskVal < 5.0) color = 'var(--risk-low)';
    else if (riskVal < 7.5) color = 'var(--risk-border)';
    else if (riskVal < 20.0) color = 'var(--risk-mid)';
    else color = 'var(--risk-high)';
    numDiv.style.color = color;
    document.querySelector('.risk-pin').style.borderColor = color;
    document.querySelector('.pin-icon').style.fill = color;

    // ピンの移動計算 (0-40%のスケールを想定。5%->25%, 7.5%->37.5%, 20%->50%)
    // 対数的なマッピングで視覚的に配置
    let pos = 0;
    if (riskVal <= 5) pos = (riskVal / 5) * 25;
    else if (riskVal <= 7.5) pos = 25 + ((riskVal - 5) / 2.5) * 12.5;
    else if (riskVal <= 20) pos = 37.5 + ((riskVal - 7.5) / 12.5) * 12.5;
    else pos = 50 + ((Math.min(riskVal, 40) - 20) / 20) * 50;
    
    document.getElementById('risk-pin').style.left = Math.min(Math.max(pos, 0), 100) + '%';
  }

  // --- PREVENT式のモック計算関数 ---
  // ※注意: これはUIテスト用の近似ロジックです。
  // 臨床運用の際は、AHA PREVENT Methodology paper (2023) の
  // Supplemental Appendix にある実際の係数(Beta)とベースライン生存率に置き換えてください。
  function executePredictEquation(age, sex, sbp, bp_med, egfr, tc, hdl, statin, dm, smoke, uacrStr, hba1cStr) {
    let score = 0;
    
    // ベースモデルの近似的重み付け
    score += (age - 55) * 0.08;
    if (sex === 1) score += 0.4;
    score += (sbp - 120) * 0.015;
    if (bp_med) score += 0.15;
    score += (tc - 180) * 0.006;
    score -= (hdl - 50) * 0.01;
    if (statin) score -= 0.1;
    if (dm) score += 0.6;
    if (smoke) score += 0.5;
    
    if (egfr < 60) score += (60 - egfr) * 0.015;

    let modelText = "✓ 適用モデル: PREVENT Base Model";

    // アドオンモデル（UACR, HbA1c）が入力された場合の補正
    let isAddon = false;
    if (uacrStr && parseFloat(uacrStr) > 0) {
      let uacr = parseFloat(uacrStr);
      if (uacr > 30) score += Math.log(uacr/30) * 0.15;
      isAddon = true;
    }
    if (hba1cStr && parseFloat(hba1cStr) > 0) {
      let hba1c = parseFloat(hba1cStr);
      if (hba1c > 6.0) score += (hba1c - 6.0) * 0.15;
      isAddon = true;
    }
    if (isAddon) modelText = "✨ 適用モデル: PREVENT Add-on Model (精度向上)";
    
    document.getElementById('model-type').innerText = modelText;

    // 基準となるリスク（55歳、リスク因子なしの約3%をベースに想定）
    let risk = 3.0 * Math.exp(score);
    
    if (risk > 99.9) risk = 99.9;
    if (risk < 0.1) risk = 0.1;
    
    return risk;
  }
</script>
</body>
</html>
"""

# StreamlitでHTMLを描画 (十分な高さを確保)
st.html(f"<div style='height: 1400px;'>{html_code}</div>")