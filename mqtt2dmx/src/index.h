#pragma once

const char INDEX_HTML[] PROGMEM = R"=====(
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DMX Light Controller</title><style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
    min-height: 100vh;
    box-sizing: border-box;
}
.page-container {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 20px;
    max-width: 1600px;
    margin: 0 auto;
    height: calc(100vh - 100px);
}
.controls-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    align-content: start;
}
.presets-container {
    position: relative;
    height: 100%;
}
.card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.presets-card {
    position: sticky;
    top: 20px;
    height: calc(100vh - 140px);
    display: flex;
    flex-direction: column;
}
.slider-container {
    margin: 10px 0;
}
.slider-container label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}
.slider-row {
    display: flex;
    align-items: center;
    gap: 10px;
}
input[type="range"] {
    flex: 1;
}
input[type="number"] {
    width: 60px;
    padding: 4px;
}
button {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    margin: 5px;
}
button:hover {
    background: #0056b3;
}
button.secondary {
    background: #6c757d;
}
button.secondary:hover {
    background: #545b62;
}
.preset-controls {
    margin-bottom: 10px;
}
#presetList {
    flex: 1;
    overflow-y: auto;
    margin-top: 10px;
    background: #f8f9fa;
    border-radius: 4px;
    padding: 10px;
}
.preset-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    background: white;
    margin: 4px 0;
    border-radius: 4px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.preset-item:hover {
    background: #f8f9fa;
}
.value-display {
    font-family: monospace;
    font-size: 14px;
    color: #666;
}
.demo-controls {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}
.demo-controls h3 {
    margin-top: 0;
}
.demo-sequence {
    background: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
    margin: 10px 0;
    max-height: 100px;
    overflow-y: auto;
}
.custom-channel {
    display: flex;
    gap: 10px;
    align-items: center;
    margin: 10px 0;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 4px;
}
.custom-channel input[type="number"] {
    width: 80px;
    padding: 8px;
}
</style></head><body><h1>DMX Light Controller</h1><div class="page-container"><div class="controls-container"><div class="card"><h2>Position Control</h2><div class="slider-container"><label>Pan (0-540°)</label><div class="slider-row"><input type="range" id="pan" min="0" max="255" value="128"><input type="number" id="panValue" min="0" max="255" value="128"></div></div><div class="slider-container"><label>Pan Fine</label><div class="slider-row"><input type="range" id="panFine" min="0" max="255" value="128"><input type="number" id="panFineValue" min="0" max="255" value="128"></div></div><div class="slider-container"><label>Tilt (0-190°)</label><div class="slider-row"><input type="range" id="tilt" min="0" max="255" value="128"><input type="number" id="tiltValue" min="0" max="255" value="128"></div></div><div class="slider-container"><label>Tilt Fine</label><div class="slider-row"><input type="range" id="tiltFine" min="0" max="255" value="128"><input type="number" id="tiltFineValue" min="0" max="255" value="128"></div></div><div class="slider-container"><label>Movement Speed (Fast → Slow)</label><div class="slider-row"><input type="range" id="speed" min="0" max="255" value="0"><input type="number" id="speedValue" min="0" max="255" value="0"></div></div></div><div class="card"><h2>Light Control</h2><div class="slider-container"><label>Master Dimmer</label><div class="slider-row"><input type="range" id="dimmer" min="0" max="255" value="255"><input type="number" id="dimmerValue" min="0" max="255" value="255"></div></div><div class="slider-container"><label>Strobe (Slow → Fast)</label><div class="slider-row"><input type="range" id="strobe" min="0" max="255" value="0"><input type="number" id="strobeValue" min="0" max="255" value="0"></div></div><div class="slider-container"><label>Red</label><div class="slider-row"><input type="range" id="red" min="0" max="255" value="255"><input type="number" id="redValue" min="0" max="255" value="255"></div></div><div class="slider-container"><label>Green</label><div class="slider-row"><input type="range" id="green" min="0" max="255" value="255"><input type="number" id="greenValue" min="0" max="255" value="255"></div></div><div class="slider-container"><label>Blue</label><div class="slider-row"><input type="range" id="blue" min="0" max="255" value="255"><input type="number" id="blueValue" min="0" max="255" value="255"></div></div><div class="slider-container"><label>White</label><div class="slider-row"><input type="range" id="white" min="0" max="255" value="255"><input type="number" id="whiteValue" min="0" max="255" value="255"></div></div></div><div class="card"><h2>Custom Channel Control</h2><div class="custom-channel"><label>Channel: <input type="number" id="customChannel" min="1" max="512" value="1"></label><label>Value: <input type="number" id="customValue" min="0" max="255" value="0"></label><button onclick="setCustomChannel()">Set Channel</button></div><div id="customChannelHistory" style="margin-top: 10px; font-family: monospace;"></div></div></div><div class="presets-container"><div class="card presets-card"><h2>Presets</h2><div class="preset-controls"><input type="text" id="presetName" placeholder="Preset name" style="width: 200px; padding: 8px; margin-right: 5px;"><button onclick="savePreset()">Save Current as Preset</button></div><div class="preset-controls"><button onclick="downloadPresets()" class="secondary">Download All Presets</button><button onclick="document.getElementById('uploadPresets').click()" class="secondary">Upload Presets</button><input type="file" id="uploadPresets" style="display:none" onchange="uploadPresetsFile(this)"></div><div id="presetList"></div><div class="demo-controls"><h3>Demo Mode</h3><div><label>Movement Delay (ms): <input type="number" id="moveDelay" value="1000" min="0" max="10000"></label></div><div><label>Hold Time (s): <input type="number" id="holdTime" value="5" min="1" max="60"></label></div><div>Selected Sequence:</div><div id="demoSequence" class="demo-sequence"></div><div><button onclick="startDemo()" id="demoButton">Start Demo</button><button onclick="stopDemo()" class="secondary" id="stopButton" style="display:none">Stop Demo</button></div></div></div></div></div><script>const channels={pan:1,panFine:2,tilt:3,tiltFine:4,speed:5,dimmer:6,strobe:7,red:8,green:9,blue:10,white:11};Object.keys(channels).forEach(id=>{const slider=document.getElementById(id);const value=document.getElementById(id+"Value");slider.oninput=()=>{value.value=slider.value;updateChannel(channels[id],parseInt(slider.value))};value.oninput=()=>{slider.value=value.value;updateChannel(channels[id],parseInt(value.value))}});async function updateChannel(channel,value){try{const response=await fetch("/api/channels",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({channel,value})});if(!response.ok)throw new Error("Failed to update channel")}catch(error){console.error("Error updating channel:",error)}}async function updateChannelsBatch(updates){try{const response=await fetch("/api/channels/batch",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({updates})});if(!response.ok)throw new Error("Failed to update channels")}catch(error){console.error("Error updating channels:",error)}}function savePreset(){const name=document.getElementById("presetName").value.trim();if(!name){alert("Please enter a preset name");return}const values=Object.keys(channels).map(id=>parseInt(document.getElementById(id).value));const presets=JSON.parse(localStorage.getItem("dmxPresets")||"{}");presets[name]=values;localStorage.setItem("dmxPresets",JSON.stringify(presets));document.getElementById("presetName").value="";updatePresetList()}async function loadPreset(name){const presets=JSON.parse(localStorage.getItem("dmxPresets")||"{}");const values=presets[name];if(!values)return;const updates=[];Object.keys(channels).forEach((id,index)=>{const slider=document.getElementById(id);const valueInput=document.getElementById(id+"Value");slider.value=values[index];valueInput.value=values[index];updates.push({channel:channels[id],value:values[index]})});await updateChannelsBatch(updates)}function deletePreset(name){const presets=JSON.parse(localStorage.getItem("dmxPresets")||"{}");delete presets[name];localStorage.setItem("dmxPresets",JSON.stringify(presets));updatePresetList()}function updatePresetList(){const presets=JSON.parse(localStorage.getItem("dmxPresets")||"{}");const list=document.getElementById("presetList");list.innerHTML="";Object.entries(presets).forEach(([name,values])=>{const item=document.createElement("div");item.className="preset-item";item.innerHTML=`<span>${name}</span><div><button onclick="loadPreset('${name}')">Load</button><button onclick="togglePresetSelection('${name}')" class="secondary">Add to Demo</button><button onclick="deletePreset('${name}')" class="secondary">Delete</button></div>`;list.appendChild(item)})}function downloadPresets(){const presets=localStorage.getItem("dmxPresets")||"{}";const blob=new Blob([presets],{type:"application/json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="dmx_presets.json";document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url)}function uploadPresetsFile(input){const file=input.files[0];if(!file)return;const reader=new FileReader;reader.onload=function(e){try{const presets=JSON.parse(e.target.result);localStorage.setItem("dmxPresets",JSON.stringify(presets));updatePresetList();input.value=""}catch(error){console.error("Error parsing presets file:",error);alert("Invalid presets file")}};reader.readAsText(file)}

let selectedPresets = [];
let isDemoRunning = false;

function togglePresetSelection(name) {
    const idx = selectedPresets.indexOf(name);
    if (idx === -1) {
        selectedPresets.push(name);
    } else {
        selectedPresets.splice(idx, 1);
    }
    updateDemoSequence();
}

function updateDemoSequence() {
    const seq = document.getElementById('demoSequence');
    seq.innerHTML = selectedPresets.map((name, idx) => 
        `<div>${idx + 1}. ${name}</div>`
    ).join('');
}

async function startDemo() {
    if (selectedPresets.length < 2) {
        alert('Please select at least 2 presets for the demo');
        return;
    }

    const moveDelay = parseInt(document.getElementById('moveDelay').value);
    const holdTime = parseInt(document.getElementById('holdTime').value);

    try {
        const response = await fetch('/api/demo/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                presets: selectedPresets.map(name => ({
                    name,
                    values: JSON.parse(localStorage.getItem('dmxPresets'))[name]
                })),
                moveDelay,
                holdTime: holdTime * 1000
            })
        });

        if (response.ok) {
            isDemoRunning = true;
            document.getElementById('demoButton').style.display = 'none';
            document.getElementById('stopButton').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error starting demo:', error);
    }
}

async function stopDemo() {
    try {
        const response = await fetch('/api/demo/stop', {
            method: 'POST'
        });

        if (response.ok) {
            isDemoRunning = false;
            document.getElementById('demoButton').style.display = 'inline-block';
            document.getElementById('stopButton').style.display = 'none';
        }
    } catch (error) {
        console.error('Error stopping demo:', error);
    }
}

// Add custom channel control
async function setCustomChannel() {
    const channel = parseInt(document.getElementById('customChannel').value);
    const value = parseInt(document.getElementById('customValue').value);
    
    if (channel < 1 || channel > 512 || value < 0 || value > 255) {
        alert('Invalid channel or value');
        return;
    }
    
    try {
        await updateChannel(channel, value);
        
        // Add to history
        const history = document.getElementById('customChannelHistory');
        const time = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.textContent = `${time} - Channel ${channel} = ${value}`;
        history.insertBefore(entry, history.firstChild);
        
        // Keep only last 5 entries
        while (history.children.length > 5) {
            history.removeChild(history.lastChild);
        }
    } catch (error) {
        console.error('Error setting custom channel:', error);
        alert('Failed to set channel');
    }
}

updatePresetList();
</script></body></html>
)====="; 