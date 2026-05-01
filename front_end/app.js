const API_URL = "http://localhost:8000";
let currentUser = null;
let currentProblemMode = 'manual';
let selectedZipFile = null;
let tcCounter = 0;
let quillEditor = null;

// Ensure Quill is loaded properly on start
document.addEventListener("DOMContentLoaded", () => {
    quillEditor = new Quill('#editor-container', {
        theme: 'snow',
        placeholder: 'Write the problem statement...',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, false] }],
                ['bold', 'italic', 'code-block'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }]
            ]
        }
    });
    
    // Check if user is already logged in from previous session
    const storedToken = localStorage.getItem('oj_token');
    const storedRole = localStorage.getItem('oj_role');
    const storedName = localStorage.getItem('oj_username');
    
    if (storedToken && storedRole) {
        currentUser = { token: storedToken, role: storedRole, username: storedName };
        setupWorkspace();
    }
});

async function handleLogin() {
    const u = document.getElementById('login-username').value;
    const p = document.getElementById('login-password').value;
    const errBox = document.getElementById('login-error');
    
    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        
        if (res.ok) {
            errBox.classList.add('hidden');
            // Store credentials securely in local storage
            localStorage.setItem('oj_token', data.access_token);
            localStorage.setItem('oj_role', data.role);
            localStorage.setItem('oj_username', data.username);
            
            currentUser = { token: data.access_token, role: data.role, username: data.username };
            setupWorkspace();
        } else {
            errBox.innerText = data.detail || "Login failed";
            errBox.classList.remove('hidden');
        }
    } catch (err) {
        errBox.innerText = "Cannot connect to server.";
        errBox.classList.remove('hidden');
    }
}

function handleLogout() {
    localStorage.clear();
    currentUser = null;
    document.getElementById('dashboard-screen').classList.add('hidden');
    document.getElementById('dashboard-screen').classList.remove('flex');
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('login-screen').classList.add('flex');
}

function setupWorkspace() {
    // Hide login, show dashboard
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('flex');
    
    const dashboard = document.getElementById('dashboard-screen');
    dashboard.classList.remove('hidden');
    dashboard.classList.add('flex');
    
    document.getElementById('user-greeting').innerText = `Hello, ${currentUser.username} (${currentUser.role})`;

    // Apply Role-Based Access Control (RBAC)
    const adminElements = document.querySelectorAll('.admin-only');
    if (currentUser.role === 'teacher' || currentUser.role === 'admin') {
        adminElements.forEach(el => el.classList.remove('hidden'));
        addTestCase(); // Prepare manual builder if teacher
        loadAllProblemsForAssign();
    } else {
        adminElements.forEach(el => el.classList.add('hidden'));
    }
    
    switchTab('tab-overview');
    loadClassrooms();
    loadLeaderboardClassrooms();
}

function switchTab(targetId) {
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('block');
    });
    const targetEl = document.getElementById(targetId);
    targetEl.classList.remove('hidden');
    targetEl.classList.add('block');

    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.target === targetId) {
            btn.classList.add('bg-slate-900');
            btn.classList.remove('hover:bg-slate-700');
        } else {
            btn.classList.remove('bg-slate-900');
            btn.classList.add('hover:bg-slate-700');
        }
    });
}

