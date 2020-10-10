/*
answer sending scenrios:
1. The user writes a lie and send before times stops
1.1. The lie is the real answer
1.1.1. There is time -> we ask the user to enter a real lie
1.1.2. There is no time -> we send out lie
1.2. The lie is a lie -> we send the lie
2. The user didn't write a lie and the timer ended -> we send out lie
*/
let answers = []
let countdownTimer = null

async function start(){
	let data = await get_question_json();
	answers = get_correct_answers(data);
	parse_and_set_question(data);
	countdownTimer = set_timer(document.getElementById("countdown").innerHTML-1, answers, data);
}

function get_lie(data){
	const suggestions = get_field(data, "Suggestions").v.split(',');
	const randomElement = suggestions[Math.floor(Math.random() * suggestions.length)];
	return randomElement;
}

function get_field(data, field_name){
	return data.fields.find(field=>field.n === field_name);
}

function get_correct_answers(data){
	let answers = [];
	answers.push(get_field(data, "CorrectText").v);
	answers.push.apply(answers, get_field(data, "AlternateSpellings").v.split(','));
	return answers;
}

function parse_and_set_question(data){
	var question = get_field(data, "QuestionText");
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

function set_timer(duration, answers, data){
	var timeleft = duration;
	var countdownTimer = setInterval(function(){
		if(timeleft <= 0){
			clearInterval(countdownTimer);
			if (document.getElementById("input_lie").value === "") {
				// send some random fake answer (also show it on the screen for the user to know)
				const lie = send_our_lie(data);
				alert("Time's out! we sent a lie of our own: " + lie);
			} else {
				// send the fake answer the user choose
				if(is_lie_true(document.getElementById("input_lie").value, answers)){
					// we send a lie from the suggestions if the user choose the correct answer
					const lie = send_our_lie(data);
					alert("You can't lie the truth!, no time so we sent a lie of our own: " + lie);
				} else {
					send_lie(document.getElementById("input_lie").value);
					alert("submited lie!");
				}
				send_lie(document.getElementById("input_lie").value);
			}
		  }
		  
		  // update the countdown
		  document.getElementById("countdown").innerHTML =  timeleft;
		  timeleft -= 1;
	}, 1000);
	return countdownTimer;
}

function is_lie_true(lie, answers){
	return answers.find(element => element === lie);
}

function send_our_lie(data){
	const lie = get_lie(data);
	document.getElementById("input_lie").value = lie;
	send_lie(lie, true);
	return lie;
}

function send_lie(lie, generated=false){
	// check if the answer is not the real answer
	// send the answer to the server with post
	// stop timer
	document.getElementById('input_lie').readOnly = true
};

function enter_send_form(e, lie) {
	if((e && e.keyCode == 13) || e == 0) {
		// TODO: answers should be a global
		if(is_lie_true(lie.value, answers)){
			alert("You can't lie the truth! enter a lie");
		} else {
			send_lie(lie.value);
			alert("submited lie!");
			if(countdownTimer){
				clearInterval(countdownTimer);
				document.getElementById("countdown").innerHTML = 0;
			}
		}
   }
}