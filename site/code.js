function start() {
    console.log("starting");
    doPost('/some_post_url', {'key': 'value'}, onPostReply)

  }


  function doPost(url_path, data_dict, onReplyCb)
  {
    console.log("sending POST");
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url_path, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = onReplyCb;

    xhr.send(JSON.stringify(data_dict));
    console.log("sent POST");
  }

  function onPostReply()
  {
    console.log("received POST");
    var data = JSON.parse(this.responseText);
    document.body.innerHTML = JSON.stringify(data);
  }