async function loadClassrooms() {
    try {
        const res = await fetch(`${API_URL}/users/me/classrooms`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        const data = await res.json();
        const classSelect = document.getElementById('select-class');
        if (classSelect && data.classrooms) {
            classSelect.innerHTML = '<option value="">-- Select Class --</option>' + 
                data.classrooms.map(c => `<option value="${c.class_id}">${c.class_name}</option>`).join('');
            classSelect.onchange = (e) => loadProblemsets(e.target.value);
        }
    } catch (err) { console.error("Error loading classrooms", err); }
}

async function loadProblemsets(classId) {
    const setSelect = document.getElementById('select-problemset');
    const probList = document.getElementById('list-problem');
    if (!classId) {
        if (setSelect) setSelect.innerHTML = '<option value="">-- Select Problemset --</option>';
        if (probList) probList.innerHTML = '<div class="p-2 text-gray-500 text-sm">Please select a class first.</div>';
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/classrooms/${classId}/problemsets`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        const data = await res.json();
        if (setSelect && data.problemsets) {
            setSelect.innerHTML = '<option value="">-- Select Problemset --</option>' + 
                data.problemsets.map(p => `<option value="${p.problemset_id}">${p.title}</option>`).join('');
            setSelect.onchange = (e) => loadProblems(e.target.value);
            if (probList) probList.innerHTML = '<div class="p-2 text-gray-500 text-sm">Please select a problemset first.</div>';
        }
    } catch (err) { console.error("Error loading problemsets", err); }
}

async function loadProblems(setId) {
    const probList = document.getElementById('list-problem');
    const descBox = document.getElementById('problem-description');
    if (descBox) descBox.innerHTML = '<div class="text-gray-400 italic">Select a problem to view description...</div>';
    
    let hiddenProbId = document.getElementById('submit-prob-id');
    if (hiddenProbId) hiddenProbId.value = '';

    if (!setId) {
        if (probList) probList.innerHTML = '<div class="p-2 text-gray-500 text-sm">Please select a problemset first.</div>';
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/problemsets/${setId}/problems`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        const data = await res.json();
        if (probList && data.problems) {
            if (data.problems.length === 0) {
                probList.innerHTML = '<div class="p-2 text-gray-500 text-sm">No problems found.</div>';
                return;
            }
            probList.innerHTML = data.problems.map(p => 
                `<div class="p-3 mb-2 border rounded cursor-pointer transition-colors hover:bg-blue-50 text-sm font-semibold text-gray-700" 
                      onclick="selectProblem('${p.problem_id}', this)">
                    📄 ${p.title}
                </div>`
            ).join('');
        }
    } catch (err) { console.error("Error loading problems", err); }
}

async function selectProblem(probId, element) {
    // 1. Highlight currently selected problem in the list
    const listItems = document.getElementById('list-problem').children;
    for (let item of listItems) {
        item.classList.remove('bg-blue-100', 'border-blue-500', 'text-blue-800');
        item.classList.add('hover:bg-blue-50');
    }
    element.classList.remove('hover:bg-blue-50');
    element.classList.add('bg-blue-100', 'border-blue-500', 'text-blue-800');

    // 2. Save problem ID dynamically to a hidden field for Submission
    let hiddenProbId = document.getElementById('submit-prob-id');
    if (!hiddenProbId) {
        hiddenProbId = document.createElement('input');
        hiddenProbId.type = 'hidden';
        hiddenProbId.id = 'submit-prob-id';
        document.body.appendChild(hiddenProbId);
    }
    hiddenProbId.value = probId;

    // 3. Fetch Problem Details (Description & Constraints)
    const descBox = document.getElementById('problem-description');
    if (descBox) {
        descBox.innerHTML = '<div class="animate-pulse text-blue-500 font-bold">Loading description...</div>';
        try {
            const res = await fetch(`${API_URL}/problems/${probId}`, {
                headers: { 'Authorization': `Bearer ${currentUser.token}` }
            });
            const data = await res.json();
            if (res.ok) {
                descBox.innerHTML = `
                    <h2 class="text-2xl font-bold mb-4 text-slate-800 border-b pb-2">${data.title}</h2>
                    <div class="prose max-w-none text-slate-800 mb-6">${data.description}</div>
                    <div class="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-md text-sm text-slate-700">
                        <p><span class="font-bold">Time Limit:</span> Python (${data.time_limits.python}s), C++ (${data.time_limits.cpp}s)</p>
                        <p><span class="font-bold">Memory Limit:</span> Python (${data.mem_limits.python}MB), C++ (${data.mem_limits.cpp}MB)</p>
                    </div>
                `;
            } else {
                descBox.innerHTML = `<div class="text-red-500">Error: ${data.detail}</div>`;
            }
        } catch(err) {
            descBox.innerHTML = `<div class="text-red-500">Network Error: ${err}</div>`;
        }
    }
}

// ================= CODE SUBMISSION & POLLING =================
async function submitSolution() {
    const probId = document.getElementById('submit-prob-id')?.value;
    const setId = document.getElementById('select-problemset')?.value || document.getElementById('submit-set-id')?.value;
    
    if (!probId || !setId) return alert("Please select a problem and a problemset.");

    const lang = document.getElementById('submit-lang').value;
    const code = document.getElementById('submit-code').value;
    const logBox = document.getElementById('submit-log');

    logBox.innerText = 'Queuing submission...';
    
    try {
        const res = await fetch(`${API_URL}/problems/${probId}/submit`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ source_code: code, language: lang, problemset_id: setId })
        });
        const data = await res.json();
        
        if (res.ok) {
            pollResult(data.submission_id);
        } else {
            logBox.innerText = `Error: ${data.detail}`;
        }
    } catch (err) { logBox.innerText = `Network error: ${err}`; }
}

