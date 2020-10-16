async function test_post() {
    console.log("testing POST");
    response = await doPost('/host', {'key': 'value'})
    document.body.innerHTML = JSON.stringify(response);
  }


  async function doPost(url_path, data)
  {
    console.log("sending POST");

    response = await fetch(url_path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    // TODO check response status, redirect if requested @@@@@@@@@@@@@@@@@@@@@@@

    response = await response.json()

    console.log("sent POST");

    return response;
  }

  