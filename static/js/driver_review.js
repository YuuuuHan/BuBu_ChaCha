$('.edit-score').val(1)
// 用trick把原本的星星(rating)值複製到django form的score值
$('#edit-comment-form').on('submit', (e) => {
  const formData = new FormData(e.target)
  $('.edit-score').val(formData.get('rating'))
})

$('.edit-button, .delete-button').on('click', (e) => {
  console.log(e.target.getAttribute('data-form-action'))
  $('#edit-comment-form').attr('action', e.target.getAttribute('data-form-action'))
  $('#delete-comment-form').attr('action', e.target.getAttribute('data-form-action'))
})
