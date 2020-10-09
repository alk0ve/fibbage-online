async function start(){
	data = await get_question_json()
	parse_and_set_question(data)
	set_timer(document.getElementById("countdown").innerHTML-1)
}

function parse_and_set_question(data){
	var question = data.fields.find(field=>field.n === "QuestionText")
	if (question){
		// set the question
		var question_str = question.v.replace("<BLANK>", "______");
		document.getElementById("question_container").innerHTML =  question_str;
	} else {
		console.log('No question in the json');
	}
}

async function get_question_json(json_path='./data'){
	const response = await fetch(json_path);
	if (response.status !== 200) {
		console.log('Looks like there was a problem. Status Code: ' + response.status);
		return;
	}

	var data = await response.json();
	return data;
}

function set_timer(duration){
	var timeleft = duration;
	var downloadTimer = setInterval(function(){
		if(timeleft < 0){
			clearInterval(downloadTimer);
			if (document.forms['frm_answer'].input_lie.value === "") {
				// send some random fake answer (also show it on the screen for the user to know)
				alert("empty");
			} else {
				// send the fake answer the user choose
				send_lie(document.forms['frm_answer'].input_lie.value);
			}
		  }
		  
		  // update the countdown
		  document.getElementById("countdown").innerHTML =  timeleft;
		  timeleft -= 1;
	}, 1000);
}

function send_lie(lie){
	// check if the answer is not the real answer
	// send the answer to the server with post
	// stop timer
	alert("submited lie!");
};


function enter_send_form(e) {
	if((e && e.keyCode == 13) || e == 0) {
		send_lie(e)
   }
}