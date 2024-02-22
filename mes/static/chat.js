function send_message(message , user_id){
	$.ajax({
		type:'POST',
		url: '/chatting/message/'+ encodeURIComponent(message) +'/' + user_id ,
		dataType: 'json',
		success: function(data){
			const html = data.map(function(message){

				var deleteUrl = `{{ url_for('delete_message', message=message.id) }}`;

				let color , bg  , mbval  , brr3, more_style, small_color, small_style, dop, dop2;

				if (message.sender == user_id) {
					bg = 'bg-light';
					mbval = '1';
					color ='black-text';
					brr3 = '<br>';
					more_style = '';
					small_color = '#777';
					small_style = '';
					dop = '';
					dop2 = '';
				}
					else {
						bg = '';
						mbval ='2'
						color = 'text-white';
						brr3 = '<br>';
						more_style = 'margin:0 auto; margin-right: 0;';
						small_color = '#eaf0fa';
						small_style = 'text-align: left';
						dop = `<a href="${deleteUrl}"><img align="right" style="margin-left: 15px; margin-top: 6px;" src="../static/site_pics/ban.png" alt="Ban" width="17" height="17"></a>
`;
				}
			return `     
              <div class="card ${bg} z-depth-0 mb-${mbval} message-text"
              style="background-color:#7299df; width: max-content; max-width: 500px; ${more_style}">
                <div class="card-body p-2">
                  <a class="card-text ${color}" style =" font-family: 'Tahoma';font-size: 14px;">${ message.message }</a>
                  <div style="${small_style}"><small class="" style="color: ${small_color}">${ message.date }</small>
                </div>
                </div>
              </div>
              ${brr3}
          `
		}).join('');
			const messages_ = document.querySelector('.messages');
			messages.innerHTML = html;
			messages.scrollTop = messages.scrollHeight;


		}
	});
}


$(document).ready(function() {
    $(".delete-message").on("click", function(e) {
        e.preventDefault();

        var messageId = $(this).data("id");

        $.ajax({
            type: "POST",
            url: '/chatting/message/'+ encodeURIComponent(message) +'/delete',
            success: function(response) {
                // Обновление участка страницы после успешного удаления
                // Ваш код обновления содержимого страницы
                alert("Сообщение успешно удалено!");
            },
            error: function(error) {
                console.error("Ошибка при удалении сообщения:", error);
            }
        });
    });
});



