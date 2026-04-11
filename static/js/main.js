// DetailFlow - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initSidebar();
    initKanban();
    initToasts();
    initConfirmDialogs();
    initMobileKeyboardScrollFix();
    initStaffNotificationPoll();
    initThemeToggle();
});

const THEME_STORAGE_KEY = 'cds-theme';

function initThemeToggle() {
    const btn = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-toggle-icon');
    if (!btn || !icon) return;

    function currentTheme() {
        return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    }

    function applyUi(theme) {
        var isLight = theme === 'light';
        icon.className = isLight ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
        btn.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
        btn.setAttribute('title', isLight ? 'Dark theme' : 'Light theme');
    }

    applyUi(currentTheme());

    btn.addEventListener('click', function () {
        var next = currentTheme() === 'light' ? 'dark' : 'light';
        if (next === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        try {
            localStorage.setItem(THEME_STORAGE_KEY, next);
        } catch (e) { /* ignore */ }
        applyUi(next);
    });
}

// Sidebar Toggle (Mobile)
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('[data-toggle="sidebar"]');
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            document.body.classList.toggle('sidebar-open');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (sidebar.classList.contains('show') && 
                !sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('show');
                document.body.classList.remove('sidebar-open');
            }
        });
    }
}

// On mobile, the virtual keyboard can cover the focused input.
// Scrolling the focused element into view keeps forms usable.
function initMobileKeyboardScrollFix() {
    const isMobile = window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
    if (!isMobile) return;

    const focusable = document.querySelectorAll('input, textarea, select');
    focusable.forEach(el => {
        el.addEventListener('focus', function () {
            setTimeout(() => {
                try {
                    this.scrollIntoView({ behavior: 'smooth', block: 'center' });
                } catch (e) {
                    // no-op (some browsers may not support smooth scroll in this context)
                }
            }, 150);
        });
    });
}

// Kanban Drag and Drop
function initKanban() {
    const kanbanCards = document.querySelectorAll('.job-card[draggable="true"]');
    const kanbanColumns = document.querySelectorAll('.kanban-cards');
    
    kanbanCards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });
    
    kanbanColumns.forEach(column => {
        column.addEventListener('dragover', handleDragOver);
        column.addEventListener('drop', handleDrop);
        column.addEventListener('dragenter', handleDragEnter);
        column.addEventListener('dragleave', handleDragLeave);
    });
}

let draggedCard = null;

function handleDragStart(e) {
    draggedCard = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.jobId);
}

function handleDragEnd() {
    this.classList.remove('dragging');
    document.querySelectorAll('.kanban-cards').forEach(col => {
        col.classList.remove('drag-over');
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDragEnter(e) {
    e.preventDefault();
    this.classList.add('drag-over');
}

function handleDragLeave() {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
    
    if (draggedCard) {
        const jobId = e.dataTransfer.getData('text/plain');
        const newStatus = this.dataset.status;
        
        // Move card visually
        this.appendChild(draggedCard);
        
        // Update on server
        updateJobStatus(jobId, newStatus);
        
        // Update column counts
        updateColumnCounts();
    }
}

function updateJobStatus(jobId, newStatus) {
    fetch(`/api/jobs/${jobId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update status');
        }
        return response.json();
    })
    .then(data => {
        showToast('Job status updated successfully', 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to update job status', 'error');
        // Optionally reload to restore state
        // location.reload();
    });
}

function updateColumnCounts() {
    document.querySelectorAll('.kanban-column').forEach(column => {
        const cards = column.querySelectorAll('.job-card').length;
        const countBadge = column.querySelector('.kanban-count');
        if (countBadge) {
            countBadge.textContent = cards;
        }
    });
}

// Toast Notifications
function initToasts() {
    // Create toast container if doesn't exist
    if (!document.querySelector('.toast-container')) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    const id = 'toast-' + Date.now();
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const html = `
        <div id="${id}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Confirm Dialogs
function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// CSRF Token Helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Format Currency (KES)
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: 'KES',
        minimumFractionDigits: 0
    }).format(amount);
}

// Format Date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-KE', options);
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search with Debounce
const searchInput = document.querySelector('[data-search]');
if (searchInput) {
    searchInput.addEventListener('input', debounce(function() {
        const query = this.value;
        const url = new URL(window.location.href);
        url.searchParams.set('q', query);
        window.location.href = url.toString();
    }, 500));
}

// Auto-dismiss alerts
document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
    }, 5000);
});

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write('<html><head><title>Print</title>');
        printWindow.document.write('<link rel="stylesheet" href="/static/css/style.css">');
        printWindow.document.write('</head><body>');
        printWindow.document.write(element.innerHTML);
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    }
}

// Staff notifications: poll API so managers/workers see new alerts (e.g. job completed)
let _lastUnreadNotificationCount = -1;

function _notificationEscapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function _renderNotificationDropdown(items) {
    const listEl = document.getElementById('notification-list');
    if (!listEl) return;

    if (!items || !items.length) {
        listEl.innerHTML = '<p class="text-center text-muted py-3 mb-0">No notifications yet.</p>';
        return;
    }

    const rows = items.map(function (n) {
        const readClass = n.is_read ? '' : 'bg-light';
        const jobLink = n.job_id ? '/jobs/' + n.job_id + '/' : '#';
        return (
            '<div class="px-3 py-2 border-bottom small ' + readClass + '">' +
            '<div class="fw-medium">' + _notificationEscapeHtml(n.title || '') + '</div>' +
            '<div class="text-muted">' + _notificationEscapeHtml(n.message || '') + '</div>' +
            (n.job_id ? '<a class="small" href="' + jobLink + '">View job</a>' : '') +
            '</div>'
        );
    });
    listEl.innerHTML = rows.join('');
}

function _updateNotificationBadge(count) {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count;
        badge.classList.remove('d-none');
    } else {
        badge.textContent = '0';
        badge.classList.add('d-none');
    }
}

function fetchStaffNotifications() {
    if (!document.body.dataset.staffNotificationPoll) return;
    fetch('/notifications/api/', {
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json' }
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            const unread = data.unread_count || 0;
            if (_lastUnreadNotificationCount >= 0 && unread > _lastUnreadNotificationCount) {
                showToast('You have new notifications', 'info');
            }
            _lastUnreadNotificationCount = unread;
            _updateNotificationBadge(unread);
            _renderNotificationDropdown(data.notifications || []);
            const lu = document.getElementById('last-updated');
            if (lu) {
                lu.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
            }
        })
        .catch(function () { /* ignore */ });
}

function initStaffNotificationPoll() {
    if (!document.body.dataset.staffNotificationPoll) return;
    const interval = typeof POLLING_INTERVAL !== 'undefined' ? POLLING_INTERVAL : 12000;
    fetchStaffNotifications();
    setInterval(fetchStaffNotifications, interval);
}

function markAllNotificationsRead() {
    fetch('/notifications/mark-all-read/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
        .then(function (r) { return r.json(); })
        .then(function () {
            _lastUnreadNotificationCount = 0;
            _updateNotificationBadge(0);
            fetchStaffNotifications();
        })
        .catch(function () { window.location.reload(); });
}

window.markAllNotificationsRead = markAllNotificationsRead;

// Export functions for global use
window.DetailFlow = {
    showToast,
    formatCurrency,
    formatDate,
    printElement,
    updateJobStatus
};
