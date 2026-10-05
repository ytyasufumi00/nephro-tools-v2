<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>信州上田 慢性腎臓病予後予測システム (Ver.31)</title>
<style>
  /* --- カラーパレット --- */
  :root {
    --sanada-red: #b32020;       /* 深紅 */
    --sanada-gold: #d4af37;      /* 金色 */
    --castle-black: #2b2b2b;     /* 兜の黒 */
    --stone-gray: #777777;       /* グレー */
    --risk-high-color: #c0392b;  /* 警告色 */
    --risk-low-color: #27ae60;   /* 安全色 */
    --sim-color: #2980b9;        /* シミュレーション青 */
    --bg-washi: #fcfaf5;
  }

  body { 
    font-family: "Yu Mincho", "Hiragino Mincho ProN", "MS PMincho", serif; 
    background-color: var(--bg-washi); 
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='10' viewBox='0 0 20 10'%3E%3Cpath d='M0 10 C5 10 5 0 10 0 C15 0 15 10 20 10' stroke='%23e0d5c1' fill='none' opacity='0.5'/%3E%3C/svg%3E");
    padding: 20px; color: #3d2e2e; 
  }

  .container { max-width: 700px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); overflow: hidden; border: 1px solid #dcd0bc; }
  
  /* --- ヘッダーエリア --- */
  .header-area {
    background-color: var(--sanada-red);
    background-image: url("data:image/svg+xml,%3Csvg width='20' height='20' viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h20v20H0V0zm2 2v16h16V2H2z' fill='%23000000' fill-opacity='0.1'/%3E%3Cpath d='M2 2h2v2H2V2zm4 4h2v2H6V6zm4 4h2v2h-2v-2zm4 4h2v2h-2v-2zm4 4h2v2h-2v-2zM2 18h2v-2H2v2zm4-4h2v-2H6v2zm4-4h2v-2h-2v2zm4-4h2V6h-2v2zm4-4h2V2h-2v2z' fill='%23d4af37' fill-opacity='0.15'/%3E%3C/svg%3E");
    padding: 30px 20px 25px; text-align: center; color: white; position: relative;
    border-bottom: 4px solid var(--castle-black);
    border-top: 8px solid var(--castle-black);
  }

  .header-icons { display: flex; justify-content: center; align-items: flex-end; gap: 30px; margin-bottom: 25px; }
  .svg-icon { fill: var(--sanada-gold); filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.3)); }
  .kabuto-svg { width: 130px; height: auto; }
  .rokumonsen-svg { width: 55px; height: auto; margin-bottom: 5px; }

  h2 { font-family: "HGS 行書B", "HGP行書B", "HG行書B", serif; margin: 0; font-size: 1.6em; line-height: 1.3; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); letter-spacing: 0.05em; }
  .sub-title-main { font-size: 0.95em; margin-top: 5px; font-weight: bold; }
  .sub-title-kfre { font-size: 0.75em; opacity: 0.85; margin-top: 8px; font-family: sans-serif; }

  /* --- 入力フォーム --- */
  .content-body { padding: 30px; }
  .form-group { margin-bottom: 20px; }
  label { display: block; font-weight: bold; margin-bottom: 8px; color: #5a4a4a; font-size: 0.95em; }
  
  input[type="number"], select { 
    width: 100%; padding: 12px; font-size: 16px; 
    border: 2px solid #e0d5c1; border-radius: 6px; 
    box-sizing: border-box; background: #fffdf9; font-family: sans-serif;
    transition: border 0.2s;
  }
  input:focus, select:focus { outline: none; border-color: var(--sanada-red); background: #fff; }

  .radio-area { background: #fdfaf4; padding: 20px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #e6dcc8; }
  .radio-label { margin-right: 20px; cursor: pointer; display: inline-flex; align-items: center; font-weight: bold; color: #3d2e2e; }
  .radio-label input { margin-right: 8px; accent-color: var(--sanada-red); transform: scale(1.2); }

  .guide-table { width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; background: #fff; border: 1px solid #ddd; }
  .guide-table th { background: #eee; padding: 4px; text-align: center; border: 1px solid #ddd; color: #555; width: 25%; }
  .guide-table td { padding: 4px; text-align: center; border: 1px solid #ddd; font-weight: bold; color: var(--sanada-red); }
  .guide-note { font-size: 0.8em; color: #666; margin-top: 5px; text-align: right; }

  /* --- ボタン（クリック感強化） --- */
  button.calc-btn { 
    width: 100%; padding: 18px; 
    background: linear-gradient(to bottom, var(--sanada-red), #8a1919);
    color: white; border: none; border-radius: 6px; 
    font-size: 20px; font-weight: bold; cursor: pointer; 
    box-shadow: 0 4px 0 #5e1111; margin-bottom: 15px;
    letter-spacing: 0.1em; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    position: relative; overflow: hidden; /* 波紋用 */
    transition: transform 0.1s, box-shadow 0.1s;
  }
  
  /* ホバー時 */
  button.calc-btn:hover { transform: translateY(2px); box-shadow: 0 2px 0 #5e1111; }
  
  /* クリック時（沈み込み） */
  button.calc-btn:active { transform: translateY(4px) scale(0.98); box-shadow: 0 0 0 #5e1111; }

  /* 波紋エフェクト */
  span.ripple {
    position: absolute; border-radius: 50%;
    transform: scale(0); animation: ripple 0.6s linear;
    background-color: rgba(255, 255, 255, 0.5);
    pointer-events: none;
  }
  @keyframes ripple { to { transform: scale(4); opacity: 0; } }

  /* --- 結果表示エリア --- */
  #result-area { margin-top: 30px; display: none; animation: fadeIn 0.6s ease; }
  .result-cards { display: flex; gap: 15px; margin-bottom: 20px; }
  @media (max-width: 600px) { .result-cards { flex-direction: column; } }

  .card { flex: 1; background: #fff; border-radius: 8px; text-align: center; padding-bottom: 15px; border: 2px solid #ddd; transition: all 0.5s; position: relative; }
  .card-header { background: #eee; color: #555; padding: 12px 5px; font-weight: bold; border-radius: 5px 5px 0 0; border-bottom: 1px solid #ddd; transition: background 0.5s; font-size: 0.9em; line-height: 1.4; }
  .risk-number { font-family: sans-serif; font-size: 3.5em; line-height: 1; margin: 15px 0; font-weight: bold; transition: color 0.3s; }
  .risk-unit { font-size: 0.5em; font-weight: normal; }
  
  .judge-mark {
    position: absolute; top: -15px; right: -10px; width: 45px; height: 45px; border-radius: 50%; 
    line-height: 45px; font-weight: bold; font-family: sans-serif; font-size: 1.4em;
    box-shadow: 0 3px 6px rgba(0,0,0,0.2); display: none; z-index: 10;
    animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  .card.target-risk .judge-mark { display: block; }

  #advice-box { padding: 20px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1em; border: 2px solid transparent; margin-bottom: 25px; transition: all 0.5s; }

  /* --- 治療シミュレーション --- */
  .strategy-area { margin-top: 30px; border: 2px dashed #d4af37; border-radius: 8px; padding: 20px; background: #fffcf0; display: none; }
  .strategy-title { text-align: center; font-weight: bold; color: #8a6d3b; margin-bottom: 15px; font-size: 1.1em; border-bottom: 1px dashed #d4af37; padding-bottom: 10px; }
  .toggle-container { display: flex; flex-wrap: wrap; justify-content: space-around; gap: 15px; }
  .toggle-item { background: #f8f8f8; border: 2px solid #ccc; color: #666; padding: 12px 18px; border-radius: 8px; cursor: pointer; user-select: none; transition: all 0.2s ease; font-size: 0.95em; font-weight: bold; display: flex; align-items: center; box-shadow: 0 2px 0 #ddd; width: 45%; box-sizing: border-box; justify-content: center; }
  @media (max-width: 600px) { .toggle-item { width: 100%; } }
  .toggle-item:hover { background: #eee; transform: translateY(1px); }
  .toggle-item input { display: none; }
  .toggle-item.active { background: var(--sanada-red); color: white; border-color: var(--sanada-gold); box-shadow: 0 2px 0 #8a1919; }
  .check-icon { display: inline-block; width: 18px; height: 18px; background: white; border: 2px solid #999; border-radius: 4px; margin-right: 10px; position: relative; transition: all 0.2s; }
  .toggle-item.active .check-icon { border-color: white; background: white; }
  .toggle-item.active .check-icon::after { content: ""; position: absolute; left: 5px; top: 1px; width: 5px; height: 10px; border: solid var(--sanada-red); border-width: 0 3px 3px 0; transform: rotate(45deg); }
  .sim-note { font-size: 0.8em; color: #8a6d3b; text-align: center; margin-top: 15px; }

  /* --- 出典 --- */
  .source-area { margin-top: 30px; padding: 15px; background: #f9f9f9; border-top: 1px solid #eee; font-size: 0.75em; color: #666; line-height: 1.5; }
  .source-title { font-weight: bold; color: #333; margin-bottom: 5px; }
  .source-list { list-style-type: none; padding: 0; margin: 0; }
  .source-list li { margin-bottom: 3px; padding-left: 10px; text-indent: -10px; }

  /* --- ステータス変化 --- */
  .status-red .target-risk { border-color: var(--risk-high-color); background-color: #fff5f5; }
  .status-red .target-risk .card-header { background: var(--risk-high-color); color: white; border-color: var(--risk-high-color); }
  .status-red .target-risk .risk-number { color: var(--risk-high-color); }
  .status-red #advice-box { color: #721c24; background: #f8d7da; border-color: #f5c6cb; }
  .status-red .target-risk .judge-mark { background: var(--risk-high-color); color: white; animation: popIn 0.4s, pulse 1s infinite 0.4s; }

  .status-green .target-risk { border-color: var(--risk-low-color); background-color: #f0fff4; }
  .status-green .target-risk .card-header { background: var(--risk-low-color); color: white; border-color: var(--risk-low-color); }
  .status-green .target-risk .risk-number { color: var(--risk-low-color); }
  .status-green #advice-box { color: #155724; background: #d4edda; border-color: #c3e6cb; }
  .status-green .target-risk .judge-mark { background: var(--risk-low-color); color: white; }

  .status-sim .target-risk .risk-number { color: var(--sim-color); }
  .status-sim .target-risk .judge-mark { background: var(--sim-color); color: white; content: "★"; animation: popIn 0.4s; }

  .card:not(.target-risk) { opacity: 0.6; }
  .note-text { font-size: 0.8em; color: #888; text-align: right; margin-top: 5px; }
  .copyright { text-align: center; font-size: 0.75em; color: #ccc; margin-top: 10px; }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes popIn { from { transform: scale(0); } to { transform: scale(1); } }
  @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
</style>
</head>
<body>

<div class="container">
  <div class="header-area">
    <div class="header-icons">
      <svg class="svg-icon rokumonsen-svg" viewBox="0 0 60 40">
        <g fill="var(--sanada-gold)">
          <circle cx="10" cy="10" r="8"/><rect x="7" y="7" width="6" height="6" fill="var(--sanada-red)"/>
          <circle cx="30" cy="10" r="8"/><rect x="27" y="7" width="6" height="6" fill="var(--sanada-red)"/>
          <circle cx="50" cy="10" r="8"/><rect x="47" y="7" width="6" height="6" fill="var(--sanada-red)"/>
          <circle cx="10" cy="30" r="8"/><rect x="7" y="27" width="6" height="6" fill="var(--sanada-red)"/>
          <circle cx="30" cy="30" r="8"/><rect x="27" y="27" width="6" height="6" fill="var(--sanada-red)"/>
          <circle cx="50" cy="30" r="8"/><rect x="47" y="27" width="6" height="6" fill="var(--sanada-red)"/>
        </g>
      </svg>
      <svg class="svg-icon kabuto-svg" viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M30,70 Q60,30 90,70" fill="var(--castle-black)" stroke="none"/>
        <path d="M20,70 Q60,100 100,70 L105,80 Q60,115 15,80 Z" fill="var(--castle-black)" />
        <path d="M25,65 L95,65" fill="none" stroke="var(--sanada-gold)" stroke-width="2" />
        <path d="M35,60 Q10,40 10,10" fill="none" stroke="var(--sanada-gold)" stroke-width="5" stroke-linecap="round"/>
        <path d="M10,35 L20,30" fill="none" stroke="var(--sanada-gold)" stroke-width="3" stroke-linecap="round"/>
        <path d="M85,60 Q110,40 110,10" fill="none" stroke="var(--sanada-gold)" stroke-width="5" stroke-linecap="round"/>
        <path d="M110,35 L100,30" fill="none" stroke="var(--sanada-gold)" stroke-width="3" stroke-linecap="round"/>
        <circle cx="60" cy="65" r="6" fill="var(--sanada-gold)" />
      </svg>
    </div>

    <h2>信州上田 慢性腎臓病<br>腎機能予後予測システム</h2>
    <div class="sub-title-main">(信州上田医療センターVer.)</div>
    <div class="sub-title-kfre">Powered by Kidney Failure Risk Equation</div>
  </div>

  <div class="content-body">
    <div class="form-group">
      <label>年齢 (歳)</label>
      <input type="number" id="age" placeholder="例: 65">
    </div>

    <div class="form-group">
      <label>性別</label>
      <select id="sex">
        <option value="1">男性</option>
        <option value="0">女性</option>
      </select>
    </div>

    <div class="form-group">
      <label>eGFR (mL/min/1.73m²)</label>
      <input type="number" id="egfr" placeholder="例: 45">
    </div>

    <div class="radio-area">
      <label style="margin-bottom:12px; display:block; color:var(--sanada-red); font-size:1.1em;">▼ 尿検査の項目を選択</label>
      <label class="radio-label">
        <input type="radio" name="urineType" value="PCR" checked onclick="toggleMode()"> 尿蛋白定量 (PCR)
      </label>
      <label class="radio-label">
        <input type="radio" name="urineType" value="ACR" onclick="toggleMode()"> 尿アルブミン (ACR)
      </label>
      <hr style="margin: 15px 0; border:0; border-top:1px solid #dcd0bc;">
      
      <div id="pcr-input-group">
        <label>尿蛋白/Cr比 (g/gCr)</label>
        <input type="number" id="pcr_val" placeholder="例: 0.3">
        <small style="color:#888;">※定量値(g/gCr)を入力してください</small>
        
        <div style="margin-top:10px;">
          <small style="font-weight:bold; color:var(--sanada-red);">▼ 定性検査(1+など)しかない場合の入力目安</small>
          <table class="guide-table">
            <tr>
              <th>定性</th>
              <td style="color:#555;">(±)</td>
              <td>1+</td>
              <td>2+</td>
              <td>3+</td>
            </tr>
            <tr>
              <th>入力値</th>
              <td style="color:#555; font-weight:normal;">0.15</td>
              <td>0.4</td>
              <td>0.9</td>
              <td>1.9</td>
            </tr>
          </table>
          <div class="guide-note">※日本腎臓学会 CKD診療ガイドを参照</div>
        </div>
      </div>

      <div id="acr-input-group" style="display:none;">
        <label>尿アルブミン/Cr比 (mg/gCr)</label>
        <input type="number" id="acr_val" placeholder="例: 300">
      </div>
    </div>

    <button type="button" class="calc-btn" onclick="handleClick(event)">計算する</button>

    <div id="result-area">
      <div id="advice-box"></div>

      <div class="result-cards">
        <div class="card" id="card-5y">
          <div class="card-header">5年で末期腎不全に至る可能性</div>
          <div class="risk-number" id="risk5-container"><span id="risk5-disp">--</span><span class="risk-unit">%</span></div>
          <div class="judge-mark"></div>
        </div>
        <div class="card" id="card-10y">
          <div class="card-header">10年で末期腎不全に至る可能性 (推定)</div>
          <div class="risk-number" id="risk10-container"><span id="risk10-disp">--</span><span class="risk-unit">%</span></div>
          <div class="judge-mark"></div>
        </div>
      </div>
      
      <div class="strategy-area" id="strategy-area">
        <div class="strategy-title">▼ 治療介入によるリスク低減（シミュレーション）</div>
        <div class="toggle-container">
          <label class="toggle-item">
            <span class="check-icon"></span>
            <input type="checkbox" value="bp" onchange="simChange(this)"> 厳格な血圧管理
          </label>
          <label class="toggle-item">
            <span class="check-icon"></span>
            <input type="checkbox" value="ras" onchange="simChange(this)"> ACE阻害薬 / ARB
          </label>
          <label class="toggle-item">
            <span class="check-icon"></span>
            <input type="checkbox" value="sglt2" onchange="simChange(this)"> SGLT2阻害薬
          </label>
          <label class="toggle-item">
            <span class="check-icon"></span>
            <input type="checkbox" value="mra" onchange="simChange(this)"> ミネラルコルチコイド受容体阻害薬
          </label>
        </div>
        <div class="sim-note">※上記薬剤等の一般的なリスク低減効果(20〜30%)を仮定した教育用シミュレーションです。</div>
      </div>

      <div class="note-text" id="conv-msg"></div>
      
      <div class="source-area">
        <div class="source-title">【出典・根拠】</div>
        <ul class="source-list">
          <li><b>紹介基準:</b> Caldinelli A, et al. Risk-based referral model to nephrologist specialist care. <i>Nephrol Dial Transplant.</i> 2026;41(1):102–111.</li>
          <li><b>計算モデル:</b> Tangri N, et al. Multinational Assessment of Accuracy of Equations for Predicting Risk of Kidney Failure (Non-North American 4-var). <i>JAMA.</i> 2016;315(2):164-174.</li>
          <li>※10年リスクは標準モデル(5年)の減衰曲線より算出した推定値です。</li>
          <li>※尿蛋白換算はCKD診療ガイドを参考に設定しています。</li>
        </ul>
      </div>

    </div>
    
    <div class="copyright">Shinshu Ueda Area Cooperation Project</div>
  </div>
</div>

<script>
  // グローバル変数
  var baseRisk5 = 0;
  var baseRisk10 = 0;

  function toggleMode() {
    var radios = document.getElementsByName('urineType');
    var val = 'PCR';
    for(var i=0; i<radios.length; i++){ if(radios[i].checked) val = radios[i].value; }
    
    if(val === 'PCR'){
      document.getElementById('pcr-input-group').style.display = 'block';
      document.getElementById('acr-input-group').style.display = 'none';
      document.getElementById('pcr_val').value = '';
    } else {
      document.getElementById('pcr-input-group').style.display = 'none';
      document.getElementById('acr-input-group').style.display = 'block';
      document.getElementById('acr_val').value = '';
    }
  }

  // ボタンクリック時のリップル効果と計算実行
  function handleClick(event) {
    createRipple(event);
    setTimeout(calc, 100); 
  }

  function createRipple(event) {
    var button = event.currentTarget;
    var circle = document.createElement("span");
    var diameter = Math.max(button.clientWidth, button.clientHeight);
    var radius = diameter / 2;

    circle.style.width = circle.style.height = diameter + "px";
    circle.style.left = (event.clientX - button.getBoundingClientRect().left - radius) + "px";
    circle.style.top = (event.clientY - button.getBoundingClientRect().top - radius) + "px";
    circle.classList.add("ripple");

    var ripple = button.getElementsByClassName("ripple")[0];
    if (ripple) { ripple.remove(); }

    button.appendChild(circle);
  }

  function calc() {
    try {
      var age = parseFloat(document.getElementById('age').value);
      var sex = parseInt(document.getElementById('sex').value);
      var egfr = parseFloat(document.getElementById('egfr').value);
      var acr = 0;
      var msg = "";
      
      var radios = document.getElementsByName('urineType');
      var type = 'PCR';
      for(var i=0; i<radios.length; i++){ if(radios[i].checked) type = radios[i].value; }

      if(type === 'PCR'){
        var pInput = parseFloat(document.getElementById('pcr_val').value);
        if(isNaN(pInput)) { alert("尿蛋白値を入力してください"); return; }
        
        // 0なら0.1として扱う (変更点)
        if(pInput === 0) {
          pInput = 0.1;
          msg = "※尿蛋白 0 を 0.1 g/gCr として計算しました";
        }
        
        acr = pInput * 1000 * 0.7;
        if(msg === "") msg = "※尿蛋白 " + pInput + " g/gCr を ACR " + Math.round(acr) + " mg/gCr に換算して計算";
        
      } else {
        var aInput = parseFloat(document.getElementById('acr_val').value);
        if(isNaN(aInput)) { alert("尿アルブミン値を入力してください"); return; }
        // ACR 0なら 10 (変更点)
        if(aInput === 0) {
          aInput = 10;
          msg = "※尿アルブミン 0 を 10 mg/gCr として計算しました";
        }
        acr = aInput;
      }

      if (acr < 1) acr = 1;
      if(isNaN(age) || isNaN(egfr)) { alert("年齢とeGFRを入力してください"); return; }

      var lnACR = Math.log(acr);
      var score = -0.2201 * (age/10 - 7.036) 
                  + 0.2467 * (sex - 0.5642) 
                  - 0.5567 * (egfr/5 - 7.222) 
                  + 0.4510 * (lnACR - 5.137);
      
      var expScore = Math.exp(score);
      baseRisk5 = 1 - Math.pow(0.9365, expScore);
      baseRisk10 = 1 - Math.pow(0.876, expScore);

      document.getElementById('result-area').style.display = 'block';
      document.getElementById('strategy-area').style.display = 'block';
      document.getElementById('conv-msg').innerHTML = msg;
      
      // オートスクロール
      document.getElementById('result-area').scrollIntoView({behavior: 'smooth', block: 'start'});

      var items = document.querySelectorAll('.toggle-item');
      items.forEach(function(item){ 
        item.classList.remove('active'); 
        item.querySelector('input').checked = false;
      });

      updateDisplay(baseRisk5, baseRisk10, false);

    } catch(e) {
      alert("エラー: " + e);
    }
  }

  function simChange(inputElement) {
    var label = inputElement.parentElement;
    if(inputElement.checked) {
      label.classList.add('active');
    } else {
      label.classList.remove('active');
    }
    runSimulation();
  }

  function runSimulation() {
    var factor = 1.0;
    var inputs = document.querySelectorAll('.strategy-area input:checked');
    inputs.forEach(function(inp){
      if(inp.value === 'bp') factor *= 0.8;
      if(inp.value === 'ras') factor *= 0.77;
      if(inp.value === 'sglt2') factor *= 0.7;
      if(inp.value === 'mra') factor *= 0.85;
    });

    var new5 = baseRisk5 * factor;
    var new10 = baseRisk10 * factor;
    var isSimulated = (factor < 1.0);
    
    updateDisplay(new5, new10, isSimulated);
  }

  function updateDisplay(r5, r10, isSim) {
    var age = parseFloat(document.getElementById('age').value);
    
    // 蛋白尿チェック（0.5以上なら強制紹介）
    var isHighProtein = false;
    var radios = document.getElementsByName('urineType');
    var type = 'PCR';
    for(var i=0; i<radios.length; i++){ if(radios[i].checked) type = radios[i].value; }
    if(type === 'PCR') {
       if(parseFloat(document.getElementById('pcr_val').value) >= 0.5) isHighProtein = true;
    } else {
       if(parseFloat(document.getElementById('acr_val').value) >= 300) isHighProtein = true;
    }

    var r5per = r5 * 100;
    var r10per = r10 * 100;

    var area = document.getElementById('result-area');
    var adviceBox = document.getElementById('advice-box');
    var card5 = document.getElementById('card-5y');
    var card10 = document.getElementById('card-10y');
    var marks = document.querySelectorAll('.judge-mark');
    
    // 表示リセット
    area.classList.remove('status-red', 'status-green', 'status-sim');
    card5.classList.remove('target-risk');
    card10.classList.remove('target-risk');

    var isReferral = false;
    var reason = "";

    // 判定ロジック: 蛋白尿0.5以上は強制紹介。それ以外は確率で判定
    if(isHighProtein) {
        isReferral = true;
        reason = "蛋白尿(0.5以上)";
    } else {
        if (age < 70) {
            if (r10per >= 5.0) { isReferral = true; reason = "70歳未満 基準:10年5%"; }
            else { reason = "70歳未満 基準:10年5%"; }
        } else {
            if (r5per >= 5.0) { isReferral = true; reason = "70歳以上 基準:5年5%"; }
            else { reason = "70歳以上 基準:5年5%"; }
        }
    }

    animateValue("risk5-disp", 0, r5per, 500);
    animateValue("risk10-disp", 0, r10per, 500);

    // カード強調
    if (age < 70) card10.classList.add('target-risk');
    else card5.classList.add('target-risk');

    if (isSim) area.classList.add('status-sim');

    if (isReferral) {
        area.classList.add('status-red');
        var adviceText = "";
        if (isHighProtein) {
             adviceText = "⚠️ 紹介推奨 (" + reason + ")";
        } else {
             adviceText = "⚠️ 紹介推奨 (" + reason + "以上)";
        }

        if(isSim) adviceText = "治療強化後もリスク高<br>専門医連携を推奨";
        else adviceText += "<br>腎臓専門医への紹介をご検討ください";
        
        adviceBox.innerHTML = adviceText;
        marks.forEach(function(m){ m.innerHTML = "!"; });
    } else {
        area.classList.add('status-green');
        var adviceText = "経過観察可能 (" + reason + "未満)";
        if(isSim) adviceText = "✨ 治療により基準値未満へ改善可能<br>適切な管理継続を推奨します";
        else adviceText += "<br>かかりつけ医での管理を推奨します";

        adviceBox.innerHTML = adviceText;
        marks.forEach(function(m){ m.innerHTML = "✔"; });
    }
  }

  function animateValue(id, start, end, duration) {
    var obj = document.getElementById(id);
    if(!obj) return;
    var range = end - start;
    var current = start;
    var increment = end > start ? 0.1 : -0.1;
    var stepTime = Math.abs(Math.floor(duration / (range / increment)));
    
    if(stepTime < 10) { stepTime = 10; increment = range / (duration / 10); }

    var timer = setInterval(function() {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        current = end;
        clearInterval(timer);
        obj.innerHTML = end.toFixed(1);
      } else {
        var disp = current.toFixed(1);
        if(current > 99.9) disp = ">99";
        if(current < 0.1) disp = "<0.1";
        obj.innerHTML = disp;
      }
    }, stepTime);
  }
</script>
</body>
</html>