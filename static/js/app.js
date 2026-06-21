/* ═══════════════════════════════════════════════════════════
   State Electric — Global JS
   Hamburger nav, offline sync engine, flash messages
   ═══════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  // ═══ HAMBURGER NAV ═══
  const hamburger = document.getElementById('hamburger-btn');
  const navLinks = document.getElementById('nav-links');

  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function(e) {
      e.stopPropagation();
      navLinks.classList.toggle('open');
    });

    // Close when clicking outside
    document.addEventListener('click', function(e) {
      if (navLinks.classList.contains('open') &&
          !navLinks.contains(e.target) &&
          !hamburger.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });

    // Close on escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') navLinks.classList.remove('open');
    });
  }

  // ═══ AUTO-DISMISS FLASH MESSAGES ═══
  document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s';
      setTimeout(function() { el.remove(); }, 300);
    }, 5000);
  });

})();

// ═══ OFFLINE SYNC ENGINE (Dexie.js) ═══
// Loads when Dexie is available from CDN in templates that need it
window.StateElectricSync = {
  db: null,

  async init() {
    // Dynamic import of Dexie
    if (typeof Dexie === 'undefined') {
      await this.loadScript('https://unpkg.com/dexie@3.2.4/dist/dexie.js');
    }
    this.db = new Dexie('StateElectric');
    this.db.version(1).stores({
      invoices: '++id, invoice_number, customer_id, status, updated_at',
      customers: '++id, name, division',
      syncQueue: '++id, action, table, data, created_at',
    });
    return this.db;
  },

  loadScript(src) {
    return new Promise(function(resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  },

  async syncFromServer() {
    if (!this.db) await this.init();
    try {
      var [invRes, custRes] = await Promise.all([
        fetch('/api/invoices/'),
        fetch('/api/customers/')
      ]);
      var invData = await invRes.json();
      var custData = await custRes.json();

      await this.db.invoices.bulkPut(invData.invoices.map(function(i) {
        return Object.assign({}, i, { updated_at: Date.now() });
      }));
      await this.db.customers.bulkPut(custData.customers);

      localStorage.setItem('lastSync', Date.now());
      return { ok: true, invoices: invData.invoices.length, customers: custData.customers.length };
    } catch (err) {
      console.error('Sync failed:', err);
      return { ok: false, error: err.message };
    }
  },

  async queueChange(action, table, data) {
    if (!this.db) await this.init();
    await this.db.syncQueue.add({ action, table, data, created_at: Date.now() });
  },

  async syncToServer() {
    if (!this.db) await this.init();
    var queue = await this.db.syncQueue.toArray();
    var csrf = document.querySelector('meta[name="csrf-token"]');
    var token = csrf ? csrf.getAttribute('content') : '';

    for (var item of queue) {
      try {
        var resp = await fetch('/api/' + item.table + '/' + item.action + '/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
          body: JSON.stringify(item.data)
        });
        if (resp.ok) await this.db.syncQueue.delete(item.id);
      } catch (err) {
        console.error('Sync queue item failed:', err);
      }
    }
  }
};

// Auto-sync when online
window.addEventListener('online', function() {
  if (window.StateElectricSync) {
    StateElectricSync.syncToServer();
  }
});

// Periodic sync every 5 minutes if online
setInterval(function() {
  if (navigator.onLine && window.StateElectricSync) {
    StateElectricSync.syncFromServer();
  }
}, 300000);
