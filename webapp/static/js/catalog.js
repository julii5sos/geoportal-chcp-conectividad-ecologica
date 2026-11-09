(() => {
  const year = document.getElementById('catalog-year');
  const type = document.getElementById('catalog-type');
  const category = document.getElementById('catalog-category');
  const rows = Array.from(document.querySelectorAll('.catalog-table tbody tr'));
  function filter() { rows.forEach(row => { row.hidden = Boolean((year.value && row.dataset.year !== year.value) || (type.value && row.dataset.type !== type.value) || (category.value && row.dataset.category !== category.value)); }); }
  year?.addEventListener('change', filter); type?.addEventListener('change', filter); category?.addEventListener('change', filter);
})();
