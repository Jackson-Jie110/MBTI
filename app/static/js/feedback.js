document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('feedback-modal');
  const card = document.getElementById('feedback-card');
  const btn = document.getElementById('feedback-btn');
  const closeBtn = document.getElementById('close-feedback');
  const submitBtn = document.getElementById('submit-feedback-btn');
  const stars = document.querySelectorAll('.star-btn');
  const contentInput = document.getElementById('feedback-content');

  if (!modal || !card || !btn || !closeBtn || !submitBtn || stars.length === 0) {
    return;
  }

  let currentRating = 0;

  function showModal() {
    modal.classList.remove('hidden');
    setTimeout(() => {
      modal.classList.remove('opacity-0');
      card.classList.remove('scale-95');
      card.classList.add('scale-100');
    }, 10);
  }

  function hideModal() {
    modal.classList.add('opacity-0');
    card.classList.remove('scale-100');
    card.classList.add('scale-95');
    setTimeout(() => {
      modal.classList.add('hidden');
    }, 300);
  }

  function updateStars(value) {
    const intValue = Number(value);
    stars.forEach((star) => {
      const starVal = Number(star.getAttribute('data-val'));
      if (starVal <= intValue) {
        star.classList.remove('text-gray-300');
        star.classList.add('text-yellow-400');
      } else {
        star.classList.add('text-gray-300');
        star.classList.remove('text-yellow-400');
      }
    });
  }

  function resetButtonState() {
    submitBtn.innerText = '提交反馈';
    submitBtn.disabled = false;
  }

  btn.addEventListener('click', showModal);
  closeBtn.addEventListener('click', hideModal);

  if (!localStorage.getItem('hasFeedback')) {
    setTimeout(() => {
      if (!localStorage.getItem('hasFeedback')) {
        showModal();
      }
    }, 15000);
  } else {
    btn.style.display = 'none';
  }

  stars.forEach((star) => {
    star.addEventListener('click', function onClick() {
      currentRating = Number(this.getAttribute('data-val'));
      updateStars(currentRating);
    });
  });

  submitBtn.addEventListener('click', async () => {
    if (currentRating === 0) {
      alert('请先点亮星星打分哦~');
      return;
    }

    const content = contentInput ? contentInput.value : '';
    const mbtiType = new URLSearchParams(window.location.search).get('type');

    submitBtn.innerText = '提交中...';
    submitBtn.disabled = true;

    try {
      const response = await fetch('/submit_feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: currentRating,
          content,
          mbti_type: mbtiType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      localStorage.setItem('hasFeedback', 'true');
      submitBtn.innerText = '🎉 感谢您的声音！';
      btn.style.display = 'none';
      setTimeout(hideModal, 1500);
    } catch (error) {
      console.error(error);
      alert('提交失败，请稍后重试');
      resetButtonState();
    }
  });
});
