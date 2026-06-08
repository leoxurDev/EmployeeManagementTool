// Employee Shift Hub - Kiosk & Dashboard Controls

document.addEventListener('DOMContentLoaded', () => {
    // Canvas setup for Star/Circle particles
    initConfetti();

    // Employee Roster Grid Listeners
    initEmployeeGrid();

    // Manager Dashboard Controls
    initManagerDashboard();

    // Unified Login Page Controller
    initUnifiedLogin();

    // Developer Page Layout Builder and AI Assistant
    initDeveloperPage();
});

// --- State Variables ---
let currentSelectedEmployeeId = null;
let currentSelectedWorkMode = 'office';
let currentPIN = '';

// --- Employee Grid Controller ---
function initEmployeeGrid() {
    const empCards = document.querySelectorAll('.kid-card');
    const modal = document.getElementById('checkin-modal');
    
    // Screens
    const pinScreen = document.getElementById('pin-screen-container');
    const moodScreen = document.getElementById('mood-screen-container'); // Screen 2: checkin/checkout/done screen
    
    // Modal buttons
    const closeBtn = document.getElementById('modal-close-btn');
    const pinCloseBtn = document.getElementById('pin-modal-close-btn');
    const submitBtn = document.getElementById('modal-submit-btn');
    
    // Names/Welcome text
    const welcomeText = document.getElementById('modal-welcome-text');
    const pinWelcomeText = document.getElementById('pin-modal-welcome-text');
    
    // Elements for PIN
    const pinDots = document.querySelectorAll('.pin-dot');
    const pinErrorMsg = document.getElementById('pin-error-msg');
    const keypadButtons = document.querySelectorAll('.keypad-btn');
    
    // Work Mode Options
    const workModeButtons = document.querySelectorAll('.mood-option-btn');

    if (!modal) return; // Not on kiosk grid screen

    function resetPINState() {
        currentPIN = '';
        pinDots.forEach(dot => dot.classList.remove('active'));
        if (pinErrorMsg) pinErrorMsg.classList.remove('show');
    }

    function showPINScreen() {
        if (pinScreen) pinScreen.style.display = 'block';
        if (moodScreen) moodScreen.style.display = 'none';
        resetPINState();
    }

    // Opening Check-in dialog
    empCards.forEach(card => {
        card.addEventListener('click', () => {
            const empName = card.getAttribute('data-name');
            currentSelectedEmployeeId = card.getAttribute('data-id');
            
            if (pinWelcomeText) pinWelcomeText.textContent = `Hi, ${empName}! 👋`;
            if (welcomeText) welcomeText.textContent = `Hi, ${empName}! 👋`;
            
            // Set default work mode styling
            workModeButtons.forEach(btn => btn.classList.remove('selected'));
            const defaultModeBtn = document.querySelector('.mood-option-btn[data-mood="office"]');
            if (defaultModeBtn) defaultModeBtn.classList.add('selected');
            currentSelectedWorkMode = 'office';

            showPINScreen();
            modal.classList.add('active');
        });
    });

    // Keypad interaction
    keypadButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const val = btn.getAttribute('data-val');
            const action = btn.getAttribute('data-action');

            if (val !== null) {
                if (currentPIN.length < 4) {
                    currentPIN += val;
                    updatePINDots();
                    if (currentPIN.length === 4) {
                        verifyPINCode();
                    }
                }
            } else if (action === 'clear') {
                resetPINState();
            } else if (action === 'backspace') {
                if (currentPIN.length > 0) {
                    currentPIN = currentPIN.slice(0, -1);
                    updatePINDots();
                }
            }
        });
    });

    function updatePINDots() {
        pinDots.forEach((dot, index) => {
            if (index < currentPIN.length) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    function verifyPINCode() {
        const formData = new FormData();
        formData.append('student_id', currentSelectedEmployeeId);
        formData.append('pin_code', currentPIN);

        fetch(VERIFY_PIN_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Transition to details/work mode selector screen
                if (pinScreen) pinScreen.style.display = 'none';
                if (moodScreen) moodScreen.style.display = 'block';
                
                // Configure Screen 2 based on employee state
                const modeSelectGrid = document.querySelector('.mood-selection-grid');
                const welcomeSub = document.querySelector('#mood-screen-container .modal-header-section p');
                
                if (data.state === 'not_checked_in') {
                    welcomeSub.innerHTML = `Scheduled Roster: <strong>${data.rostered_shift}</strong><br>Select your Work Mode to Check In:`;
                    if (modeSelectGrid) modeSelectGrid.style.display = 'grid';
                    if (submitBtn) {
                        submitBtn.textContent = '📥 Check In';
                        submitBtn.setAttribute('data-action', 'check_in');
                        submitBtn.style.display = 'inline-flex';
                    }
                } else if (data.state === 'checked_in') {
                    welcomeSub.innerHTML = `You checked in at <strong>${data.check_in_time}</strong>.<br>Ready to complete your shift?`;
                    if (modeSelectGrid) modeSelectGrid.style.display = 'none';
                    if (submitBtn) {
                        submitBtn.textContent = '📤 Check Out';
                        submitBtn.setAttribute('data-action', 'check_out');
                        submitBtn.style.display = 'inline-flex';
                    }
                } else {
                    welcomeSub.innerHTML = `Shift Completed! 🎉<br>Check-in: ${data.check_in_time}<br>Check-out: ${data.check_out_time}<br>Total Hours Worked: <strong>${data.hours_worked} hrs</strong>`;
                    if (modeSelectGrid) modeSelectGrid.style.display = 'none';
                    if (submitBtn) {
                        submitBtn.style.display = 'none'; // Only Close is needed
                    }
                }
            } else {
                if (pinScreen) {
                    pinScreen.classList.add('shake');
                    if (pinErrorMsg) {
                        pinErrorMsg.textContent = data.error || 'Wrong PIN! 🤫';
                        pinErrorMsg.classList.add('show');
                    }
                    setTimeout(() => {
                        pinScreen.classList.remove('shake');
                    }, 500);
                }
                resetPINState();
            }
        })
        .catch(err => {
            console.error("PIN verification error:", err);
            resetPINState();
        });
    }

    // Work Mode selection
    workModeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            workModeButtons.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            currentSelectedWorkMode = btn.getAttribute('data-mood');
        });
    });

    const closeAllModals = () => {
        modal.classList.remove('active');
        currentSelectedEmployeeId = null;
        resetPINState();
    };

    if (closeBtn) closeBtn.addEventListener('click', closeAllModals);
    if (pinCloseBtn) pinCloseBtn.addEventListener('click', closeAllModals);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAllModals();
        }
    });

    // Check-in / check-out submit handler
    submitBtn.addEventListener('click', () => {
        if (!currentSelectedEmployeeId) return;
        const action = submitBtn.getAttribute('data-action');

        const formData = new FormData();
        formData.append('student_id', currentSelectedEmployeeId);
        formData.append('action', action);
        formData.append('mood', currentSelectedWorkMode); // mapped to work_mode in views

        fetch(TOGGLE_ATTENDANCE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.kid-card[data-id="${currentSelectedEmployeeId}"]`);
                if (card) {
                    if (action === 'check_out') {
                        card.classList.add('checked-in'); // Keep styled as completed
                        card.classList.remove('checked-in-late');
                        card.querySelector('.status-indicator-badge').textContent = '✅';
                        card.querySelector('.kid-status-text').innerHTML = `
                            Completed Shift <br>
                            Out: ${data.time} (Hours: ${data.hours_worked})
                        `;
                    } else {
                        if (data.status === 'late') {
                            card.classList.add('checked-in-late');
                        } else {
                            card.classList.add('checked-in');
                        }
                        
                        const modeEmoji = data.mood_emoji || '🏢';
                        card.querySelector('.status-indicator-badge').textContent = modeEmoji;
                        const lateLabel = data.status === 'late' ? ' (Late)' : '';
                        card.querySelector('.kid-status-text').innerHTML = `
                            In${lateLabel} at ${data.time} <br>
                            Mode: ${modeEmoji} ${data.mood.charAt(0).toUpperCase() + data.mood.slice(1)}
                        `;
                        
                        // Burst particles celebrating check-in
                        const rect = card.getBoundingClientRect();
                        triggerConfetti(rect.left + rect.width / 2, rect.top + rect.height / 2);
                    }
                    
                    recalculateGridStats();
                }
            } else {
                console.error("Action failure:", data.error);
            }
            closeAllModals();
        })
        .catch(err => {
            console.error("Fetch attendance toggle failure:", err);
            closeAllModals();
        });
    });
}

function recalculateGridStats() {
    const totalCards = document.querySelectorAll('.kid-card').length;
    const checkedInCount = document.querySelectorAll('.kid-card.checked-in, .kid-card.checked-in-late').length;
    const rate = totalCards > 0 ? Math.round((checkedInCount / totalCards) * 100) : 0;

    const statsHerePill = document.querySelector('.stats-cloud-banner .stat-pill:nth-child(2) strong');
    if (statsHerePill) statsHerePill.textContent = checkedInCount;

    const fillBar = document.querySelector('.progress-bar-fill');
    if (fillBar) fillBar.style.width = `${rate}%`;

    const percentText = document.querySelector('.progress-percent-text');
    if (percentText) percentText.textContent = `${rate}% Present`;
}

// --- Manager Dashboard Controller ---
function initManagerDashboard() {
    const actionBtns = document.querySelectorAll('.status-action-btn');

    actionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const empId = btn.getAttribute('data-student');
            const status = btn.getAttribute('data-status');
            
            const formData = new FormData();
            formData.append('student_id', empId);
            formData.append('action', status === 'absent' ? 'check_out' : 'check_in');
            formData.append('status', status);

            fetch(TOGGLE_ATTENDANCE_URL, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const empButtons = document.querySelectorAll(`.status-action-btn[data-student="${empId}"]`);
                    empButtons.forEach(b => {
                        if (b.getAttribute('data-status') === status) {
                            b.classList.add('active');
                        } else {
                            b.classList.remove('active');
                        }
                    });

                    const timeCells = document.querySelectorAll(`[data-student-id="${empId}"] .checked-time-cell`);
                    timeCells.forEach(cell => {
                        cell.textContent = (status !== 'absent') ? data.time : '-';
                    });

                    const moodCells = document.querySelectorAll(`[data-student-id="${empId}"] .mood-cell`);
                    moodCells.forEach(cell => {
                        cell.textContent = (status !== 'absent' && data.mood_emoji) ? `${data.mood.charAt(0).toUpperCase() + data.mood.slice(1)} ${data.mood_emoji}` : '-';
                    });

                    if (status === 'present') {
                        const rect = btn.getBoundingClientRect();
                        triggerConfetti(rect.left + rect.width / 2, rect.top + rect.height / 2);
                    }

                    recalculateManagerStats();
                }
            })
            .catch(err => console.error("Manager attendance update failed:", err));
        });
    });

    const gridBtn = document.getElementById('view-grid-btn');
    const listBtn = document.getElementById('view-list-btn');
    const gridView = document.getElementById('roster-grid-view');
    const listView = document.getElementById('roster-list-view');

    function activateGridView() {
        if (!gridBtn) return;
        gridBtn.classList.add('active');
        gridBtn.style.background = '#2563eb';
        gridBtn.style.color = '#ffffff';
        if (listBtn) {
            listBtn.classList.remove('active');
            listBtn.style.background = 'transparent';
            listBtn.style.color = '#64748b';
        }
        if (gridView) gridView.style.display = 'grid';
        if (listView) listView.style.display = 'none';
        localStorage.setItem('managerDashView', 'grid');
    }

    function activateListView() {
        if (!listBtn) return;
        listBtn.classList.add('active');
        listBtn.style.background = '#2563eb';
        listBtn.style.color = '#ffffff';
        if (gridBtn) {
            gridBtn.classList.remove('active');
            gridBtn.style.background = 'transparent';
            gridBtn.style.color = '#64748b';
        }
        if (listView) listView.style.display = 'block';
        if (gridView) gridView.style.display = 'none';
        localStorage.setItem('managerDashView', 'list');
    }

    if (gridBtn && listBtn) {
        gridBtn.addEventListener('click', activateGridView);
        listBtn.addEventListener('click', activateListView);

        const savedView = localStorage.getItem('managerDashView');
        if (savedView === 'list') {
            activateListView();
        } else {
            activateGridView();
        }
    }

    const pinToggleBtns = document.querySelectorAll('.pin-toggle-btn');
    pinToggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const container = btn.parentElement;
            if (container) {
                const hiddenDigits = container.querySelector('.pin-digits-hidden');
                const shownDigits = container.querySelector('.pin-digits-shown');
                
                if (hiddenDigits && shownDigits) {
                    if (hiddenDigits.style.display === 'none') {
                        hiddenDigits.style.display = 'inline';
                        shownDigits.style.display = 'none';
                        btn.textContent = '👁️';
                    } else {
                        hiddenDigits.style.display = 'none';
                        shownDigits.style.display = 'inline';
                        btn.textContent = '🙈';
                    }
                }
            }
        });
    });
}

function recalculateManagerStats() {
    const empIdSet = new Set();
    document.querySelectorAll('[data-student-id]').forEach(el => {
        const eid = el.getAttribute('data-student-id');
        if (eid) empIdSet.add(eid);
    });
    const totalEmployees = empIdSet.size;

    let presentCount = 0;
    let lateCount = 0;
    let absentCount = 0;

    empIdSet.forEach(eid => {
        const activeBtn = document.querySelector(`.status-action-btn.active[data-student="${eid}"]`);
        if (activeBtn) {
            const status = activeBtn.getAttribute('data-status');
            if (status === 'present') presentCount++;
            else if (status === 'late') lateCount++;
            else absentCount++;
        } else {
            absentCount++;
        }
    });

    const rate = totalEmployees > 0 ? Math.round(((presentCount + lateCount) / totalEmployees) * 100) : 0;

    const presentVal = document.querySelector('.mini-stat-card.present .value');
    if (presentVal) presentVal.textContent = presentCount;

    const lateVal = document.querySelector('.mini-stat-card.late .value');
    if (lateVal) lateVal.textContent = lateCount;

    const absentVal = document.querySelector('.mini-stat-card.absent .value');
    if (absentVal) absentVal.textContent = absentCount;

    const rateVal = document.querySelector('.mini-stat-card.rate .value');
    if (rateVal) rateVal.textContent = `${rate}%`;
}

// --- Confetti particle engine ---
let canvas = null;
let ctx = null;
let particles = [];
let animationId = null;

function initConfetti() {
    canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;

    ctx = canvas.getContext('2d');
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();
}

class KidParticle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 8 + 6;
        this.speedX = Math.random() * 10 - 5;
        this.speedY = Math.random() * -12 - 4;
        this.gravity = 0.4;
        
        // Professional corporate brand colors
        this.colors = ['#3b82f6', '#10b981', '#60a5fa', '#34d399', '#bfdbfe', '#a7f3d0', '#6366f1'];
        this.color = this.colors[Math.floor(Math.random() * this.colors.length)];
        
        this.type = Math.random() > 0.5 ? 'star' : 'circle';
        this.rotation = Math.random() * 360;
        this.rotationSpeed = Math.random() * 10 - 5;
        this.opacity = 1;
        this.fade = Math.random() * 0.015 + 0.01;
    }
    update() {
        this.x += this.speedX;
        this.speedY += this.gravity;
        this.y += this.speedY;
        this.rotation += this.rotationSpeed;
        this.opacity -= this.fade;
    }
    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.fillStyle = this.color;
        ctx.globalAlpha = this.opacity;
        
        if (this.type === 'star') {
            ctx.beginPath();
            for (let i = 0; i < 5; i++) {
                ctx.lineTo(Math.cos((18 + i * 72) * Math.PI / 180) * this.size,
                           Math.sin((18 + i * 72) * Math.PI / 180) * this.size);
                ctx.lineTo(Math.cos((54 + i * 72) * Math.PI / 180) * (this.size / 2),
                           Math.sin((54 + i * 72) * Math.PI / 180) * (this.size / 2));
            }
            ctx.closePath();
            ctx.fill();
        } else {
            ctx.beginPath();
            ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    }
}

function triggerConfetti(x, y) {
    if (!canvas) return;
    
    for (let i = 0; i < 35; i++) {
        particles.push(new KidParticle(x, y));
    }
    if (!animationId) {
        animateParticles();
    }
}

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles = particles.filter(p => p.opacity > 0);
    
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    
    if (particles.length > 0) {
        animationId = requestAnimationFrame(animateParticles);
    } else {
        animationId = null;
    }
}

// --- Unified Login Controller ---
function initUnifiedLogin() {
    const tabStudent = document.getElementById('tab-student');
    const tabTeacher = document.getElementById('tab-teacher');
    const studentSection = document.getElementById('student-login-section');
    const teacherSection = document.getElementById('teacher-login-section');
    const slider = document.querySelector('.login-tab-slider');

    if (!tabStudent || !tabTeacher) return;

    // Tab Switching Logic
    tabStudent.addEventListener('click', () => {
        tabStudent.classList.add('active');
        tabTeacher.classList.remove('active');
        if (slider) slider.style.left = '0.35rem';
        if (studentSection) studentSection.style.display = 'block';
        if (teacherSection) teacherSection.style.display = 'none';
    });

    tabTeacher.addEventListener('click', () => {
        tabTeacher.classList.add('active');
        tabStudent.classList.remove('active');
        if (slider) slider.style.left = 'calc(50% - 0.35rem)';
        if (teacherSection) teacherSection.style.display = 'block';
        if (studentSection) studentSection.style.display = 'none';
    });

    let selectedEmployeeId = null;
    let selectedEmployeeName = '';
    let selectedEmployeeEmoji = '💼';
    let selectedEmployeeColor = '#A0C4FF';
    let selectedWorkMode = 'office';
    let pinBuffer = '';

    const empSelect = document.getElementById('student-select');
    const selectGroup = document.getElementById('student-select-group');
    const keypadContainer = document.getElementById('student-keypad-container');
    const moodContainer = document.getElementById('student-mood-container');
    const successContainer = document.getElementById('student-success-container');
    const moodWelcomeText = document.getElementById('student-mood-welcome');
    const pinDots = document.querySelectorAll('#student-keypad-container .pin-dot');
    const pinErrorMsg = document.getElementById('student-pin-error-msg');
    const keypadButtons = document.querySelectorAll('.keypad-btn.student-key');
    const workModeButtons = document.querySelectorAll('#student-mood-container .mood-option-btn');
    const submitBtn = document.getElementById('student-submit-checkin');
    const resetBtn = document.getElementById('student-reset-btn');

    function resetStudentPIN() {
        pinBuffer = '';
        pinDots.forEach(dot => dot.classList.remove('active'));
        if (pinErrorMsg) pinErrorMsg.classList.remove('show');
    }

    empSelect.addEventListener('change', () => {
        const option = empSelect.options[empSelect.selectedIndex];
        selectedEmployeeId = empSelect.value;
        selectedEmployeeName = option.getAttribute('data-name');
        selectedEmployeeEmoji = option.getAttribute('data-emoji') || '💼';
        selectedEmployeeColor = option.getAttribute('data-color') || '#A0C4FF';

        resetStudentPIN();
        if (keypadContainer) keypadContainer.style.display = 'block';
        if (moodContainer) moodContainer.style.display = 'none';
        if (successContainer) successContainer.style.display = 'none';
    });

    keypadButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!selectedEmployeeId) return;

            const val = btn.getAttribute('data-val');
            const action = btn.getAttribute('data-action');

            if (val !== null) {
                if (pinBuffer.length < 4) {
                    pinBuffer += val;
                    updateDots();
                    if (pinBuffer.length === 4) {
                        verifyStudentPIN();
                    }
                }
            } else if (action === 'clear') {
                resetStudentPIN();
            } else if (action === 'backspace') {
                if (pinBuffer.length > 0) {
                    pinBuffer = pinBuffer.slice(0, -1);
                    updateDots();
                }
            }
        });
    });

    function updateDots() {
        pinDots.forEach((dot, idx) => {
            if (idx < pinBuffer.length) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    function verifyStudentPIN() {
        const formData = new FormData();
        formData.append('student_id', selectedEmployeeId);
        formData.append('pin_code', pinBuffer);

        fetch(VERIFY_PIN_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (selectGroup) selectGroup.style.display = 'none';
                if (keypadContainer) keypadContainer.style.display = 'none';
                
                const selectTitle = document.querySelector('#student-mood-container .modal-header-section p');
                
                if (data.state === 'not_checked_in') {
                    if (moodWelcomeText) moodWelcomeText.textContent = `Hi, ${selectedEmployeeName}! 👋`;
                    if (selectTitle) selectTitle.innerHTML = `Scheduled: <strong>${data.rostered_shift}</strong><br>Select your Work Mode to Check In:`;
                    workModeButtons.forEach(b => b.classList.remove('selected'));
                    const defaultModeBtn = document.querySelector('#student-mood-container .mood-option-btn[data-mood="office"]');
                    if (defaultModeBtn) defaultModeBtn.classList.add('selected');
                    selectedWorkMode = 'office';
                    if (submitBtn) {
                        submitBtn.textContent = '📥 Check In';
                        submitBtn.setAttribute('data-action', 'check_in');
                    }
                    if (moodContainer) moodContainer.style.display = 'block';
                } else if (data.state === 'checked_in') {
                    if (moodWelcomeText) moodWelcomeText.textContent = `Hi, ${selectedEmployeeName}! 👋`;
                    if (selectTitle) selectTitle.innerHTML = `You checked in at <strong>${data.check_in_time}</strong>.<br>Ready to check out and log hours?`;
                    const modeSelectGrid = document.querySelector('#student-mood-container .mood-selection-grid');
                    if (modeSelectGrid) modeSelectGrid.style.display = 'none';
                    if (submitBtn) {
                        submitBtn.textContent = '📤 Check Out';
                        submitBtn.setAttribute('data-action', 'check_out');
                    }
                    if (moodContainer) moodContainer.style.display = 'block';
                } else {
                    // Already checked out
                    if (selectGroup) selectGroup.style.display = 'none';
                    if (keypadContainer) keypadContainer.style.display = 'none';
                    if (moodContainer) moodContainer.style.display = 'none';
                    
                    const successCircle = document.getElementById('student-success-avatar-circle');
                    if (successCircle) {
                        successCircle.textContent = selectedEmployeeEmoji;
                        successCircle.style.backgroundColor = selectedEmployeeColor;
                    }
                    
                    const successMsg = document.getElementById('student-success-msg');
                    if (successMsg) {
                        successMsg.innerHTML = `<strong>${selectedEmployeeName}</strong> is already checked out for today! ✅<br>Total Hours Worked: <strong>${data.hours_worked} hrs</strong>`;
                    }
                    
                    if (successContainer) successContainer.style.display = 'block';
                }
            } else {
                if (keypadContainer) {
                    keypadContainer.classList.add('shake');
                    if (pinErrorMsg) {
                        pinErrorMsg.textContent = data.error || 'Wrong PIN! 🤫';
                        pinErrorMsg.classList.add('show');
                    }
                    setTimeout(() => {
                        keypadContainer.classList.remove('shake');
                    }, 500);
                }
                resetStudentPIN();
            }
        })
        .catch(err => {
            console.error("Unified PIN verification error:", err);
            resetStudentPIN();
        });
    }

    workModeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            workModeButtons.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedWorkMode = btn.getAttribute('data-mood');
        });
    });

    submitBtn.addEventListener('click', () => {
        if (!selectedEmployeeId) return;
        const action = submitBtn.getAttribute('data-action');

        const formData = new FormData();
        formData.append('student_id', selectedEmployeeId);
        formData.append('action', action);
        formData.append('mood', selectedWorkMode);

        fetch(TOGGLE_ATTENDANCE_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (moodContainer) moodContainer.style.display = 'none';
                
                const successCircle = document.getElementById('student-success-avatar-circle');
                if (successCircle) {
                    successCircle.textContent = selectedEmployeeEmoji;
                    successCircle.style.backgroundColor = selectedEmployeeColor;
                }
                
                const successMsg = document.getElementById('student-success-msg');
                if (successMsg) {
                    if (action === 'check_in') {
                        const lateLabel = data.status === 'late' ? ' (Late)' : '';
                        successMsg.innerHTML = `<strong>${selectedEmployeeName}</strong> is checked in${lateLabel} at ${data.time}! ✅<br>Work Mode: ${data.mood_emoji} ${selectedWorkMode.charAt(0).toUpperCase() + selectedWorkMode.slice(1)}`;
                    } else {
                        successMsg.innerHTML = `<strong>${selectedEmployeeName}</strong> is checked out at ${data.time}! ✅<br>Shift Completed! Total Hours Worked: <strong>${data.hours_worked} hrs</strong>`;
                    }
                }

                if (successContainer) successContainer.style.display = 'block';
                triggerConfetti(window.innerWidth / 2, window.innerHeight / 2 - 100);
            } else {
                console.error("Unified checkin failed:", data.error);
            }
        })
        .catch(err => console.error("Unified fetch failed:", err));
    });

    resetBtn.addEventListener('click', () => {
        empSelect.value = '';
        if (selectGroup) selectGroup.style.display = 'block';
        if (keypadContainer) keypadContainer.style.display = 'none';
        if (moodContainer) moodContainer.style.display = 'none';
        
        const modeSelectGrid = document.querySelector('#student-mood-container .mood-selection-grid');
        if (modeSelectGrid) modeSelectGrid.style.display = 'grid'; // Reset display state
        
        if (successContainer) successContainer.style.display = 'none';
        resetStudentPIN();
    });
}

// --- Developer Page Controller (Drag & Drop + Gemini AI) ---
function initDeveloperPage() {
    const listContainer = document.getElementById('drag-drop-list');
    const saveBtn = document.getElementById('save-layout-btn');
    const successBanner = document.getElementById('save-success-banner');
    
    const chatInput = document.getElementById('chat-input-text');
    const sendBtn = document.getElementById('chat-send-btn');
    const chatMessages = document.getElementById('ai-chat-messages');
    const apiKeyInput = document.getElementById('gemini-api-key');

    if (!listContainer) return; // Not on developer page

    const draggables = document.querySelectorAll('.draggable-block-item');
    
    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', () => {
            draggable.classList.add('dragging');
        });

        draggable.addEventListener('dragend', () => {
            draggable.classList.remove('dragging');
        });
    });

    listContainer.addEventListener('dragover', e => {
        e.preventDefault();
        const afterElement = getDragAfterElement(listContainer, e.clientY);
        const draggable = document.querySelector('.dragging');
        if (draggable) {
            if (afterElement == null) {
                listContainer.appendChild(draggable);
            } else {
                listContainer.insertBefore(draggable, afterElement);
            }
        }
    });

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.draggable-block-item:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    const checkboxes = document.querySelectorAll('.visibility-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const statusLabel = checkbox.parentElement.nextElementSibling;
            if (statusLabel) {
                if (checkbox.checked) {
                    statusLabel.textContent = 'Visible';
                    statusLabel.style.color = '#10b981';
                } else {
                    statusLabel.textContent = 'Hidden';
                    statusLabel.style.color = '#94a3b8';
                }
            }
        });
    });

    saveBtn.addEventListener('click', () => {
        const blocks = [];
        document.querySelectorAll('.draggable-block-item').forEach((item, index) => {
            blocks.push({
                id: item.getAttribute('data-block-id'),
                order: index + 1,
                is_visible: item.querySelector('.visibility-checkbox').checked
            });
        });

        saveLayoutConfiguration(blocks, () => {
            if (successBanner) {
                successBanner.style.display = 'block';
                setTimeout(() => {
                    successBanner.style.display = 'none';
                }, 3000);
            }
        });
    });

    function saveLayoutConfiguration(blocks, successCallback) {
        fetch('/manager/developer/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ blocks: blocks })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (successCallback) successCallback();
            } else {
                console.error("Save layout failure:", data.error);
                alert("Error saving layout: " + data.error);
            }
        })
        .catch(err => {
            console.error("Fetch save layout failure:", err);
        });
    }

    function scrollChatToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function appendMessageBubble(messageText, isUser = false) {
        const bubble = document.createElement('div');
        bubble.className = isUser ? 'chat-bubble user-bubble' : 'chat-bubble ai-bubble';
        
        if (isUser) {
            bubble.style.cssText = 'background: #e0f2fe; border: 2px solid #bae6fd; border-radius: 18px 18px 4px 18px; padding: 0.8rem 1.2rem; max-width: 85%; align-self: flex-end; font-weight: 600; color: #0369a1; line-height: 1.5; font-size: 0.95rem; box-shadow: 0 4px 6px rgba(0,0,0,0.02);';
        } else {
            bubble.style.cssText = 'background: #eff6ff; border: 2px solid #bfdbfe; border-radius: 18px 18px 18px 4px; padding: 0.8rem 1.2rem; max-width: 85%; align-self: flex-start; font-weight: 600; color: #1e3a8a; line-height: 1.5; font-size: 0.95rem; box-shadow: 0 4px 6px rgba(0,0,0,0.02);';
        }
        
        bubble.innerHTML = messageText;
        if (chatMessages) {
            chatMessages.appendChild(bubble);
            scrollChatToBottom();
        }
        return bubble;
    }

    function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessageBubble(text, true);
        chatInput.value = '';

        const typingBubble = appendMessageBubble('<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', false);

        const apiKey = apiKeyInput.value.trim();

        fetch('/manager/developer/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ message: text, api_key: apiKey })
        })
        .then(res => res.json())
        .then(data => {
            if (chatMessages) {
                chatMessages.removeChild(typingBubble);
            }

            if (data.success) {
                appendMessageBubble(data.message, false);
                if (data.blocks) {
                    reorderUIBlocks(data.blocks);
                }
            } else {
                appendMessageBubble("Oh no! I ran into an issue handling that layout command: " + data.error, false);
            }
        })
        .catch(err => {
            if (chatMessages && chatMessages.contains(typingBubble)) {
                chatMessages.removeChild(typingBubble);
            }
            appendMessageBubble("Oops! Something went wrong connecting to my AI processor. Check your connection or API key! 🔌", false);
            console.error("AI chat communication error:", err);
        });
    }

    function reorderUIBlocks(blocksList) {
        const items = [...listContainer.querySelectorAll('.draggable-block-item')];
        
        blocksList.forEach(blockData => {
            const blockItem = items.find(item => item.getAttribute('data-block-id') === blockData.block_id);
            if (blockItem) {
                const cb = blockItem.querySelector('.visibility-checkbox');
                if (cb) {
                    cb.checked = blockData.is_visible;
                    cb.dispatchEvent(new Event('change'));
                }
                
                listContainer.appendChild(blockItem);
                
                blockItem.style.transition = 'none';
                blockItem.style.backgroundColor = '#ecfdf5';
                blockItem.style.borderColor = '#34d399';
                setTimeout(() => {
                    blockItem.style.transition = 'all 0.4s';
                    blockItem.style.backgroundColor = '#f8fafc';
                    blockItem.style.borderColor = '#e2e8f0';
                }, 800);
            }
        });
    }

    sendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
}