async function pollResult(submissionId) {
    const logBox = document.getElementById('submit-log');
    try {
        const res = await fetch(`${API_URL}/submissions/${submissionId}`);
        const data = await res.json();
        
        if (data.verdict === "Pending") {
            logBox.innerText = `⏳ Executing in Sandbox...\nSubmission ID: ${submissionId}`;
            setTimeout(() => pollResult(submissionId), 2000);
        } else {
            logBox.innerText = `🏁 FINISHED!\nVerdict: ${data.verdict}\nExecution Time: ${data.execution_time}s\nPassed: ${data.passed_cases}/${data.total_cases}`;
            
            // Auto refresh leaderboard
            const submittedSetId = document.getElementById('select-problemset')?.value || document.getElementById('submit-set-id')?.value;
            const lbSetIdInput = document.getElementById('lb-set-id');
            if (lbSetIdInput && submittedSetId) {
                lbSetIdInput.value = submittedSetId;
            }
            fetchLeaderboard();
        }
    } catch (err) {
        logBox.innerText = `Polling error: ${err}`;
    }
}

// ================= LEADERBOARD DROPDOWNS =================
async function loadLeaderboardClassrooms() {
    try {
        const res = await fetch(`${API_URL}/users/me/classrooms`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        const data = await res.json();
        const classSelect = document.getElementById('lb-select-class');
        if (classSelect && data.classrooms) {
            classSelect.innerHTML = '<option value="">-- Select Class --</option>' + 
                data.classrooms.map(c => `<option value="${c.class_id}">${c.class_name}</option>`).join('');
            classSelect.onchange = (e) => loadLeaderboardProblemsets(e.target.value);
        }
    } catch (err) { console.error("Error loading LB classrooms", err); }
}

async function loadLeaderboardProblemsets(classId) {
    const setSelect = document.getElementById('lb-select-set');
    if (!classId) {
        if (setSelect) setSelect.innerHTML = '<option value="">-- Select Problemset --</option>';
        document.getElementById('lb-results').innerHTML = '';
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/classrooms/${classId}/problemsets`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        const data = await res.json();
        if (setSelect && data.problemsets) {
            setSelect.innerHTML = '<option value="">-- Select Problemset --</option>' + 
                data.problemsets.map(p => `<option value="${p.problemset_id}">${p.title}</option>`).join('');
            setSelect.onchange = () => fetchLeaderboard();
        }
    } catch (err) { console.error("Error loading LB problemsets", err); }
}

// ================= LEADERBOARD =================
async function fetchLeaderboard() {
    const setId = document.getElementById('lb-select-set')?.value || document.getElementById('lb-set-id')?.value;
    const resultBox = document.getElementById('lb-results');
    if (!setId) return;
    
    try {
        const res = await fetch(`${API_URL}/problemsets/${setId}/leaderboard`);
        const data = await res.json();
        if (res.ok) {
            resultBox.innerHTML = data.leaderboard.map(u => 
                `<div class="p-3 bg-gray-50 border rounded flex justify-between">
                    <span class="font-bold">#${u.rank} ${u.username}</span>
                    <span class="text-blue-600 font-bold">${u.score} pts</span>
                </div>`
            ).join('');
        } else {
            resultBox.innerText = `Error: ${data.detail}`;
        }
    } catch (err) { resultBox.innerText = `Network error: ${err}`; }
}

// ================= PROBLEM CREATION (TEACHER ONLY) =================
function switchProblemMode(mode) {
    currentProblemMode = mode;
    const btnManual = document.getElementById('btn-mode-manual');
    const btnZip = document.getElementById('btn-mode-zip');
    const divManual = document.getElementById('mode-manual');
    const divZip = document.getElementById('mode-zip');

    if (mode === 'manual') {
        btnManual.className = "px-4 py-2 bg-white shadow-sm rounded-md text-sm font-bold text-slate-800";
        btnZip.className = "px-4 py-2 rounded-md text-sm font-bold text-gray-500 hover:text-slate-800";
        divManual.classList.remove('hidden'); divManual.classList.add('block');
        divZip.classList.add('hidden'); divZip.classList.remove('block');
    } else {
        btnZip.className = "px-4 py-2 bg-white shadow-sm rounded-md text-sm font-bold text-slate-800";
        btnManual.className = "px-4 py-2 rounded-md text-sm font-bold text-gray-500 hover:text-slate-800";
        divZip.classList.remove('hidden'); divZip.classList.add('block');
        divManual.classList.add('hidden'); divManual.classList.remove('block');
    }
}

function addTestCase() {
    tcCounter++;
    const wrapper = document.getElementById('testcases-wrapper');
    const div = document.createElement('div');
    div.className = "bg-gray-50 p-4 border border-gray-200 rounded";
    div.id = `tc-block-${tcCounter}`;
    div.innerHTML = `
        <div class="flex justify-between items-center mb-2">
            <span class="font-bold text-gray-700">Case #${tcCounter}</span>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <textarea id="in_${tcCounter}" class="w-full h-20 border rounded p-2 font-mono text-sm" placeholder="Input"></textarea>
            <textarea id="out_${tcCounter}" class="w-full h-20 border rounded p-2 font-mono text-sm" placeholder="Expected Output"></textarea>
        </div>
        <div class="mt-2 flex items-center">
            <input type="checkbox" id="hidden_${tcCounter}" class="mr-2 cursor-pointer w-4 h-4">
            <label class="text-sm text-gray-600">Hidden Test Case</label>
        </div>
    `;
    wrapper.appendChild(div);
}

function handleZipSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedZipFile = file;
        document.getElementById('zip-file-name').innerText = `Selected File: ${file.name}`;
    }
}

async function submitManualProblem() {
    const title = document.getElementById('prob-title').value;
    const pyTime = document.getElementById('time-python').value;
    const cppTime = document.getElementById('time-cpp').value;
    const desc = quillEditor.root.innerHTML;
    
    const testCases = [];
    document.getElementById('testcases-wrapper').querySelectorAll('[id^="tc-block-"]').forEach(block => {
        const idStr = block.id.split('-')[2]; 
        const inVal = document.getElementById(`in_${idStr}`).value;
        const outVal = document.getElementById(`out_${idStr}`).value;
        const isHidden = document.getElementById(`hidden_${idStr}`).checked;
        if (inVal || outVal) testCases.push({ input: inVal, output: outVal, hidden: isHidden });
    });

    const payload = {
        title: title,
        description: desc,
        allowed_langs: ["python", "cpp"],
        time_limits: { "python": parseFloat(pyTime), "cpp": parseFloat(cppTime) },
        mem_limits: { "python": 512, "cpp": 256 },
        test_cases: testCases
    };

    try {
        const res = await fetch(`${API_URL}/problems/create/manual`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(res.ok ? `Success! Problem ID: ${data.problem_id}` : `Error: ${data.detail}`);
    } catch (err) { alert(`Network error: ${err}`); }
}

async function submitZipProblem() {
    if (!selectedZipFile) return alert("Select a ZIP file first!");
    const formData = new FormData();
    formData.append('file', selectedZipFile);
    
    try {
        const res = await fetch(`${API_URL}/problems/create/zip`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${currentUser.token}` },
            body: formData
        });
        const data = await res.json();
        alert(res.ok ? `Success! Problem ID: ${data.problem_id}` : `Error: ${data.detail}`);
    } catch (err) { alert(`Network error: ${err}`); }
}

