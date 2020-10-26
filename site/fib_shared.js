async function test_post() {
    console.log("testing POST");
    response = await doPost('/host', {'key': 'value'})
    document.body.innerHTML = JSON.stringify(response);
  }


  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }


  function getIdFromCurrentURL()
  {
    return window.location.hash.substr(1);
  }

  // matching fib_game.py
const POST_RETURN_CODES = {
  POST_REPLY: 0,
  POST_REDIRECT: 1,
  POST_VALIDATION_ERROR: 2,
  POST_INTERNAL_ERROR: 3,
  POST_ENDPOINT_NOT_FOUND: 4
};

const GAME_STATES = {
  GAME_PREPARING: 'preparing',
  GAME_FIBBING: 'fibbing',
  GAME_CHOOSING: 'choosing',
  GAME_DISPLAYING: 'displaying'
};

const FIB_TYPES = {
  FIB_USER_CREATED: 0,
  FIB_SUGGESTION: 1
};

/*
  Sends JSON to the specified URL via POST,
  receives a response JSON with return code and data;
  if return code is POST_REPLY the result is returned;
  if return code is redirect a redirect is performed;
  otherwise the error is displayed in the specified label.

  This function should match the contents of
  HorribleHTTPRequestHandler.do_POST() in http_server.py.
*/
  async function doPost(url_path, data, error_label_id = "")
  {
    body_content = JSON.stringify(data);
    console.log("sending POST to " + url_path + " with " + body_content);

    let response = await fetch(url_path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    let response_dictionary = await response.json();

    console.log("Received POST reply with " + JSON.stringify(response_dictionary));

    let return_code = Number(response_dictionary["return_code"]);

    if (return_code == POST_RETURN_CODES.POST_REPLY)
    {
      return response_dictionary["data"];
    }
    else if (return_code == POST_RETURN_CODES.POST_REDIRECT)
    {
      let location = response_dictionary["location"];
      //console.log("REDIRECT to " + location);
      window.location = location;
    }
    else if (error_label_id.length > 0)
    {
      //console.log("ERROR MESSAGE: " + response_dictionary["error_message"]);
      document.getElementById(error_label_id).textContent = "ERROR: " + response_dictionary["error_message"];
    }

    return null;
  }

/* Randomize array in-place using Durstenfeld shuffle algorithm */
function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
  }
}