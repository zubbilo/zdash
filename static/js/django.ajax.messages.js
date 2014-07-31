function addMessage(text, extra_tags) {
    var message = $('<div class="alert alert-'+extra_tags+'">'+text+'</li>').hide();
    $("#messages").append(message);
    message.fadeIn(500);

    setTimeout(function() {
        message.fadeOut(500, function() {
            message.remove();
        });
    }, 50000);
}