// ================= ASSIGN PROBLEMS (TEACHER ONLY) =================
// 1. Lái dropdown Class từ bên mục Submit qua mục Assign
const originalLoadClassrooms = loadClassrooms;
loadClassrooms = async function() {
    await originalLoadClassrooms();
    try {
        const res = await fetch(`${API_URL}/users/me/classrooms`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const data = await res.json();
        const assignClassSelect = document.getElementById('assign-class');
        if (assignClassSelect && data.classrooms && (currentUser.role === 'teacher' || currentUser.role === 'admin')) {
            assignClassSelect.innerHTML = '<option value="">-- Select Class --</option>' + 
                data.classrooms.map(c => `<option value="${c.class_id}">${c.class_name}</option>`).join('');
        }
    } catch (err) {}
}

async function loadAssignProblemsets(classId) {
    const setSelect = document.getElementById('assign-problemset');
    const box = document.getElementById('current-problems-box');
    if (!classId) {
        setSelect.innerHTML = '<option value="">-- Select Problemset --</option>';
        box.classList.add('hidden');
        return;
    }
    try {
        const res = await fetch(`${API_URL}/classrooms/${classId}/problemsets`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const data = await res.json();
        setSelect.innerHTML = '<option value="">-- Select Problemset --</option>' + 
            data.problemsets.map(p => `<option value="${p.problemset_id}">${p.title}</option>`).join('');
    } catch (err) { console.error(err); }
}

async function loadCurrentAssignedProblems(setId) {
    const box = document.getElementById('current-problems-box');
    const list = document.getElementById('current-problems-list');
    if (!setId) { box.classList.add('hidden'); return; }
    
    try {
        const res = await fetch(`${API_URL}/problemsets/${setId}/problems`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const data = await res.json();
        if (data.problems && data.problems.length > 0) {
            list.innerHTML = data.problems.map(p => `<li>${p.title}</li>`).join('');
            box.classList.remove('hidden');
        } else {
            list.innerHTML = '<li class="italic text-gray-500">No problems assigned yet.</li>';
            box.classList.remove('hidden');
        }
    } catch (err) { console.error(err); }
}

async function loadAllProblemsForAssign() {
    try {
        const res = await fetch(`${API_URL}/problems`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const data = await res.json();
        const list = document.getElementById('all-problems-list');
        if (data.problems) {
            list.innerHTML = data.problems.map(p => `
                <label class="flex items-center p-3 bg-white border rounded cursor-pointer hover:bg-blue-50 transition shadow-sm">
                    <input type="checkbox" value="${p.problem_id}" class="assign-prob-checkbox w-4 h-4 text-blue-600 rounded mr-3 cursor-pointer">
                    <span class="font-semibold text-sm text-gray-700 flex-grow">${p.title}</span>
                    <span class="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-1 rounded">${p.problem_id.substring(0, 10)}...</span>
                </label>
            `).join('');
        }
    } catch (err) { console.error(err); }
}

async function submitAssignProblems() {
    const setId = document.getElementById('assign-problemset').value;
    if (!setId) return alert("Please select a problemset first!");
    
    const checkboxes = document.querySelectorAll('.assign-prob-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);
    
    if (selectedIds.length === 0) return alert("Please select at least one problem to add!");
    
    try {
        const res = await fetch(`${API_URL}/problemsets/${setId}/assign`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ problem_ids: selectedIds })
        });
        const data = await res.json();
        if (res.ok) {
            // Uncheck boxes and reload UI
            checkboxes.forEach(cb => cb.checked = false);
            loadCurrentAssignedProblems(setId);
            alert("✅ Problems added successfully!");
        } else {
            alert(`❌ Error: ${data.detail}`);
        }
    } catch (err) { alert(`Network error: ${err}`); }
}