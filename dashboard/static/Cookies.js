function get_login_cookie_gift_card(giftcode, userid) {
    var cookies = document.cookie;
    var logged = false;
    var not_used_gift;
    var logged_user;
  
    if(userid !== ""){
      var cookie_splited = cookies.split(";");
      var gift_code_val;
  
      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");
  
        if(value_array[0].replace(" ", "") === "gift_code" && value_array[1] !== ''){
          gift_code_val = value_array[1];
        }
      }
  
      if(gift_code_val !== null){
        document.cookie = `gift_code=; expires=${delete_cookie()}; path=/`
        return window.location.replace(`https://a.advic.repl.co/redeemcode?gift_code=${gift_code_val}&userid=${userid}`);
      }
    }
    
    if(cookies == ''){
      alert("You're Not Logged In!");
      document.cookie = `gift_code=${giftcode}`;
      return window.location.replace("https://a.advic.repl.co/login?redirect=gift_code");
    }else{
      var cookie_splited = cookies.split(";");
  
      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");
  
        if(value_array[0].replace(" ", "") === "login_key" && value_array[1] !== ''){
          logged = true;
          logged_user = value_array[1];
        }
  
        if(value_array[0].replace(" ", "") === "gift_code" && value_array[1] !== ''){
          logged = true;
          logged_user = value_array[1];
        }
      }
  
      if(logged==false){
        alert("You're Not Logged In!");
        document.cookie = `gift_code=${giftcode}`;
        return window.location.replace("https://a.advic.repl.co/login?redirect=gift_code");
      }else{
        return window.location.replace(`https://a.advic.repl.co/redeemcode?gift_code=${giftcode}&userid=${logged_user}`);
      }
    }
  }

  function delete_gift_cookie() {
    var cookies = document.cookie;

    if(cookies == ''){
      alert("You're Not Logged In!");
      return window.location.replace("https://a.advic.repl.co/login?redirect=home");
    }else{
      var cookie_splited = cookies.split(";");

      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");

        if(value_array[0].replace(" ", "") == "gift_code" && value_array[1] !== ''){
          document.cookie = `gift_code=; expire=${delete_cookie()}`;
          return;
          break;
        }
      }
    }

    return;
  }
  
  function get_login_cookie() {
    var cookies = document.cookie;
  
    if(cookies == ''){
      alert("You're Not Logged In!");
      return window.location.replace("https://a.advic.repl.co/login?redirect=gift_code");
    }else{
      var cookie_splited = cookies.split(";");
  
      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");
  
        if(value_array[0].replace(" ", "") == "login_key" && value_array[1] !== ''){
          return value_array[1];
          break;
        }
      }
  
      alert("You're Not Logged In!");
      return window.location.replace("https://a.advic.repl.co/login?redirect=gift_code");
    }
  }
  
  function get_login_key(redirect) {
    var cookie = document.cookie;
  
    if(cookie == ''){
      alert("You're Not Logged In!");
      return window.location.replace(`https://a.advic.repl.co/login?redirect=${redirect}`);
    }else{
      var cookie_splited = cookie.split(";");
  
      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");
  
        if(value_array[0].replace(" ", "") == "login_key" && value_array[1] !== ''){
          return value_array[1];
          break;
        }
      }
  
      alert("You're Not Logged In!");
      return window.location.replace(`https://a.advic.repl.co/login?redirect=${redirect}`);
    }
  }
  
  function set_login_cookie(data, redirect){
    const cookie = document.cookie;
    var redirect_cookie;
  
    if(cookie !== ''){
      var cookie_splited = cookie.split(";");
    
      for(i=0; i<cookie_splited.length; i++){
        var value_array = cookie_splited[i].split("=");
  
        if(value_array[0].replace(" ", "") == "login_key" && value_array[1] !== ''){
          return window.location.replace(get_link(redirect, data))
        }
      }
    }
  
    if(data === null || data === undefined || data === ""){
      document.cookie = `redirect=${redirect}; path=/`;
      return window.location.replace("https://a.advic.repl.co/just_random_thing/login?redirect=DClogin");
    }
    
    var cookie_splited = cookie.split(";");
    console.log(cookie_splited)
    
    for(i=0; i<cookie_splited.length; i++){
      var value_array = cookie_splited[i].split("=");
      console.log("this")
  
      if(value_array[0].replace(" ", "") == "redirect"){
        redirect_cookie = value_array[1];
      }
    }
  
    if(redirect_cookie === null || redirect_cookie === undefined || redirect_cookie === ''){
      document.cookie = `redirect=${redirect}; path=/`;
      return window.location.replace("https://a.advic.repl.co/just_random_thing/login?redirect=DClogin");
    }else{
      document.cookie = `redirect=; expires=${delete_cookie()}; path=/`
      const d = new Date();
      var exdays = 7;
      d.setTime(d.getTime() + (exdays*24*60*60*1000));
      let expires = "expires="+ d.toUTCString();
      document.cookie = `login_key=${data}; ${expires}`;
  
      return window.location.replace(get_link(redirect_cookie, data));
    }
  }
  
  function delete_cookie() {
    const d = new Date();
    var exdays = -1;
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    return "Thu, 25 Dec 2021 12:00:00 UTC"
  }
  
  function get_link(type, user) {
    if(type == "dashboard"){
      return "https://a.advic.repl.co/dashboard";
    }else if(type == "gift_code"){
      return `https://a.advic.repl.co/test.sbbotgiftcard?userid=${user}`;
    }else if(type == "edit-rank-card"){
      return "https://a.advic.repl.co/edit-rank-card";
    }else if(type == "embed_form"){
      return "https://a.advic.repl.co/create_embed";
    }else if(type == "private_embed_form"){
      return "https://a.advic.repl.co/send_private_message";
    }else if(type == "message_form"){
      return "https://a.advic.repl.co/send_message";
    }else if(type == "home"){
      return "https://a.advic.repl.co";
    }else{
      return "https://a.advic.repl.co";
    }
  }