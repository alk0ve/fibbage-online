function start() {
    console.log("starting");
    response = doPost('/some_post_url', {'key': 'value'})
    document.body = JSON.stringify(response)
  }


  async function doPost(url_path, data)
  {
    console.log("sending POST");

    const response = await fetch(url_path, {
      method: 'POST', // *GET, POST, PUT, DELETE, etc.
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data) // body data type must match "Content-Type" header
    });

    console.log("sent POST");

    return response.json(); // parses JSON response into native JavaScript objects    
  }

  