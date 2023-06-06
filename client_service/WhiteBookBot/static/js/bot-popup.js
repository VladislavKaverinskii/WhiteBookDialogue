$(document).ready(function(){
	var arrow = $('.chat-head img');
	var textarea = $('.chat-text textarea');
	var start_button = $('.dialog-start_button');
	var additional_data = {};
	var request_counter = 0;
	var base_url = ""
	
	var chat_head_height = $(".chat-head").height();
	var chat_text_height = $(".chat-text").height();
    var chat_box_height = $(".chat-box").height();
	var chat_body_height = chat_box_height - chat_head_height - chat_text_height;
	
	$(".chat-body").height(chat_body_height); 
	
	$(window).resize(function() {
		chat_head_height = $(".chat-head").height();
		chat_text_height = $(".chat-text").height();
		chat_box_height = $(".chat-box").height();
			
	    chat_body_height = chat_box_height - chat_head_height - chat_text_height;
		$(".chat-body").height(chat_body_height); 
	});
	
	$.ajax({
				url: "/get_history/",
				data: {},
				type: "post",
				success: restoreDialog
			})
			
			
	function restoreDialog(data) {		
		if (data.length > 0) {
			//console.log(data);
			$(".msg-insert").empty();					
			$('.msg-insert').append("<div class='msg-receive'>Привіт! Це довідкова система з питань реабілітації. Що вас цікавить?</div>");
			for (var item_n in data) {
				if (typeof data[item_n]["type"] != "undefined") {
					if (data[item_n]["type"] == "question") {
						$('.msg-insert').append("<div class='msg-send'>"+data[item_n]["question"]+"</div>");
					} else {
						//console.log(data[item_n]);
						distlayResponse(data[item_n]);
					}
				}				
			}
			stopDialogButton();
			$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
			
			$(".chat-text_input").removeAttr("disabled");
			$(".chat-text_input").attr("placeholder", "Введіть Ваше питання і натисніть Enter...");
		} else {
			console.log("session is new");
			$(".chat-text_input").attr("placeholder", "Натисніть кнопку для початку діалогу.");
		}		
	}
	

	arrow.on('click', function(){
		var src = arrow.attr('src');
		
		$('.chat-body').slideToggle('slow');		
		
		if(src == '/static/img/angle_down-16.png'){
			arrow.attr('src', '/static/img/angle_up-16.png');
			$('.chat-box').animate({height:"45px"}, 'slow');
			$('.chat-text').animate({height:"1px"}, 'fast');
		}
		else{
			arrow.attr('src', '/static/img/angle_down-16.png');
			$('.chat-box').animate({height:"90%"}, 'slow');
			$('.chat-text').animate({height:"65px"}, 'fast');
		}
	});

	textarea.keypress(function(event) {

		var $this = $(this);	

		if(event.keyCode == 13){
			var msg = $this.val();
			$this.val('');
			var current_data = {"question": msg}
			sendRequest(current_data)
			$('.msg-insert').append("<div class='msg-send'>"+msg+"</div>");
		}
	});
	
	
	function sendRequest(sending_data) {
		$(".dialog-button").prop('disabled', true);
		$(".stop_dialog-button").parent().remove();
		$(".stop_dialog-button-positive").parent().remove();
		request_counter = 0;
		$(".chat-text_input").empty();
		$(".chat-text_input").attr("placeholder", "Очікую відповідь...");
		$(".chat-text_input").prop('disabled', true);
		$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
		$.ajax({
			url: "/process_question/",
			data: sending_data,
			type: "post",
			success: requestAnswer
		})
		
	}
	
	
	
	$(".msg-insert").on('click', ".dialog-start_button", function(e){
		e.preventDefault();
		$(".chat-text_input").attr("placeholder", "З'єднання з сервером... Зачекайте.");
		$(".dialog-button").prop('disabled', true);
		$(".start-dialog_replic").remove();
		$.ajax({
			url: "/",
			data: {},
			type: "post",
			success: startNewDialog,
				complete: function(jqXHR, status) {
					$(".dialog-button").removeAttr("disabled");
					$(".chat-text_input").removeAttr("disabled");
					$(".chat-text_input").attr("placeholder", "Введіть Ваше питання і натисніть Enter...");
					$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
				}
		})
		
	});
	
	$(".msg-insert").on('click', ".show-additional_button", function(e){
		e.preventDefault();		
		
		new_msg = additional_data[$(this).attr("name")];
		//console.log("name " + $(this).attr("name"));
		if (new_msg != "undefined" && new_msg != "") {
			$(this).parent().append(new_msg);
		}
		$(this).remove();		
	});	
	
	
	
	$(".msg-insert").on('click', ".send-request_button", function(e){
		e.preventDefault();	
		
		new_msg = $(this).attr("name");
		if (new_msg != "undefined" && new_msg != "") {
			new_msg = new_msg.replace('&apos', "'")
			//console.log(new_msg);
			$('.msg-insert').append("<div class='msg-send'>" + new_msg + "</div>");
			sendRequest({"question": new_msg});
		}	
	});	
	
	
	function startNewDialog(data) {
		$(".chat-text_input").removeAttr("disabled");		
        $('.msg-insert').append("<div class='msg-receive'>" + data["greeting_phrase"] +"</div>");
		stopDialogButton();
		
	}
	
	function requestAnswer(data) {
		console.log(data);
		$(".chat-text_input").val("");
		request_counter += 1;
		var anwerExist = false;
		
		if ((request_counter <= 3000) &&(typeof data["tech_response"] != "undefined") && (data["tech_response"] == "is_standard")) {
			for (var key in data["primary_answers"]) {
				if (data["primary_answers"].length > 1) {
				renderPrimaryAnswerMessage(data["primary_answers"][key]);
				} else {
					$('.msg-insert').append("<div class='msg-receive'>" + formAnswerPhrase(data["primary_answers"][key]) +"</div>");
				}		
			}
			$(".dialog-button").prop('disabled', false);
			$(".chat-text_input").removeAttr("disabled");
			$(".chat-text_input").attr("placeholder", "Введіть Ваше питання...");
			$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
			stopDialogButton();
		} else if ((request_counter <= 3000) &&(typeof data["tech_response"] != "undefined") && (data["tech_response"] == "is_cashed")){
			anwerExist = true;
			$(".dialog-button").prop('disabled', false);
			//console.log(data);
			distlayResponse(data);
			stopDialogButton();
			$(".chat-text_input").removeAttr("disabled");
			$(".chat-text_input").attr("placeholder", "Введіть Ваше питання...");
			$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
		} else {
			
			$.ajax({
				url: "/get_answer/",
				data: {"task_id": data["task_id"],
						"is_too_long": data["is_too_long"],
						"question_data": data["question_data"]},
				type: "post",
				success: function (data_2) {
						//console.log((typeof data_2["tech_response"] !== "undefined") && (data_2["tech_response"] == "in_process"));
						if ((request_counter <= 3000) &&(typeof data_2["tech_response"] != "undefined") && (data_2["tech_response"] == "in_process")) {
							anwerExist = false;
							setTimeout(requestAnswer (data), 1000);
						} else {
							anwerExist = true;
							$(".dialog-button").prop('disabled', false);
							//console.log(data_2);
							distlayResponse(data_2);
							stopDialogButton();
							$(".chat-text_input").removeAttr("disabled");
							$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
							$(".chat-text_input").attr("placeholder", "Введіть Ваше питання...");
						}
					}
			})
		}
		
	}
	
	function renderPrimaryAnswerMessage(data) {
		var answer_phrase = formAnswerPhrase(data);	
		//console.log(data["semantic_type"]);
		if ((data["semantic_type"] == "linked_classes_down") ||
			(data["semantic_type"] == "sub_class") || 
			(data["semantic_type"] == "chapter") || 
			(data["semantic_type"] == "topic") || 
			(data["semantic_type"] == "query_of_predicate"))
			{
				if (answer_phrase.length > 100) {
					$('.msg-insert').append("<div class='msg-receive'><button name='" + answer_phrase.slice(0, 100).replace("'", '&apos') + "' class='send-request_button dialog-button'>" + answer_phrase.slice(0, 100) + "..." + "</button></div>");
				} else {
					$('.msg-insert').append("<div class='msg-receive'><button name='" + answer_phrase.replace("'", '&apos') + "' class='send-request_button dialog-button'>" + answer_phrase + "</button></div>");
				}
		} else {			
			$('.msg-insert').append("<div class='msg-receive'>" + answer_phrase +"</div>");	
		}
		
	}
			
			
	function formAnswerPhrase(dataItem) {
		var answer_phrase = "";
		
		/*if ((typeof dataItem["comment"] != "undefined") && (dataItem["comment"] != "")) {
			answer_phrase += "<strong><i>" +  dataItem["comment"] + "</i></strong><br />"	;							
		}*/
		if ((typeof dataItem["name"] != "undefined") && (dataItem["name"] != "") && (dataItem["name"] != "Topic") && (dataItem["name"] != "Chapter")) {
			answer_phrase += "<b>" +  dataItem["name"] + "</b><br />"	;							
		}							
		
		if (dataItem["semantic_type"] == "predicate_definition") {
			if (typeof dataItem["entities_for_query"] !== "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong>";
				}
			}
		} else if ((dataItem["semantic_type"] == "super_class") || (dataItem["semantic_type"] == "linked_classes_up")) {
			if (typeof dataItem["entities_for_query"] != "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong> належить до: ";
				}
			}
			
		} else if (dataItem["semantic_type"] == "predicate_query") {
			if (typeof dataItem["entities_for_query"] != "undefined") {
				if (typeof dataItem["entities_for_query"]["inputEntity"] != "undefined") {
					answer_phrase += "<strong>" + dataItem["entities_for_query"]["inputEntity"] + "</strong> ";
				}
			}			
		}
		
		if ((typeof dataItem["content"] != "undefined") && (dataItem["content"] != "")) {
			/* answer_phrase += "<br /><i><b>\"" + dataItem["content"]; */
			if ((dataItem["semantic_type"] == "super_class" || (dataItem["semantic_type"] == "linked_classes_up"))
			     && dataItem["entities_for_query"] != "undefined") {
				answer_phrase += "<br /><i><b>\"" + dataItem["content"] + "\"</b></i>";
			} else if (answer_phrase != "") {
				answer_phrase += "<br />" + dataItem["content"];
			} else {
				answer_phrase += dataItem["content"];
			}
		}
		return answer_phrase;		
	}
	
	
	
	function stopDialogButton() {
		$(".stop_dialog-button").parent().remove();
		$(".stop_dialog-button-positive").parent().remove();
		$('.msg-insert').append("<div class='msg-receive'><button class='stop_dialog-button dialog-button'>Завершити діалог</button></div>");		
	}
	
	
	$(".msg-insert").on('click', ".stop_dialog-button", function(e){
		e.preventDefault();
		$(this).parent().append("Чи отримали Ви відповіді на свої питання?<br /><button class='stop_dialog-button-positive dialog-button'>Так</button><button class='stop_dialog-button-negative dialog-button'>Ні</button>");
		$(this).remove();
		$(".chat-body").animate({scrollTop: $(".chat-body")[0].scrollHeight});
		
	});
	
	
	$(".msg-insert").on('click', ".stop_dialog-button-positive", function(e){
		e.preventDefault();
		
		$(this).parent().remove();
		$(".msg-insert").empty();
		$(".dialog-button").prop('disabled', true);
		$(".chat-text_input").prop('disabled', true);
		$(".chat-text_input").attr("placeholder", "З'єднання з сервером... Зачекайте.");
		
		$(".start-dialog_replic").remove();
		$.ajax({
			url: "/ask_unsubscribe/",
			data: {"result": "True"},
			type: "post",
			success: function (data) {
				
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'> Бажаєте розпочати розмову? </div>");
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'><button class='dialog-button dialog-start_button'>Розпочати діалог</button></div>");
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Натисніть кнопку для початку діалогу");
			},
			complete: function(jqXHR, status) {
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Натисніть кнопку для початку діалогу");
			}
		})	
		
	});
		
		
	$(".msg-insert").on('click', ".stop_dialog-button-negative", function(e){
		e.preventDefault();
		$(this).parent().remove();
		$(".msg-insert").empty();
		$(".dialog-button").prop('disabled', true);
		$(".chat-text_input").prop('disabled', true);		
		$(".start-dialog_replic").remove();
		$(".chat-text_input").attr("placeholder", "З'єднання з сервером... Зачекайте.");
		$.ajax({
			url: "/ask_unsubscribe/",
			data: {"result": "False"},
			type: "post",
			success: function (data) {
				
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'> Бажаєте розпочати розмову? </div>");
				$('.msg-insert').append("<div class='msg-receive start-dialog_replic'><button class='dialog-button dialog-start_button'>Розпочати діалог</button></div>");
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Натисніть кнопку для початку діалогу");
			},
			complete: function(jqXHR, status) {
				$(".dialog-button").prop('disabled', false);
				$(".chat-text_input").attr("placeholder", "Натисніть кнопку для початку діалогу");
			}
		})
		
	});
	
	
	function distlayResponse(data) {
		if (typeof data["greeting_phrase"] != "undefined" && data["greeting_phrase"] != "") {
			$('.msg-insert').append("<div class='msg-receive'>"+ data["greeting_phrase"] +"</div>");
		} else {
			var greeting_phrase = "";
			for (var key in data["primary_answers"]) {
				if (typeof data["primary_answers"][key]["comment"] != "undefined") {
					if (data["primary_answers"][key]["comment"] != "") {
						$('.msg-insert').append("<div class='msg-receive'>"+ data["primary_answers"][key]["comment"] +"</div>");
						break;
					}
				}
			}
		}
							
		for (var key in data["primary_answers"]) {
			if (data["primary_answers"].length > 1) {
				renderPrimaryAnswerMessage(data["primary_answers"][key]);
			} else {
				$('.msg-insert').append("<div class='msg-receive'>" + formAnswerPhrase(data["primary_answers"][key]) +"</div>");
			}
			
		}
		if (typeof data["additional_answers"] != "undefined") {
			if (data["additional_answers"].length > 0) {
				$('.msg-insert').append("<div class='msg-receive'>"+ data["additional_info_message"] +"</div>");						
				
				for (var key in data["additional_answers"]) {
					var current_phrase_additional = formAnswerPhrase(data["additional_answers"][key]);
					var name_key = "1";
					if ((typeof data["additional_answers"][key]["name"] != "undefined") && (data["additional_answers"][key]["name"] != "")) {
						name_key = data["additional_answers"][key]["name"];									
					} else if ((typeof data["additional_answers"][key]["entities_for_query"] != "undefined") && (data["additional_answers"][key]["name"] != {})) {
						if (typeof data["additional_answers"][key]["entities_for_query"]["inputEntity"] != "undefined") {
							name_key = data["additional_answers"][key]["entities_for_query"]["inputEntity"];
                            var name_key_llist = name_key.split('|');
							name_key = name_key_llist[0];
							var expl_name = name_key_llist[1];
							if (typeof expl_name == "undefined") {
								expl_name = '';
							} else {
								expl_name = expl_name;
							}
							
								if ((typeof data["additional_answers"][key]["content"] != "undefined") && (data["additional_answers"][key]["content"] != "")) {												
									name_key += " " + data["additional_answers"][key]["content"].slice(0, 20);
									if (data["additional_answers"][key]["content"].length > 20) {
										name_key += "... ";
									}
								} else {
									name_key += " " + String(key + 1);
								}
							name_key += expl_name;
							
						}
					} else if ((typeof data["additional_answers"][key]["content"] != "undefined") && (data["additional_answers"][key]["content"] != "")) {
						name_key =  data["additional_answers"][key]["content"].slice(0, 20);
						var name_key_llist = name_key.split('|');
							name_key = name_key_llist[0];
							var expl_name = name_key_llist[1];
							if (typeof expl_name == "undefined") {
								expl_name = '';
							} else {
								expl_name = expl_name;
							}
						
						
						if (data["additional_answers"][key]["content"].length > 20) {
										name_key += "... ";
									}
									
					}
					if (data["additional_answers"][key]["semantic_type"] == "predicate_definition") {
						name_key += " |<strong>(визначення)</strong>";
					}  else if (data["additional_answers"][key]["semantic_type"] == "sub_class") {
						name_key += " |<strong>(складові)</strong>";
					} else if (data["additional_answers"][key]["semantic_type"] == "predicate_query") {	
						name_key += " |<strong>(основна інформація)</strong>";
					} else if (data["additional_answers"][key]["semantic_type"] == "label_definition") {	
						name_key += " |<strong>(пояснення)</strong>";
					} else if (data["additional_answers"][key]["semantic_type"] == "linked_classes_up") {	
						name_key += " |<strong>(приналежність)</strong>";
					} 
					
					additional_data[name_key.replace("'", '&apos')] = current_phrase_additional;								
					$('.msg-insert').append("<div class='msg-receive'><button name='" + name_key.replace("'", '&apos') + "' class='show-additional_button dialog-button'>" + name_key.split('|').join(' ') + "</button></div>");
									
				}
			}
		}	
		
		
	}
	
	
	
	
	
	
	

});