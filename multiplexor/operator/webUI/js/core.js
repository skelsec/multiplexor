

var relayScoketState = "closed";
var relaySocket = new WebSocket("ws://127.0.0.1:54321"); //this socket is for relaying server data to the locally running agent
relaySocket.onopen = function (event) {
  console.log("Connection opened to the local agent");
  relayScoketState = "open";
};

relaySocket.onerror = function (event) {
  console.error("Relay websocket error observed:", event);
  relayScoketState = "closed";
};

relaySocket.onclose = function(event) {
  console.log("Relay websocket is closed now.");
  relayScoketState = "closed";
};
relaySocket.onmessage = function(event) {
  serverSocket.send(event.data);
};




var serverSocketState = "closed";
var serverSocket = new WebSocket("ws://127.0.0.1:9999");

serverSocket.onopen = function (event) {
	console.log("Connection opened to the server");
  serverSocketState = "open";
  sendRequest(operatorListAgentsCmd);
};

serverSocket.onerror = function (event) {
	console.error("WebSocket error observed:", event);
};

serverSocket.onclose = function(event) {
  console.log("WebSocket is closed now.");
};


function sendRequest(msg) {
  serverSocket.send(JSON.stringify(msg));
  console.log("Sent message to server!");
}

serverSocket.onmessage = function(event) {
  var msg = JSON.parse(event.data);
  console.log("Got the following data from server: ", msg);
  
  switch(msg.cmdtype) {
    case OperatorCmdType.LIST_AGENTS_RPLY:
      addAgents(msg);
      break;

    case OperatorCmdType.GET_AGENT_INFO_RPLY:
      addAgentInfo(msg);
      break;

    case OperatorCmdType.GET_PLUGINS_RPLY:
      addPlugins(msg);
      break;

  case OperatorCmdType.GET_PLUGINS_RPLY:
      addPluginInfo(msg);
      break;

  case OperatorCmdType.PLUGIN_STARTED:
      addPlugin(msg);
      break;

  case OperatorCmdType.PLUGIN_STOPPED:
      removePlugin(msg);
      break;

  }

  if(relayScoketState == "open"){
    relaySocket.send(event.data);
  }
  
};

function addAgents(rply) {
  console.log("addAgents invoked");

};

function addAgent(agent_data){

};

function addAgentInfo(rply){

};

function addPlugins(rply){

};

function addPlugin(plugin_data){

};

function removePlugin(plugin_data){

};

function addPluginInfo(rply){

};
