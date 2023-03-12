$('.score').val(1)
// 用trick把原本的星星(rating)值複製到django form的score值
$('#form').on('submit', (e) => {
  const formData = new FormData(e.target)
  $('.score').val(formData.get('rating'))
})

