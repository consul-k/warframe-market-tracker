// tracker/static/tracker/autocomplete.js
(function() {
  const input = document.getElementById('id_name');
  const hidden = document.getElementById('id_item_url_name');
  const list = document.getElementById('autocomplete-results');
  let activeIndex = -1;
  let items = [];

  function debounce(fn, wait) {
    let t;
    return function(...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  async function fetchSuggestions(q) {
    if (!q) {
      hideList();
      return;
    }
    try {
      const resp = await fetch(`/autocomplete/?q=${encodeURIComponent(q)}`);
      if (!resp.ok) { hideList(); return; }
      const data = await resp.json();
      items = data; // [{name, url}, ...]
      renderList(items);
    } catch (e) {
      console.error('Autocomplete error', e);
      hideList();
    }
  }

  const debouncedFetch = debounce((e) => fetchSuggestions(e.target.value.trim()), 250);

  if (!input || !list) {
    console.warn('Autocomplete: required DOM elements not found (input or list).');
    return;
  }

  input.addEventListener('input', debouncedFetch);

  // клик по элементу списка
  list.addEventListener('click', function(ev) {
    const li = ev.target.closest('a[data-index]');
    if (!li) return;
    const idx = parseInt(li.dataset.index, 10);
    chooseItem(idx);
  });

  // клавиши вверх/вниз/enter/esc
  input.addEventListener('keydown', function(e) {
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, items.length - 1);
      highlight(activeIndex);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      highlight(activeIndex);
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < items.length) {
        e.preventDefault();
        chooseItem(activeIndex);
      }
    } else if (e.key === 'Escape') {
      hideList();
    }
  });

  function renderList(arr) {
    if (!arr.length) { hideList(); return; }
    list.innerHTML = '';
    arr.forEach((it, idx) => {
      const a = document.createElement('a');
      a.className = 'list-group-item list-group-item-action';
      a.setAttribute('data-index', idx);
      a.style.cursor = 'pointer';
      a.innerHTML = `<div><strong>${escapeHtml(it.name)}</strong></div><small class="text-muted">${escapeHtml(it.url)}</small>`;
      list.appendChild(a);
    });
    list.style.display = 'block';
    activeIndex = -1;
  }

  function chooseItem(idx) {
    const it = items[idx];
    if (!it) return;

    input.value = it.name;
    if (hidden) hidden.value = it.url;
    hideList();

    // --- самое важное: записываем max_rank ---
    const maxRank = it.max_rank || 0;

    const rankFields = document.getElementById("rank-fields");
    const minField = document.getElementById("id_min_rank");
    const maxField = document.getElementById("id_max_rank");

    if (maxRank > 0) {
        rankFields.style.display = "block";

        // по умолчанию выбираем МАКСИМАЛЬНЫЙ
        document.getElementById("rank_max").checked = true;

        // заполняем скрытые поля
        minField.value = maxRank;
        maxField.value = maxRank;

        // сохраняем для переключателя rank_choice
        window.lastMaxRank = maxRank;

    } else {
        // мод без рангов
        rankFields.style.display = "none";
        minField.value = 0;
        maxField.value = 0;
        window.lastMaxRank = 0;
    }
  }

  document.addEventListener("change", (e) => {
    if (e.target.name === "rank_choice") {
      const minField = document.getElementById("id_min_rank");
      const maxField = document.getElementById("id_max_rank");
      if (!minField || !maxField) return;

      if (e.target.value === "min") {
        minField.value = 0;
        maxField.value = 0;
      } else if (e.target.value === "max") {
        // maxRank сохраняется при выборе предмета
        const max = window.lastMaxRank || 0;
        minField.value = max;
        maxField.value = max;
      }
    }
      });


  function highlight(idx) {
    const children = list.querySelectorAll('[data-index]');
    children.forEach((el, i) => {
      el.classList.toggle('active', i === idx);
    });
  }

  function hideList() {
    list.style.display = 'none';
    list.innerHTML = '';
    items = [];
    activeIndex = -1;
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function(m) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]);
    });
  }

  // клик вне списка — скрыть
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#autocomplete-results') && e.target !== input) {
      hideList();
    }
  });

})();
