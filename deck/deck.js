(() => {
  const slides = [...document.querySelectorAll('.slide')]
  const progress = document.querySelector('.progress > i')
  const counter = document.querySelector('[data-counter]')
  const total = slides.length
  let i = 0

  function show(n) {
    i = (n + total) % total
    slides.forEach((s, k) => s.classList.toggle('is-on', k === i))
    if (progress) progress.style.width = `${((i + 1) / total) * 100}%`
    if (counter) counter.textContent = String(i + 1).padStart(2, '0') + ' / ' + String(total).padStart(2, '0')
    history.replaceState(null, '', '#' + (i + 1))
    document.title = `${i + 1}. ${slides[i].dataset.title || "Dr Non's DIY RAG"}`
  }

  function fromHash() {
    const n = parseInt(location.hash.replace('#', ''), 10)
    if (Number.isFinite(n) && n >= 1 && n <= total) show(n - 1)
    else show(0)
  }

  document.addEventListener('keydown', (e) => {
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) {
      e.preventDefault()
      show(i + 1)
    } else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) {
      e.preventDefault()
      show(i - 1)
    } else if (e.key === 'Home') {
      e.preventDefault()
      show(0)
    } else if (e.key === 'End') {
      e.preventDefault()
      show(total - 1)
    }
  })

  document.querySelector('.stage')?.addEventListener('click', (e) => {
    if (e.target.closest('a')) return
    const mid = e.currentTarget.getBoundingClientRect()
    show(e.clientX > mid.left + mid.width / 2 ? i + 1 : i - 1)
  })

  document.querySelectorAll('[data-go]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault()
      show(Number(a.dataset.go) - 1)
    })
  })

  window.addEventListener('hashchange', fromHash)
  fromHash()
})()
